"""Basic RFQ Generator implementation."""

from datetime import datetime, timedelta
from typing import Dict, List, Set
import uuid
from rfq_generator.interface import RFQGeneratorInterface
from models.rfq import RFQ, RFQStore, RFQStatus
from models.order_schedule import OrderSchedule
from models.blanket_pos import BlanketPOs
from models.supplier_search import SupplierSearchStore, SupplierSearchResult


class BasicRFQGenerator(RFQGeneratorInterface):
    """Basic RFQ generator that creates one RFQ per supplier per material."""

    def __init__(self, rfq_validity_days: int = 14) -> None:
        """Initialize RFQ generator.
        
        Args:
            rfq_validity_days: Number of days RFQ is valid for responses
        """
        self.rfq_validity_days = rfq_validity_days

    def generate_rfqs(
        self,
        order_schedule: OrderSchedule,
        blanket_pos: BlanketPOs,
        supplier_results: SupplierSearchStore,
    ) -> RFQStore:
        """Generate RFQs for materials in the order schedule.
        
        Creates one RFQ per supplier per material. Uses blanket PO information
        to determine standard terms and quantities.
        """
        now = datetime.now()
        rfqs: List[RFQ] = []
        
        # Extract unique materials from order schedule
        materials_to_order: Dict[str, Dict] = {}
        for order in order_schedule.orders:
            if order.material_id not in materials_to_order:
                materials_to_order[order.material_id] = {
                    "material_name": order.material_name,
                    "total_quantity": 0,
                    "earliest_delivery": order.expected_delivery_date,
                }
            materials_to_order[order.material_id]["total_quantity"] += order.order_quantity
            if order.expected_delivery_date < materials_to_order[order.material_id]["earliest_delivery"]:
                materials_to_order[order.material_id]["earliest_delivery"] = order.expected_delivery_date
        
        # Get standard terms from blanket POs if available
        blanket_po_terms = self._extract_blanket_po_terms(blanket_pos)
        
        # Build supplier-to-material mapping
        supplier_materials: Dict[str, List[str]] = {}
        for result in supplier_results.results:
            for material_id in materials_to_order.keys():
                if material_id in result.materials_offered or any(
                    material_id.lower() in m.lower() for m in result.materials_offered
                ):
                    if result.supplier_id not in supplier_materials:
                        supplier_materials[result.supplier_id] = []
                    if material_id not in supplier_materials[result.supplier_id]:
                        supplier_materials[result.supplier_id].append(material_id)
        
        # Create RFQs for each supplier-material combination
        for supplier_result in supplier_results.results:
            supplier_id = supplier_result.supplier_id
            if supplier_id not in supplier_materials:
                continue
            
            for material_id in supplier_materials[supplier_id]:
                material_info = materials_to_order[material_id]
                
                # Build terms string
                terms = self._build_terms(material_id, blanket_po_terms)
                
                rfq = RFQ(
                    rfq_id=f"RFQ-{uuid.uuid4().hex[:8].upper()}",
                    material_id=material_id,
                    material_name=material_info["material_name"],
                    quantity=material_info["total_quantity"],
                    required_delivery_date=material_info["earliest_delivery"],
                    supplier_id=supplier_id,
                    supplier_name=supplier_result.name,
                    supplier_email=supplier_result.contact_email,
                    terms=terms,
                    status=RFQStatus.DRAFT,
                    created_at=now,
                    valid_until=now + timedelta(days=self.rfq_validity_days),
                )
                rfqs.append(rfq)
        
        return RFQStore(rfqs=rfqs, created_at=now)

    def _extract_blanket_po_terms(self, blanket_pos: BlanketPOs) -> Dict[str, Dict]:
        """Extract standard terms from blanket POs by product/material."""
        terms_by_product: Dict[str, Dict] = {}
        
        for bpo in blanket_pos.blanket_pos:
            terms_by_product[bpo.product_id] = {
                "total_quantity": bpo.total_quantity,
                "remaining_quantity": bpo.remaining_quantity,
                "unit_price": bpo.unit_price,
                "terms": bpo.terms,
            }
        
        return terms_by_product

    def _build_terms(self, material_id: str, blanket_po_terms: Dict[str, Dict]) -> str:
        """Build terms string for RFQ."""
        base_terms = (
            "Standard payment terms: Net 30 days. "
            "Quality requirements: ISO 9001 certified or equivalent. "
            "Delivery: FOB destination, freight prepaid."
        )
        
        # Add blanket PO reference if available
        if material_id in blanket_po_terms:
            bpo = blanket_po_terms[material_id]
            base_terms += f" Reference pricing: ${bpo['unit_price']:.2f}/unit."
            if bpo.get('terms'):
                base_terms += f" Additional terms: {bpo['terms']}"
        
        return base_terms


from datetime import datetime
from collections import defaultdict
from supplier_state_calculator.interface import SupplierStateCalculatorInterface
from models.delivery_history import DeliveryHistory, DeliveryStatus
from models.approved_suppliers_list import ApprovedSuppliersList, SupplierStatus
from models.blanket_pos import BlanketPOs, BlanketPOStatus
from models.supplier_state import SupplierStateStore, SupplierState

class BasicSupplierStateCalculator(SupplierStateCalculatorInterface):
    def calculate_supplier_state(self, delivery_history: DeliveryHistory, approved_suppliers_list: ApprovedSuppliersList, blanket_pos: BlanketPOs) -> SupplierStateStore:
        """Calculate supplier state from delivery history, approved suppliers, and blanket POs.
        
        This implementation:
        1. Groups delivery records by supplier-product combination
        2. Counts total and successful deliveries
        3. Counts active blanket POs per supplier-product
        4. Gets supplier status from approved suppliers list
        5. Calculates average lead time from delivery records
        """
        now = datetime.now()
        
        # Create lookup for supplier info
        supplier_lookup: dict[str, dict] = {}
        for supplier in approved_suppliers_list.suppliers:
            supplier_lookup[supplier.supplier_id] = {
                "name": supplier.supplier_name,
                "status": supplier.status
            }
        
        # Group delivery records by supplier_id + product_id
        delivery_stats: dict[tuple[str, str], dict] = defaultdict(lambda: {
            "total_deliveries": 0,
            "successful_deliveries": 0,
            "lead_times": [],
            "last_delivery_date": None,
            "supplier_name": "",
            "product_name": ""
        })
        
        for record in delivery_history.records:
            key = (record.supplier_id, record.product_id)
            stats = delivery_stats[key]
            
            stats["total_deliveries"] += 1
            stats["supplier_name"] = record.supplier_name
            stats["product_name"] = record.product_name
            
            # Count successful deliveries (DELIVERED status)
            if record.status == DeliveryStatus.DELIVERED:
                stats["successful_deliveries"] += 1
            
            # Calculate lead time if both dates are available
            if record.expected_delivery_date and record.actual_delivery_date:
                lead_time = (record.actual_delivery_date - record.expected_delivery_date).days
                stats["lead_times"].append(lead_time)
            
            # Track last delivery date
            if record.delivery_date:
                if stats["last_delivery_date"] is None or record.delivery_date > stats["last_delivery_date"]:
                    stats["last_delivery_date"] = record.delivery_date
        
        # Count active blanket POs by supplier-product
        blanket_po_counts: dict[tuple[str, str], int] = defaultdict(int)
        for blanket_po in blanket_pos.blanket_pos:
            if blanket_po.status == BlanketPOStatus.ACTIVE:
                key = (blanket_po.supplier_id, blanket_po.product_id)
                blanket_po_counts[key] += 1
        
        # Create supplier states
        supplier_states = []
        for (supplier_id, product_id), stats in delivery_stats.items():
            # Get supplier status from lookup, default to INACTIVE if not found
            supplier_info = supplier_lookup.get(supplier_id, {})
            supplier_status = supplier_info.get("status", SupplierStatus.INACTIVE)
            
            # Calculate average lead time
            avg_lead_time = None
            if stats["lead_times"]:
                avg_lead_time = sum(stats["lead_times"]) / len(stats["lead_times"])
            
            # Get active blanket PO count
            active_blanket_pos_count = blanket_po_counts.get((supplier_id, product_id), 0)
            
            supplier_state = SupplierState(
                supplier_id=supplier_id,
                supplier_name=stats["supplier_name"] or supplier_info.get("name", f"Supplier {supplier_id}"),
                product_id=product_id,
                product_name=stats["product_name"],
                total_deliveries=stats["total_deliveries"],
                successful_deliveries=stats["successful_deliveries"],
                active_blanket_pos_count=active_blanket_pos_count,
                supplier_status=supplier_status,
                average_lead_time_days=avg_lead_time,
                last_delivery_date=stats["last_delivery_date"],
            )
            supplier_states.append(supplier_state)
        
        return SupplierStateStore(
            states=supplier_states,
            built_at=now,
        )
"""Basic Purchase Order Builder implementation."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from purchase_order_builder.interface import PurchaseOrderBuilderInterface
from models.order_schedule import OrderSchedule, OrderItem, OrderStatus
from models.quote import Quote
from models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderStore,
    POLineItem,
    POStatus,
)


class BasicPurchaseOrderBuilder(PurchaseOrderBuilderInterface):
    """Builds purchase orders by consolidating orders by supplier."""

    def __init__(
        self,
        default_unit_price: float = 10.0,
        payment_terms: str = "Net 30",
        shipping_terms: str = "FOB Destination",
    ) -> None:
        """Initialize the builder.
        
        Args:
            default_unit_price: Default price if no quote available
            payment_terms: Default payment terms
            shipping_terms: Default shipping terms
        """
        self.default_unit_price = default_unit_price
        self.payment_terms = payment_terms
        self.shipping_terms = shipping_terms

    def build_purchase_orders(
        self,
        order_schedule: OrderSchedule,
        accepted_quotes: List[Quote],
        tax_rate: float = 0.0,
    ) -> PurchaseOrderStore:
        """Build purchase orders from order schedule and accepted quotes.
        
        Groups orders by supplier, applies pricing from quotes,
        and creates consolidated purchase orders.
        """
        now = datetime.now()
        
        # Build quote lookup: (material_id, supplier_id) -> Quote
        quote_lookup = self._build_quote_lookup(accepted_quotes)
        
        # Group orders by supplier
        orders_by_supplier = self._group_orders_by_supplier(order_schedule)
        
        # Build purchase orders
        purchase_orders: List[PurchaseOrder] = []
        
        for supplier_id, orders in orders_by_supplier.items():
            po = self._build_purchase_order(
                supplier_id=supplier_id,
                orders=orders,
                quote_lookup=quote_lookup,
                tax_rate=tax_rate,
                created_at=now,
            )
            if po:
                purchase_orders.append(po)
        
        return PurchaseOrderStore(orders=purchase_orders, created_at=now)

    def _build_quote_lookup(
        self, quotes: List[Quote]
    ) -> Dict[tuple[str, str], Quote]:
        """Build lookup from (material_id, supplier_id) to Quote."""
        lookup: Dict[tuple[str, str], Quote] = {}
        for quote in quotes:
            key = (quote.material_id, quote.supplier_id)
            # Keep the most recent quote if duplicates
            if key not in lookup or quote.received_at > lookup[key].received_at:
                lookup[key] = quote
        return lookup

    def _group_orders_by_supplier(
        self, order_schedule: OrderSchedule
    ) -> Dict[str, List[OrderItem]]:
        """Group order items by supplier_id."""
        by_supplier: Dict[str, List[OrderItem]] = defaultdict(list)
        
        for order in order_schedule.orders:
            # Only include scheduled/pending orders
            if order.order_status in [OrderStatus.SCHEDULED, OrderStatus.PENDING]:
                by_supplier[order.supplier_id].append(order)
        
        return dict(by_supplier)

    def _build_purchase_order(
        self,
        supplier_id: str,
        orders: List[OrderItem],
        quote_lookup: Dict[tuple[str, str], Quote],
        tax_rate: float,
        created_at: datetime,
    ) -> Optional[PurchaseOrder]:
        """Build a single purchase order for a supplier."""
        if not orders:
            return None
        
        # Get supplier info from first order
        first_order = orders[0]
        supplier_name = first_order.supplier_name
        
        # Find supplier email from quotes
        supplier_email = self._find_supplier_email(supplier_id, quote_lookup)
        
        # Build line items
        line_items: List[POLineItem] = []
        for idx, order in enumerate(orders, start=1):
            quote = quote_lookup.get((order.material_id, supplier_id))
            unit_price = quote.unit_price if quote else self.default_unit_price
            
            line_item = POLineItem(
                line_number=idx,
                material_id=order.material_id,
                material_name=order.material_name,
                quantity=order.order_quantity,
                unit_price=unit_price,
                total_price=round(order.order_quantity * unit_price, 2),
                required_delivery_date=order.expected_delivery_date,
            )
            line_items.append(line_item)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in line_items)
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = round(subtotal + tax_amount, 2)
        
        # Determine expected delivery (earliest required date)
        expected_delivery = min(item.required_delivery_date for item in line_items)
        
        return PurchaseOrder(
            po_number=self._generate_po_number(),
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            supplier_email=supplier_email,
            order_date=created_at,
            expected_delivery_date=expected_delivery,
            line_items=line_items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status=POStatus.DRAFT,
            payment_terms=self.payment_terms,
            shipping_terms=self.shipping_terms,
            created_at=created_at,
        )

    def _find_supplier_email(
        self,
        supplier_id: str,
        quote_lookup: Dict[tuple[str, str], Quote],
    ) -> str:
        """Generate supplier email from supplier_id."""
        # Quote model doesn't include email; generate from supplier_id
        return f"{supplier_id.lower().replace('-', '')}@supplier.com"

    def _generate_po_number(self) -> str:
        """Generate a unique PO number."""
        return f"PO-{uuid.uuid4().hex[:8].upper()}"

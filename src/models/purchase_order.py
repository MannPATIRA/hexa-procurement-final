"""Purchase order data models."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class POStatus(str, Enum):
    """Purchase order status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_DELIVERED = "partially_delivered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class POLineItem:
    """A single line item in a purchase order."""
    line_number: int
    material_id: str
    material_name: str
    quantity: int
    unit_price: float
    total_price: float
    required_delivery_date: datetime
    notes: str = ""


@dataclass(frozen=True)
class PurchaseOrder:
    """A purchase order for a supplier."""
    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_email: str
    order_date: datetime
    expected_delivery_date: datetime
    line_items: List[POLineItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    status: POStatus
    payment_terms: str = "Net 30"
    shipping_terms: str = "FOB Destination"
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def item_count(self) -> int:
        """Number of line items."""
        return len(self.line_items)
    
    @property
    def total_quantity(self) -> int:
        """Total quantity across all line items."""
        return sum(item.quantity for item in self.line_items)


@dataclass(frozen=True)
class PurchaseOrderStore:
    """Collection of purchase orders."""
    orders: List[PurchaseOrder]
    created_at: datetime
    orders_by_supplier: Dict[str, List[PurchaseOrder]] = field(
        default_factory=dict, init=False, repr=False
    )
    orders_by_id: Dict[str, PurchaseOrder] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Build indexes."""
        by_supplier: Dict[str, List[PurchaseOrder]] = defaultdict(list)
        by_id: Dict[str, PurchaseOrder] = {}
        
        for order in self.orders:
            by_supplier[order.supplier_id].append(order)
            by_id[order.po_number] = order
        
        object.__setattr__(self, 'orders_by_supplier', dict(by_supplier))
        object.__setattr__(self, 'orders_by_id', by_id)

    @property
    def total_value(self) -> float:
        """Total value of all purchase orders."""
        return sum(order.total_amount for order in self.orders)
    
    @property
    def supplier_count(self) -> int:
        """Number of unique suppliers."""
        return len(self.orders_by_supplier)

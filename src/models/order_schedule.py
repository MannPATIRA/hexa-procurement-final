"""Order schedule data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    PLACED = "placed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderItem:
    """Represents a single order entry in the schedule."""

    material_id: str
    material_name: str
    supplier_id: str
    supplier_name: str
    order_date: datetime
    expected_delivery_date: datetime
    order_quantity: int
    order_status: OrderStatus
    metadata: Dict[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class ProjectedInventoryLevel:
    """Represents projected inventory level at a point in time."""

    material_id: str
    date: datetime
    projected_quantity: int
    is_below_reorder_point: bool
    is_above_maximum_stock: bool

@dataclass(frozen=True)
class OrderSchedule:
    """Represents order schedule with orders and projected inventory levels."""

    orders: List[OrderItem]
    projected_levels: List[ProjectedInventoryLevel]
    schedule_start_date: datetime
    schedule_end_date: datetime
    generated_at: datetime
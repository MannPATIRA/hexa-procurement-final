"""Internal order (production/work order) data models."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class InternalOrderStatus(str, Enum):
    """Internal order status enumeration."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class InternalOrder:
    """Represents a single production/work order."""

    product_id: str
    product_name: str
    quantity: int
    start_date: datetime
    completion_date: datetime
    status: InternalOrderStatus
    production_line: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InternalOrderSchedule:
    """Represents a schedule of internal production orders."""

    orders: List[InternalOrder]
    schedule_start_date: datetime
    schedule_end_date: datetime
    generated_at: datetime
    orders_by_product: Dict[str, List[InternalOrder]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Build index by product_id."""
        index: Dict[str, List[InternalOrder]] = defaultdict(list)
        for order in self.orders:
            index[order.product_id].append(order)
        object.__setattr__(self, 'orders_by_product', dict(index))

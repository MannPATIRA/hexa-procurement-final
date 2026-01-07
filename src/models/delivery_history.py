"""Delivery history data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""

    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DeliveryRecord:
    """Represents a single delivery record."""

    delivery_id: str
    order_id: str
    supplier_id: str
    supplier_name: str
    product_id: str
    product_name: str
    quantity: int
    delivery_date: datetime
    status: DeliveryStatus
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None


@dataclass(frozen=True)
class DeliveryHistory:
    """Represents delivery history data from ERP system."""

    records: List[DeliveryRecord]
    fetched_at: datetime
    records_by_id: Dict[str, DeliveryRecord] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index."""
        index = {record.delivery_id: record for record in self.records}
        object.__setattr__(self, 'records_by_id', index)

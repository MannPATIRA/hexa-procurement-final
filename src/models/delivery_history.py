"""Delivery history data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


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




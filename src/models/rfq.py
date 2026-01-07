"""RFQ (Request for Quote) data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class RFQStatus(str, Enum):
    """RFQ status enumeration."""

    DRAFT = "draft"
    SENT = "sent"
    RESPONDED = "responded"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class RFQ:
    """Represents a Request for Quote sent to a supplier."""

    rfq_id: str
    material_id: str
    material_name: str
    quantity: int
    required_delivery_date: datetime
    supplier_id: str
    supplier_name: str
    supplier_email: str
    terms: str
    status: RFQStatus
    created_at: datetime
    valid_until: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RFQStore:
    """Collection of RFQs."""

    rfqs: List[RFQ]
    created_at: datetime


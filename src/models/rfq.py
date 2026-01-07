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
    rfqs_by_id: Dict[str, RFQ] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by rfq_id."""
        index = {rfq.rfq_id: rfq for rfq in self.rfqs}
        object.__setattr__(self, 'rfqs_by_id', index)

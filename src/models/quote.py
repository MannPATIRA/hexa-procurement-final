"""Quote data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class QuoteStatus(str, Enum):
    """Quote status enumeration."""

    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Quote:
    """Represents a quote received from a supplier."""

    quote_id: str
    rfq_id: str
    supplier_id: str
    supplier_name: str
    material_id: str
    material_name: str
    unit_price: float
    quantity: int
    total_price: float
    lead_time_days: int
    valid_until: datetime
    received_at: datetime
    status: QuoteStatus = QuoteStatus.RECEIVED
    terms: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class QuoteStore:
    """Collection of quotes."""

    quotes: List[Quote]
    updated_at: datetime


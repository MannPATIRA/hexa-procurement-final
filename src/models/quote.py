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
    quotes_by_id: Dict[str, Quote] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by quote_id."""
        index = {quote.quote_id: quote for quote in self.quotes}
        object.__setattr__(self, 'quotes_by_id', index)

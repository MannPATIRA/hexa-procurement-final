"""Supplier search result data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SupplierSearchResult:
    """Represents a supplier found via web search."""

    supplier_id: str
    name: str
    contact_email: str
    website: str
    materials_offered: List[str]
    estimated_price_range: Tuple[float, float]  # (min, max)
    estimated_lead_time_days: int
    certifications: List[str]
    rating: Optional[float] = None  # 0.0 to 5.0
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SupplierSearchStore:
    """Collection of supplier search results."""

    results: List[SupplierSearchResult]
    searched_at: datetime
    search_query: str


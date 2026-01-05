"""Inventory data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class InventoryItem:
    """Represents a single inventory item."""

    item_id: str
    item_name: str
    quantity: int
    unit_price: float
    location: str
    last_updated: datetime
    supplier_id: Optional[str] = None


@dataclass(frozen=True)
class InventoryData:
    """Represents inventory data fetched from ERP system."""

    items: List[InventoryItem]
    fetched_at: datetime

    def __post_init__(self) -> None:
        """Validate inventory data."""
        if not self.items:
            raise ValueError("Inventory data must contain at least one item")
        if self.fetched_at > datetime.now():
            raise ValueError("Fetched timestamp cannot be in the future")


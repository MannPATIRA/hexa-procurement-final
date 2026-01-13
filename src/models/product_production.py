"""Product production information data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProductProductionInfo:
    """Production parameters for a single product."""

    product_id: str
    production_lead_time_days: int  # How long it takes to produce
    production_rate_per_day: Optional[int] = None  # Units per day capacity
    setup_time_hours: Optional[float] = None  # Setup/changeover time
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductProductionStore:
    """Collection of product production information."""

    items: List[ProductProductionInfo]
    items_by_id: Dict[str, ProductProductionInfo] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Build index by product_id."""
        index = {item.product_id: item for item in self.items}
        object.__setattr__(self, 'items_by_id', index)

"""Bill of Materials (BOM) data model."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass(frozen=True)
class BOMItem:
    """Represents a single BOM entry mapping a product to a material requirement."""

    product_id: str
    material_id: str
    quantity_required: float


@dataclass(frozen=True)
class BOMData:
    """Represents BOM data from ERP system."""

    items: List[BOMItem]
    fetched_at: datetime
    items_by_product: Dict[str, List[BOMItem]] = field(default_factory=dict, init=False, repr=False)
    items_by_material: Dict[str, List[BOMItem]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build indexes by product_id and material_id."""
        by_product: Dict[str, List[BOMItem]] = defaultdict(list)
        by_material: Dict[str, List[BOMItem]] = defaultdict(list)
        for item in self.items:
            by_product[item.product_id].append(item)
            by_material[item.material_id].append(item)
        object.__setattr__(self, 'items_by_product', dict(by_product))
        object.__setattr__(self, 'items_by_material', dict(by_material))

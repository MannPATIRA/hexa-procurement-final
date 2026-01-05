"""Bill of Materials (BOM) data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


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

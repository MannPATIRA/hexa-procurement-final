"""Guardrail data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Guardrail:
    """Represents guardrail thresholds for a single material."""

    material_id: str
    material_name: str
    reorder_point: int
    safety_stock: int
    maximum_stock: int
    eoq: int  # Economic Order Quantity
    valid_period_start: datetime
    valid_period_end: datetime
    calculated_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardrailStore:
    """Represents guardrail data for all materials."""

    items: List[Guardrail]
    calculated_at: datetime
    items_by_id: Dict[str, Guardrail] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by material_id."""
        index = {item.material_id: item for item in self.items}
        object.__setattr__(self, 'items_by_id', index)

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

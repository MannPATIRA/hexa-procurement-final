"""Supplier state data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from models.approved_suppliers_list import SupplierStatus


@dataclass(frozen=True)
class SupplierState:
    """Represents state for a single supplier-SKU combination."""

    supplier_id: str
    supplier_name: str
    product_id: str
    product_name: str
    total_deliveries: int
    successful_deliveries: int
    active_blanket_pos_count: int
    supplier_status: SupplierStatus
    average_lead_time_days: Optional[float] = None
    average_defect_rate: Optional[float] = None
    last_delivery_date: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100.0


@dataclass(frozen=True)
class SupplierStateStore:
    """Represents aggregated supplier state for all supplier-SKU combinations."""

    states: List[SupplierState]
    built_at: datetime
    states_by_key: Dict[Tuple[str, str], SupplierState] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by (supplier_id, product_id) tuple."""
        index = {(state.supplier_id, state.product_id): state for state in self.states}
        object.__setattr__(self, 'states_by_key', index)

"""Sales data model (time series)."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SalesRecord:
    """Represents a single sales record in a time series."""

    timestamp: datetime
    product_id: str
    product_name: str
    quantity_sold: int
    unit_price: float
    total_revenue: float
    customer_id: Optional[str] = None
    # New optional fields from updated Sheet2 format
    variant_id: Optional[str] = None
    variant_value: Optional[str] = None
    category: Optional[str] = None
    uom: Optional[str] = None  # Unit of Measure
    type: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    additional_info: Optional[str] = None


@dataclass(frozen=True)
class SalesData:
    """Represents sales history time series data from ERP system."""

    records: List[SalesRecord]
    start_date: datetime
    end_date: datetime
    fetched_at: datetime
    records_by_product: Dict[str, List[SalesRecord]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by product_id."""
        index: Dict[str, List[SalesRecord]] = defaultdict(list)
        for record in self.records:
            index[record.product_id].append(record)
        object.__setattr__(self, 'records_by_product', dict(index))

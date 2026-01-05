"""Sales data model (time series)."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

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

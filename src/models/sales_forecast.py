"""Sales forecast data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ForecastItem:
    """Represents a forecast for a single SKU/inventory item."""

    item_id: str
    item_name: str
    forecasted_quantity: int
    forecast_period_start: datetime
    forecast_period_end: datetime
    confidence_level: Optional[float] = None
    forecasted_revenue: Optional[float] = None


@dataclass(frozen=True)
class SalesForecast:
    """Represents sales forecast predictions for inventory items."""

    forecasts: List[ForecastItem]
    forecast_generated_at: datetime
    forecast_period_start: datetime
    forecast_period_end: datetime
    forecasts_by_id: Dict[str, ForecastItem] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by item_id."""
        index = {forecast.item_id: forecast for forecast in self.forecasts}
        object.__setattr__(self, 'forecasts_by_id', index)

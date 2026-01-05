"""Materials forecast data model"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass(frozen=True)
class MaterialForecastItem:
    """Represents a forecast for a single material."""

    material_id: str
    material_name: str
    forecasted_quantity: float
    forecast_period_start: datetime
    forecast_period_end: datetime
    confidence_level: Optional[float] = None

@dataclass(frozen=True)
class MaterialsForecast:
    """Represents materials forecast predictions based on product sales forecasts and BOMs."""

    forecasts: List[MaterialForecastItem]
    forecast_generated_at: datetime
    forecast_period_start: datetime
    forecast_period_end: datetime
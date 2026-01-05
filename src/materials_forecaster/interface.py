from abc import ABC, abstractmethod
from models.materials_forecast import MaterialsForecast
from models.bom import BOMData
from models.sales_forecast import SalesForecast


class MaterialsForecasterInterface(ABC):
    @abstractmethod
    def forecast_materials(self, sales_forecast: SalesForecast, bom_data: BOMData, forecast_period_days: int) -> MaterialsForecast:
        pass

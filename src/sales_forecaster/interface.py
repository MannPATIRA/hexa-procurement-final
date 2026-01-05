from abc import ABC, abstractmethod
from models.inventory_data import InventoryData
from models.sales_data import SalesData
from models.sales_forecast import SalesForecast

class SalesForecasterInterface(ABC):

    @abstractmethod
    def forecast_sales(self, inventory_data: InventoryData, sales_data: SalesData, forecast_period_days: int,) -> SalesForecast:
        pass
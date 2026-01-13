"""Internal Order Scheduler interface."""

from abc import ABC, abstractmethod
from models.internal_order import InternalOrderSchedule
from models.sales_forecast import SalesForecast
from models.inventory_data import InventoryData
from models.product_production import ProductProductionStore


class InternalOrderSchedulerInterface(ABC):
    """Interface for scheduling internal production orders."""

    @abstractmethod
    def schedule_internal_orders(
        self,
        sales_forecast: SalesForecast,
        product_inventory: InventoryData,
        product_production_info: ProductProductionStore,
        num_days: int,
    ) -> InternalOrderSchedule:
        """Schedule internal production orders based on sales forecast and inventory.
        
        Args:
            sales_forecast: Forecasted sales demand for products
            product_inventory: Current product inventory levels
            product_production_info: Production parameters (lead times, rates)
            num_days: Number of days to schedule ahead
            
        Returns:
            InternalOrderSchedule with production orders
        """
        pass

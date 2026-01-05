from abc import ABC, abstractmethod
from models.inventory_data import InventoryData
from models.delivery_history import DeliveryHistory
from models.sales_data import SalesData
from models.bom import BOMData
from models.blanket_pos import BlanketPOs

class ERPDataFetcherInterface(ABC):

    @abstractmethod
    def fetch_inventory_data(self) -> InventoryData:
        pass

    @abstractmethod
    def fetch_delivery_history(self) -> DeliveryHistory:
        pass

    @abstractmethod
    def fetch_sales_data(self) -> SalesData:
        pass

    @abstractmethod
    def fetch_bom_data(self) -> BOMData:
        pass

    @abstractmethod
    def fetch_blanket_pos(self) -> BlanketPOs:
        pass
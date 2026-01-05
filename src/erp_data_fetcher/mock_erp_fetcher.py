from erp_data_fetcher.interface import ERPDataFetcherInterface

from models.inventory_data import InventoryData
from models.delivery_history import DeliveryHistory
from models.sales_data import SalesData
from models.bom import BOMData
from models.blanket_pos import BlanketPOs

from mocks.mock_erp import MockERP

mock_erp = MockERP()

class MockERPDataFetcher(ERPDataFetcherInterface):
    def fetch_inventory_data(self) -> InventoryData:
        return mock_erp.inventory_data
    
    def fetch_delivery_history(self) -> DeliveryHistory:
        return mock_erp.delivery_history

    def fetch_sales_data(self) -> SalesData:
        return mock_erp.sales_data
    
    def fetch_bom_data(self) -> BOMData:
        return mock_erp.bom_data
    
    def fetch_blanket_pos(self) -> BlanketPOs:
        return mock_erp.blanket_pos_data 
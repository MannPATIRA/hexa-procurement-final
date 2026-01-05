from crm_data_fetcher.interface import CRMDataFetcherInterface
from models.blanket_pos import BlanketPOs
from models.approved_suppliers_list import ApprovedSuppliersList
from mocks.mock_crm import MockCRM

mock_crm = MockCRM()

class MockCRMDataFetcher(CRMDataFetcherInterface):
    def fetch_blanket_pos(self) -> BlanketPOs:
        return mock_crm.blanket_pos
    
    def fetch_approved_suppliers(self) -> ApprovedSuppliersList:
        return mock_crm.approved_suppliers
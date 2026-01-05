from abc import ABC, abstractmethod
from models.blanket_pos import BlanketPOs
from models.approved_suppliers_list import ApprovedSuppliersList

class CRMDataFetcherInterface(ABC):

    @abstractmethod
    def fetch_blanket_pos(self) -> BlanketPOs:
        pass

    @abstractmethod
    def fetch_approved_suppliers(self) -> ApprovedSuppliersList:
        pass
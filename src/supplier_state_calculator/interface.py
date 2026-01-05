from abc import ABC, abstractmethod
from models.delivery_history import DeliveryHistory
from models.approved_suppliers_list import ApprovedSuppliersList
from models.blanket_pos import BlanketPOs
from models.supplier_state import SupplierStateStore, SupplierState

class SupplierStateCalculatorInterface(ABC):

    @abstractmethod
    def calculate_supplier_state(self, delivery_history: DeliveryHistory, approved_suppliers_list: ApprovedSuppliersList, blanket_pos: BlanketPOs) -> SupplierStateStore:
        pass
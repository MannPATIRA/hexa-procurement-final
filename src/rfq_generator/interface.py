"""RFQ Generator interface."""

from abc import ABC, abstractmethod
from models.rfq import RFQStore
from models.order_schedule import OrderSchedule
from models.blanket_pos import BlanketPOs
from models.supplier_search import SupplierSearchStore


class RFQGeneratorInterface(ABC):
    """Interface for generating RFQs."""

    @abstractmethod
    def generate_rfqs(
        self,
        order_schedule: OrderSchedule,
        blanket_pos: BlanketPOs,
        supplier_results: SupplierSearchStore,
    ) -> RFQStore:
        """Generate RFQs for materials in the order schedule.
        
        Args:
            order_schedule: Order schedule with material orders
            blanket_pos: Blanket purchase orders for reference quantities/terms
            supplier_results: Suppliers found via web search
            
        Returns:
            RFQStore containing generated RFQs
        """
        pass


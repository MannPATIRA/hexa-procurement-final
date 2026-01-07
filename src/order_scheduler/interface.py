from abc import ABC, abstractmethod
from models.order_schedule import OrderSchedule
from models.materials_forecast import MaterialsForecast
from models.supplier_state import SupplierStateStore
from models.guardrails import GuardrailStore
from models.inventory_data import InventoryData

class OrderSchedulerInterface(ABC):
    @abstractmethod
    def schedule_orders(self, inventory_data: InventoryData, materials_forecast: MaterialsForecast, supplier_state_store: SupplierStateStore, guardrails: GuardrailStore) -> OrderSchedule:
        pass
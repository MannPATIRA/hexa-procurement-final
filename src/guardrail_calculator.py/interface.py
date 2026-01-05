from abc import ABC, abstractmethod
from models.guardrails import GuardrailStore, Guardrail
from models.supplier_state import SupplierStateStore
from models.sales_forecast import SalesForecast

class GuardrailCalculatorInterface(ABC):
    @abstractmethod
    def calculate_guardrails(self, supplier_state_store: SupplierStateStore, sales_forecast: SalesForecast) -> GuardrailStore:
        pass
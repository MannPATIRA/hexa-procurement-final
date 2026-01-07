from abc import ABC, abstractmethod
from models.guardrails import GuardrailStore, Guardrail
from models.supplier_state import SupplierStateStore
from models.materials_forecast import MaterialsForecast

class GuardrailCalculatorInterface(ABC):
    @abstractmethod
    def calculate_guardrails(self, supplier_state_store: SupplierStateStore, materials_forecast: MaterialsForecast) -> GuardrailStore:
        pass
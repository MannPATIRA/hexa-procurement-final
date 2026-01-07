"""Quote Evaluator interface."""

from abc import ABC, abstractmethod
from models.quote import Quote
from models.supplier_state import SupplierStateStore
from models.evaluation_result import EvaluationResult


class QuoteEvaluatorInterface(ABC):
    """Interface for evaluating quotes against current suppliers."""

    @abstractmethod
    def evaluate(
        self,
        quote: Quote,
        supplier_state_store: SupplierStateStore,
        current_unit_price: float,
        current_lead_time_days: int,
    ) -> EvaluationResult:
        """Evaluate a quote against current supplier performance.
        
        Args:
            quote: Quote to evaluate
            supplier_state_store: Current supplier performance data
            current_unit_price: Current unit price for the material
            current_lead_time_days: Current lead time for the material
            
        Returns:
            EvaluationResult with scores and recommendation
        """
        pass


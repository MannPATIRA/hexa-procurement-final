"""Order Schedule Updater interface."""

from abc import ABC, abstractmethod
from models.order_schedule import OrderSchedule
from models.quote import Quote
from models.evaluation_result import EvaluationResult


class OrderScheduleUpdaterInterface(ABC):
    """Interface for updating order schedules based on quote evaluations."""

    @abstractmethod
    def update_if_better(
        self,
        schedule: OrderSchedule,
        quote: Quote,
        evaluation: EvaluationResult,
    ) -> OrderSchedule:
        """Update the order schedule if the quote is better than current suppliers.
        
        Args:
            schedule: Current order schedule
            quote: Quote that was evaluated
            evaluation: Result of quote evaluation
            
        Returns:
            Updated OrderSchedule (or original if no update needed)
        """
        pass


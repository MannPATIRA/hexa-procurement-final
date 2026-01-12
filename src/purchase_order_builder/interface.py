"""Purchase Order Builder interface."""

from abc import ABC, abstractmethod
from typing import List

from models.order_schedule import OrderSchedule
from models.quote import Quote
from models.purchase_order import PurchaseOrderStore


class PurchaseOrderBuilderInterface(ABC):
    """Interface for building purchase orders from order schedules and quotes."""

    @abstractmethod
    def build_purchase_orders(
        self,
        order_schedule: OrderSchedule,
        accepted_quotes: List[Quote],
        tax_rate: float = 0.0,
    ) -> PurchaseOrderStore:
        """Build purchase orders from an order schedule and accepted quotes.
        
        Consolidates order items by supplier and creates purchase orders
        with line items, pricing, and totals.
        
        Args:
            order_schedule: Order schedule with material orders
            accepted_quotes: List of accepted quotes with pricing
            tax_rate: Tax rate to apply (default 0.0 = 0%)
            
        Returns:
            PurchaseOrderStore containing generated purchase orders
        """
        pass

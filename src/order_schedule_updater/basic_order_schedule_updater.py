"""Basic Order Schedule Updater implementation."""

from datetime import datetime, timedelta
from typing import List
from order_schedule_updater.interface import OrderScheduleUpdaterInterface
from models.order_schedule import OrderSchedule, OrderItem, ProjectedInventoryLevel, OrderStatus
from models.quote import Quote
from models.evaluation_result import EvaluationResult


class BasicOrderScheduleUpdater(OrderScheduleUpdaterInterface):
    """Basic order schedule updater that replaces suppliers when quotes are better."""

    def update_if_better(
        self,
        schedule: OrderSchedule,
        quote: Quote,
        evaluation: EvaluationResult,
    ) -> OrderSchedule:
        """Update the order schedule if the quote is better than current suppliers.
        
        If the evaluation indicates the quote is better, updates all pending/scheduled
        orders for the same material to use the new supplier.
        
        Args:
            schedule: Current order schedule
            quote: Quote that was evaluated
            evaluation: Result of quote evaluation
            
        Returns:
            Updated OrderSchedule (or original if no update needed)
        """
        # If quote is not better, return original schedule unchanged
        if not evaluation.is_better_than_current:
            return schedule
        
        # Find orders for the same material that can be updated
        updated_orders: List[OrderItem] = []
        orders_updated = False
        
        for order in schedule.orders:
            if (
                order.material_id == quote.material_id
                and order.order_status in [OrderStatus.PENDING, OrderStatus.SCHEDULED]
            ):
                # Update this order with new supplier info
                new_delivery_date = order.order_date + timedelta(days=quote.lead_time_days)
                
                updated_order = OrderItem(
                    material_id=order.material_id,
                    material_name=order.material_name,
                    supplier_id=quote.supplier_id,
                    supplier_name=quote.supplier_name,
                    order_date=order.order_date,
                    expected_delivery_date=new_delivery_date,
                    order_quantity=order.order_quantity,
                    order_status=order.order_status,
                    metadata={
                        **order.metadata,
                        "updated_from_quote": quote.quote_id,
                        "previous_supplier": order.supplier_id,
                        "evaluation_score": str(evaluation.overall_score),
                        "improvement": f"{evaluation.improvement_percentage:.1f}%",
                    },
                )
                updated_orders.append(updated_order)
                orders_updated = True
            else:
                # Keep order unchanged
                updated_orders.append(order)
        
        if not orders_updated:
            # No orders were updated, return original
            return schedule
        
        # Create new schedule with updated orders
        return OrderSchedule(
            orders=updated_orders,
            projected_levels=schedule.projected_levels,  # Keep projected levels unchanged for now
            schedule_start_date=schedule.schedule_start_date,
            schedule_end_date=schedule.schedule_end_date,
            generated_at=datetime.now(),
        )


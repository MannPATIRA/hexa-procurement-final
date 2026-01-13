"""Basic Internal Order Scheduler implementation."""

from datetime import datetime, timedelta
from collections import defaultdict
from internal_order_scheduler.interface import InternalOrderSchedulerInterface
from models.internal_order import InternalOrderSchedule, InternalOrder, InternalOrderStatus
from models.sales_forecast import SalesForecast
from models.inventory_data import InventoryData, ItemType
from models.product_production import ProductProductionStore


class BasicInternalOrderScheduler(InternalOrderSchedulerInterface):
    """Rough-cut internal order scheduler using simple production lead times."""

    def schedule_internal_orders(
        self,
        sales_forecast: SalesForecast,
        product_inventory: InventoryData,
        product_production_info: ProductProductionStore,
        num_days: int,
    ) -> InternalOrderSchedule:
        """Schedule internal production orders based on sales forecast and inventory.
        
        Uses day-by-day simulation:
        1. Projects product inventory based on forecasted demand
        2. Schedules production when inventory drops below reorder point
        3. Uses production lead times to set completion dates
        4. Tracks pending production orders to avoid duplicates
        """
        now = datetime.now()
        schedule_start = now
        schedule_end = now + timedelta(days=num_days)
        
        # Build lookup maps
        # Product inventory: product_id -> current quantity
        product_inv: dict[str, int] = {}
        for item in product_inventory.items:
            if item.item_type == ItemType.PRODUCT:
                product_inv[item.item_id] = item.quantity
        
        # Production info lookup
        production_info_map = product_production_info.items_by_id
        
        # Daily demand lookup: product_id -> daily_demand
        daily_demand: dict[str, float] = {}
        forecast_period_days = (sales_forecast.forecast_period_end - sales_forecast.forecast_period_start).days
        if forecast_period_days == 0:
            forecast_period_days = 1
        
        for forecast_item in sales_forecast.forecasts:
            daily_demand[forecast_item.item_id] = forecast_item.forecasted_quantity / forecast_period_days
        
        # Track current inventory levels (will be updated day by day)
        current_inventory: dict[str, float] = {}
        for product_id in daily_demand.keys():
            current_inventory[product_id] = float(product_inv.get(product_id, 0))
        
        # Track pending production orders: product_id -> InternalOrder
        pending_orders: dict[str, InternalOrder] = {}
        
        # Lists to collect results
        orders: list[InternalOrder] = []
        
        # Day-by-day projection
        for day_offset in range(num_days):
            current_date = schedule_start + timedelta(days=day_offset)
            
            # Process each product
            for product_id, demand_per_day in daily_demand.items():
                # Get product info
                forecast_item = sales_forecast.forecasts_by_id.get(product_id)
                if not forecast_item:
                    continue
                
                product_name = forecast_item.item_name
                production_info = production_info_map.get(product_id)
                
                if not production_info:
                    # Skip products without production info
                    continue
                
                # Check for completed production (orders scheduled earlier that complete today)
                if product_id in pending_orders:
                    pending_order = pending_orders[product_id]
                    if pending_order.completion_date.date() == current_date.date():
                        # Production completes today
                        current_inventory[product_id] += pending_order.quantity
                        # Remove from pending (order is completed)
                        del pending_orders[product_id]
                
                # Subtract daily demand
                current_inventory[product_id] -= demand_per_day
                
                # Ensure inventory doesn't go negative
                if current_inventory[product_id] < 0:
                    current_inventory[product_id] = 0
                
                # Calculate reorder point for this product
                # Similar to materials: (daily_demand * production_lead_time) + safety_stock
                production_lead_time = production_info.production_lead_time_days
                safety_stock = int(demand_per_day * production_lead_time * 1.5)  # 1.5x lead time demand
                reorder_point = int(demand_per_day * production_lead_time) + safety_stock
                
                # Check if we need to schedule production
                # Only schedule if: inventory < reorder_point AND no pending production exists
                inventory_qty = int(current_inventory[product_id])
                if inventory_qty < reorder_point and product_id not in pending_orders:
                    # Calculate production quantity
                    # Use production rate if available, otherwise use demand gap
                    demand_gap = reorder_point - inventory_qty
                    if production_info.production_rate_per_day:
                        # Respect capacity constraint
                        production_qty = min(demand_gap, production_info.production_rate_per_day)
                    else:
                        # Assume infinite capacity - produce enough to cover gap
                        production_qty = max(demand_gap, 10)  # Minimum production quantity
                    
                    # Calculate completion date
                    completion_date = current_date + timedelta(days=production_lead_time)
                    
                    # Create internal order
                    order = InternalOrder(
                        product_id=product_id,
                        product_name=product_name,
                        quantity=production_qty,
                        start_date=current_date,
                        completion_date=completion_date,
                        status=InternalOrderStatus.SCHEDULED,
                    )
                    
                    orders.append(order)
                    pending_orders[product_id] = order
        
        return InternalOrderSchedule(
            orders=orders,
            schedule_start_date=schedule_start,
            schedule_end_date=schedule_end,
            generated_at=now,
        )

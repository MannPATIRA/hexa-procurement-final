from datetime import datetime, timedelta
from collections import defaultdict
from order_scheduler.interface import OrderSchedulerInterface
from models.materials_forecast import MaterialsForecast
from models.supplier_state import SupplierStateStore
from models.guardrails import GuardrailStore, Guardrail
from models.order_schedule import OrderSchedule, OrderItem, ProjectedInventoryLevel, OrderStatus
from models.inventory_data import InventoryData, ItemType

class BasicOrderScheduler(OrderSchedulerInterface):
    def schedule_orders(self, inventory_data: InventoryData, materials_forecast: MaterialsForecast, supplier_state_store: SupplierStateStore, guardrails: GuardrailStore, num_days: int) -> OrderSchedule:
        """Create an order schedule for materials based on inventory, forecast, and guardrails.
        
        This implementation:
        1. Projects material inventory day-by-day based on forecasted demand
        2. Schedules orders when inventory drops below reorder points
        3. Uses EOQ from guardrails for order quantities
        4. Calculates expected delivery dates based on lead times
        5. Generates projected inventory levels for each day
        """
        now = datetime.now()
        schedule_start = now
        schedule_end = now + timedelta(days=num_days)
        
        # Build lookup maps
        # Material inventory: material_id -> current quantity
        material_inventory: dict[str, int] = {}
        material_suppliers: dict[str, tuple[str, str]] = {}  # material_id -> (supplier_id, supplier_name)
        
        for item in inventory_data.items:
            # Filter for materials only (exclude products/finished goods)
            if item.item_type == ItemType.MATERIAL:
                material_inventory[item.item_id] = item.quantity
                if item.supplier_id:
                    material_suppliers[item.item_id] = (item.supplier_id, f"Supplier {item.supplier_id}")
        
        # Guardrails lookup: use items_by_id index
        guardrails_map = guardrails.items_by_id
        
        # Daily demand lookup: material_id -> daily_demand
        daily_demand: dict[str, float] = {}
        forecast_period_days = (materials_forecast.forecast_period_end - materials_forecast.forecast_period_start).days
        if forecast_period_days == 0:
            forecast_period_days = 1
        
        for forecast_item in materials_forecast.forecasts:
            daily_demand[forecast_item.material_id] = forecast_item.forecasted_quantity / forecast_period_days
        
        # Default supplier and lead time
        default_supplier_id = "SUP-DEFAULT"
        default_supplier_name = "Default Supplier"
        default_lead_time_days = 7
        
        # Track current inventory levels (will be updated day by day)
        current_inventory: dict[str, float] = {}
        for material_id in daily_demand.keys():
            current_inventory[material_id] = float(material_inventory.get(material_id, 0))
        
        # Track pending orders: material_id -> OrderItem (to avoid duplicate scheduling)
        pending_orders: dict[str, OrderItem] = {}
        
        # Lists to collect results
        orders: list[OrderItem] = []
        projected_levels: list[ProjectedInventoryLevel] = []
        
        # Day-by-day projection
        for day_offset in range(num_days):
            current_date = schedule_start + timedelta(days=day_offset)
            
            # Process each material
            for material_id, demand_per_day in daily_demand.items():
                # Get material info using forecasts_by_id index
                forecast_item = materials_forecast.forecasts_by_id.get(material_id)
                if not forecast_item:
                    continue
                
                material_name = forecast_item.material_name
                guardrail = guardrails_map.get(material_id)
                
                if not guardrail:
                    # Skip materials without guardrails
                    continue
                
                # Check for incoming deliveries (orders scheduled earlier that arrive today)
                if material_id in pending_orders:
                    pending_order = pending_orders[material_id]
                    if pending_order.expected_delivery_date.date() == current_date.date():
                        # Order arrives today
                        current_inventory[material_id] += pending_order.order_quantity
                        # Remove from pending (order is delivered)
                        del pending_orders[material_id]
                
                # Subtract daily demand
                current_inventory[material_id] -= demand_per_day
                
                # Ensure inventory doesn't go negative (shouldn't happen in real scenario, but safety check)
                if current_inventory[material_id] < 0:
                    current_inventory[material_id] = 0
                
                # Check if we need to schedule an order
                # Only schedule if: inventory < reorder_point AND no pending order exists
                inventory_qty = int(current_inventory[material_id])
                if inventory_qty < guardrail.reorder_point and material_id not in pending_orders:
                    # Schedule an order
                    supplier_id, supplier_name = material_suppliers.get(material_id, (default_supplier_id, default_supplier_name))
                    
                    # Use default lead time (since SupplierStateStore tracks products, not materials)
                    lead_time_days = default_lead_time_days
                    expected_delivery_date = current_date + timedelta(days=lead_time_days)
                    
                    # Create order
                    order = OrderItem(
                        material_id=material_id,
                        material_name=material_name,
                        supplier_id=supplier_id,
                        supplier_name=supplier_name,
                        order_date=current_date,
                        expected_delivery_date=expected_delivery_date,
                        order_quantity=guardrail.eoq,
                        order_status=OrderStatus.SCHEDULED,
                    )
                    
                    orders.append(order)
                    pending_orders[material_id] = order
                
                # Record projected inventory level for this day
                is_below_reorder = inventory_qty < guardrail.reorder_point
                is_above_max = inventory_qty > guardrail.maximum_stock
                
                projected_level = ProjectedInventoryLevel(
                    material_id=material_id,
                    date=current_date,
                    projected_quantity=inventory_qty,
                    is_below_reorder_point=is_below_reorder,
                    is_above_maximum_stock=is_above_max,
                )
                projected_levels.append(projected_level)
        
        return OrderSchedule(
            orders=orders,
            projected_levels=projected_levels,
            schedule_start_date=schedule_start,
            schedule_end_date=schedule_end,
            generated_at=now,
        )
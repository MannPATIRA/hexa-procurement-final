from datetime import datetime, timedelta
from collections import defaultdict
from interface import GuardrailCalculatorInterface
from models.supplier_state import SupplierStateStore
from models.sales_forecast import SalesForecast
from models.guardrails import GuardrailStore, Guardrail

class BasicGuardrailCalculator(GuardrailCalculatorInterface):
    def calculate_guardrails(self, supplier_state_store: SupplierStateStore, sales_forecast: SalesForecast) -> GuardrailStore:
        """Calculate guardrails (reorder points, safety stock, etc.) based on sales forecast and supplier lead times.
        
        This implementation:
        1. Finds average lead time for each product from supplier state
        2. Calculates daily demand from sales forecast
        3. Calculates safety stock, reorder point, max stock, and EOQ
        """
        now = datetime.now()
        
        # Calculate forecast period in days
        forecast_period_days = (sales_forecast.forecast_period_end - sales_forecast.forecast_period_start).days
        if forecast_period_days == 0:
            forecast_period_days = 1
        
        # Group supplier states by product_id to find average lead time
        product_lead_times: dict[str, list[float]] = defaultdict(list)
        product_names: dict[str, str] = {}
        
        for state in supplier_state_store.states:
            if state.average_lead_time_days is not None:
                product_lead_times[state.product_id].append(state.average_lead_time_days)
            if state.product_id not in product_names:
                product_names[state.product_id] = state.product_name
        
        # Calculate average lead time per product
        avg_lead_times: dict[str, float] = {}
        for product_id, lead_times in product_lead_times.items():
            avg_lead_times[product_id] = sum(lead_times) / len(lead_times) if lead_times else 0.0
        
        # Calculate guardrails for each product in sales forecast
        guardrails = []
        for forecast_item in sales_forecast.forecasts:
            product_id = forecast_item.item_id
            product_name = forecast_item.item_name
            
            # Calculate daily demand from forecast
            daily_demand = forecast_item.forecasted_quantity / forecast_period_days if forecast_period_days > 0 else 0
            
            # Get average lead time for this product (default to 7 days if not found)
            avg_lead_time = avg_lead_times.get(product_id, 7.0)
            if avg_lead_time <= 0:
                avg_lead_time = 7.0  # Default to 7 days if no lead time data
            
            # Calculate safety stock: buffer for uncertainty (1.5x lead time demand)
            safety_stock = int(daily_demand * avg_lead_time * 1.5)
            
            # Calculate reorder point: when to place order (lead time demand + safety stock)
            reorder_point = int(daily_demand * avg_lead_time) + safety_stock
            
            # Calculate EOQ (Economic Order Quantity): simple formula based on demand
            # Basic EOQ approximation: sqrt(2 * annual_demand * ordering_cost / holding_cost)
            # Simplified: use a multiplier of monthly demand (e.g., 2-3 months worth)
            monthly_demand = daily_demand * 30
            eoq = int(monthly_demand * 2.5)  # Order ~2.5 months worth
            if eoq < 10:  # Minimum order quantity
                eoq = 10
            
            # Calculate maximum stock: reorder point + EOQ (with some buffer)
            maximum_stock = reorder_point + eoq
            
            guardrail = Guardrail(
                product_id=product_id,
                product_name=product_name,
                reorder_point=reorder_point,
                safety_stock=safety_stock,
                maximum_stock=maximum_stock,
                eoq=eoq,
                valid_period_start=sales_forecast.forecast_period_start,
                valid_period_end=sales_forecast.forecast_period_end,
                calculated_at=now,
            )
            guardrails.append(guardrail)
        
        return GuardrailStore(
            items=guardrails,
            calculated_at=now,
        )
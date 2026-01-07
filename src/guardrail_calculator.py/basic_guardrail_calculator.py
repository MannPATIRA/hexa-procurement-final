from datetime import datetime, timedelta
from collections import defaultdict
from interface import GuardrailCalculatorInterface
from models.supplier_state import SupplierStateStore
from models.materials_forecast import MaterialsForecast
from models.guardrails import GuardrailStore, Guardrail

class BasicGuardrailCalculator(GuardrailCalculatorInterface):
    def calculate_guardrails(self, supplier_state_store: SupplierStateStore, materials_forecast: MaterialsForecast) -> GuardrailStore:
        """Calculate guardrails (reorder points, safety stock, etc.) based on materials forecast and supplier lead times.
        
        This implementation:
        1. Uses default lead time for materials (since SupplierStateStore tracks products, not materials)
        2. Calculates daily demand from materials forecast
        3. Calculates safety stock, reorder point, max stock, and EOQ
        """
        now = datetime.now()
        
        # Calculate forecast period in days
        forecast_period_days = (materials_forecast.forecast_period_end - materials_forecast.forecast_period_start).days
        if forecast_period_days == 0:
            forecast_period_days = 1
        
        # Since SupplierStateStore tracks products (not materials), we use a default lead time
        # This can be enhanced later if material-to-supplier mappings are added
        default_lead_time_days = 7.0
        
        # Calculate guardrails for each material in materials forecast
        guardrails = []
        for forecast_item in materials_forecast.forecasts:
            material_id = forecast_item.material_id
            material_name = forecast_item.material_name
            
            # Calculate daily demand from forecast
            daily_demand = forecast_item.forecasted_quantity / forecast_period_days if forecast_period_days > 0 else 0
            
            # Use default lead time for materials
            avg_lead_time = default_lead_time_days
            
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
                material_id=material_id,
                material_name=material_name,
                reorder_point=reorder_point,
                safety_stock=safety_stock,
                maximum_stock=maximum_stock,
                eoq=eoq,
                valid_period_start=materials_forecast.forecast_period_start,
                valid_period_end=materials_forecast.forecast_period_end,
                calculated_at=now,
            )
            guardrails.append(guardrail)
        
        return GuardrailStore(
            items=guardrails,
            calculated_at=now,
        )
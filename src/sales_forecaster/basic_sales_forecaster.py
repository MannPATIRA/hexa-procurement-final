from datetime import datetime, timedelta
from collections import defaultdict
from sales_forecaster.interface import SalesForecasterInterface
from models.inventory_data import InventoryData
from models.sales_data import SalesData
from models.sales_forecast import SalesForecast, ForecastItem

class BasicSalesForecaster(SalesForecasterInterface):
    def forecast_sales(self, inventory_data: InventoryData, sales_data: SalesData, forecast_period_days: int) -> SalesForecast:
        """Generate a basic sales forecast based on historical sales data.
        
        This implementation calculates average daily sales for each product
        and projects that forward for the forecast period.
        """
        now = datetime.now()
        forecast_period_start = now
        forecast_period_end = now + timedelta(days=forecast_period_days)
        
        # Calculate total sales and days in historical period for each product
        product_sales: dict[str, dict] = defaultdict(lambda: {"total_quantity": 0, "total_revenue": 0.0, "sale_days": set()})
        
        for record in sales_data.records:
            product_id = record.product_id
            if product_id not in product_sales:
                product_sales[product_id] = {"total_quantity": 0, "total_revenue": 0.0, "sale_days": set()}
            product_sales[product_id]["total_quantity"] += record.quantity_sold
            product_sales[product_id]["total_revenue"] += record.total_revenue
            product_sales[product_id]["sale_days"].add(record.timestamp.date())
        
        # Calculate historical period in days
        historical_days = (sales_data.end_date - sales_data.start_date).days
        if historical_days == 0:
            historical_days = 1  # Avoid division by zero
        
        # Create forecast items for each inventory item
        forecast_items = []
        for item in inventory_data.items:
            # Get sales data for this product
            sales_info = product_sales.get(item.item_id, {"total_quantity": 0, "total_revenue": 0.0, "sale_days": set()})
            
            # Calculate average daily sales
            # Use the full historical period to get average daily rate
            # This accounts for days with no sales, giving a realistic projection
            avg_daily_quantity = sales_info["total_quantity"] / historical_days
            avg_daily_revenue = sales_info["total_revenue"] / historical_days
            
            # Project forward for forecast period
            forecasted_quantity = int(avg_daily_quantity * forecast_period_days)
            forecasted_revenue = avg_daily_revenue * forecast_period_days
            
            # Simple confidence: higher if we have more historical data
            confidence_level = min(1.0, len([r for r in sales_data.records if r.product_id == item.item_id]) / 10.0)
            if confidence_level == 0:
                confidence_level = 0.5  # Default confidence for products with no sales history
            
            forecast_item = ForecastItem(
                item_id=item.item_id,
                item_name=item.item_name,
                forecasted_quantity=forecasted_quantity,
                forecast_period_start=forecast_period_start,
                forecast_period_end=forecast_period_end,
                confidence_level=confidence_level,
                forecasted_revenue=forecasted_revenue,
            )
            forecast_items.append(forecast_item)
        
        return SalesForecast(
            forecasts=forecast_items,
            forecast_generated_at=now,
            forecast_period_start=forecast_period_start,
            forecast_period_end=forecast_period_end,
        )
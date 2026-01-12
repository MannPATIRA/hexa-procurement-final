from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict
from materials_forecaster.interface import MaterialsForecasterInterface
from models.sales_forecast import SalesForecast
from models.sales_data import SalesData
from models.bom import BOMData
from models.materials_forecast import MaterialsForecast, MaterialForecastItem

class BasicMaterialsForecaster(MaterialsForecasterInterface):
    def __init__(self, materials_lookup: Optional[dict[str, str]] = None):
        """Initialize materials forecaster with optional materials lookup.
        
        Args:
            materials_lookup: Dictionary mapping material_id to material_name.
                             If None, will use material_id as name.
        """
        self.materials_lookup = materials_lookup or {}
    
    def forecast_materials(self, sales_forecast: SalesForecast, bom_data: BOMData, forecast_period_days: int) -> MaterialsForecast:
        """Generate a materials forecast based on sales forecast and BOM data.
        
        This implementation:
        1. For each product in the sales forecast, finds its BOM requirements
        2. Calculates material needs: forecasted_product_quantity * material_quantity_required
        3. Aggregates material requirements across all products
        """
        now = datetime.now()
        
        # Use items_by_product index from BOM data
        bom_by_product = bom_data.items_by_product
        
        # Aggregate material requirements
        # Key: material_id, Value: total_quantity, confidence_sum, confidence_count
        material_requirements: dict[str, dict] = defaultdict(lambda: {
            "total_quantity": 0.0,
            "confidence_sum": 0.0,
            "confidence_count": 0
        })
        
        # Process each product forecast
        for product_forecast in sales_forecast.forecasts:
            product_id = product_forecast.item_id
            forecasted_quantity = product_forecast.forecasted_quantity
            product_confidence = product_forecast.confidence_level or 0.5
            
            # Get BOM items for this product
            bom_items = bom_by_product.get(product_id, [])
            
            for bom_item in bom_items:
                material_id = bom_item.material_id
                quantity_required = bom_item.quantity_required
                
                # Calculate material requirement: product quantity * material per product
                material_quantity = forecasted_quantity * quantity_required
                
                # Aggregate material requirements
                material_requirements[material_id]["total_quantity"] += material_quantity
                material_requirements[material_id]["confidence_sum"] += product_confidence
                material_requirements[material_id]["confidence_count"] += 1
        
        # Create forecast items for each material
        forecast_items = []
        for material_id, requirements in material_requirements.items():
            # Calculate average confidence for this material
            avg_confidence = (
                requirements["confidence_sum"] / requirements["confidence_count"]
                if requirements["confidence_count"] > 0
                else 0.5
            )
            
            # Get material name from lookup, or use material_id as fallback
            material_name = self.materials_lookup.get(material_id, f"Material {material_id}")
            
            forecast_item = MaterialForecastItem(
                material_id=material_id,
                material_name=material_name,
                forecasted_quantity=requirements["total_quantity"],
                forecast_period_start=sales_forecast.forecast_period_start,
                forecast_period_end=sales_forecast.forecast_period_end,
                confidence_level=avg_confidence,
            )
            forecast_items.append(forecast_item)
        
        return MaterialsForecast(
            forecasts=forecast_items,
            forecast_generated_at=now,
            forecast_period_start=sales_forecast.forecast_period_start,
            forecast_period_end=sales_forecast.forecast_period_end,
        )
    
    def calculate_historical_usage(
        self, 
        sales_data: SalesData, 
        bom_data: BOMData
    ) -> Dict[str, List[Dict[str, any]]]:
        """
        Calculate historical materials usage from sales history.
        
        For each sales record, looks up the product's BOM and calculates
        materials consumed: quantity_sold * material_quantity_required.
        Aggregates by day and material to create a time series.
        
        Args:
            sales_data: Historical sales records
            bom_data: Bill of Materials data
            
        Returns:
            Dictionary mapping material_id to list of daily usage records.
            Each record contains: {'date': datetime, 'quantity_used': float}
        """
        # Use items_by_product index from BOM data
        bom_by_product = bom_data.items_by_product
        
        # Aggregate materials usage by day
        # Structure: material_id -> date -> total_quantity
        daily_usage: Dict[str, Dict[datetime.date, float]] = defaultdict(lambda: defaultdict(float))
        
        # Process each sales record
        for record in sales_data.records:
            product_id = record.product_id
            quantity_sold = record.quantity_sold
            sale_date = record.timestamp.date()
            
            # Get BOM items for this product
            bom_items = bom_by_product.get(product_id, [])
            
            # Calculate materials used for this sale
            for bom_item in bom_items:
                material_id = bom_item.material_id
                quantity_required = bom_item.quantity_required
                
                # Calculate material usage: quantity_sold * material per product
                material_quantity = quantity_sold * quantity_required
                
                # Aggregate by date
                daily_usage[material_id][sale_date] += material_quantity
        
        # Convert to list format with material names
        result: Dict[str, List[Dict[str, any]]] = {}
        
        for material_id, date_usage in daily_usage.items():
            # Get material name from lookup
            material_name = self.materials_lookup.get(material_id, f"Material {material_id}")
            
            # Create list of daily usage records, sorted by date
            usage_records = []
            for date, quantity in sorted(date_usage.items()):
                usage_records.append({
                    'date': datetime.combine(date, datetime.min.time()),
                    'quantity_used': quantity,
                    'material_id': material_id,
                    'material_name': material_name
                })
            
            result[material_id] = usage_records
        
        return result
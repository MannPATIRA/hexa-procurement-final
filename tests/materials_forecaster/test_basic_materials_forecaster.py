"""Test cases for BasicMaterialsForecaster."""

from datetime import datetime, timedelta
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.materials_forecast import MaterialsForecast


def test_forecast_materials_returns_materials_forecast():
    """Test that forecast_materials returns a MaterialsForecast instance."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Now forecast materials
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    assert isinstance(result, MaterialsForecast)


def test_forecast_materials_has_forecasts():
    """Test that returned materials forecast contains forecast items."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Now forecast materials
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    assert len(result.forecasts) > 0


def test_forecast_materials_has_correct_period():
    """Test that forecast period dates match the sales forecast period."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Now forecast materials
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    # Materials forecast should have same period as sales forecast
    assert result.forecast_period_start == sales_forecast.forecast_period_start
    assert result.forecast_period_end == sales_forecast.forecast_period_end
    assert result.forecast_period_start <= datetime.now()
    assert result.forecast_period_end > result.forecast_period_start


def test_forecast_materials_has_material_names():
    """Test that forecast items have proper material names from lookup."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Now forecast materials
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    # Check that material names are from lookup, not just "Material MAT-XXX"
    for forecast_item in result.forecasts:
        assert forecast_item.material_name != f"Material {forecast_item.material_id}"
        assert forecast_item.material_name in materials_lookup.values()


def test_forecast_materials_aggregates_materials():
    """Test that materials are aggregated across multiple products."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Now forecast materials
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    # MAT-001 is used by multiple products (PROD-001, PROD-002, PROD-004)
    # So it should have aggregated quantity > 0
    mat_001_forecast = next((f for f in result.forecasts if f.material_id == "MAT-001"), None)
    assert mat_001_forecast is not None
    assert mat_001_forecast.forecasted_quantity > 0


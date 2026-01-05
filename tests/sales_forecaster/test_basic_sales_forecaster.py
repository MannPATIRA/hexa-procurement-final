"""Test cases for BasicSalesForecaster."""

from datetime import datetime, timedelta
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.sales_forecast import SalesForecast


def test_forecast_sales_returns_sales_forecast():
    """Test that forecast_sales returns a SalesForecast instance."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert isinstance(result, SalesForecast)


def test_forecast_sales_has_forecasts():
    """Test that returned sales forecast contains forecast items."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) > 0


def test_forecast_sales_has_correct_period():
    """Test that forecast period dates are set correctly."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    assert result.forecast_period_start <= datetime.now()
    assert result.forecast_period_end > result.forecast_period_start
    expected_end = result.forecast_period_start + timedelta(days=forecast_period_days)
    assert abs((result.forecast_period_end - expected_end).total_seconds()) < 1  # Within 1 second


def test_forecast_sales_has_forecast_items_for_all_products():
    """Test that forecast contains items for all inventory products."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Should have a forecast for each inventory item
    assert len(result.forecasts) == len(inventory_data.items)
    
    # Check that all inventory item IDs are in forecasts
    inventory_item_ids = {item.item_id for item in inventory_data.items}
    forecast_item_ids = {forecast.item_id for forecast in result.forecasts}
    assert inventory_item_ids == forecast_item_ids


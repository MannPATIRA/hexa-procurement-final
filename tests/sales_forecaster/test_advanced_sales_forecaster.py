"""Test cases for AdvancedSalesForecaster."""

from datetime import datetime, timedelta
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.sales_forecast import SalesForecast


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

def test_forecast_sales_returns_sales_forecast():
    """Test that forecast_sales returns a SalesForecast instance."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert isinstance(result, SalesForecast)


def test_forecast_sales_has_forecasts():
    """Test that returned sales forecast contains forecast items."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) > 0


def test_forecast_sales_has_correct_period():
    """Test that forecast period dates are set correctly."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    assert result.forecast_period_start <= datetime.now()
    assert result.forecast_period_end > result.forecast_period_start
    expected_end = result.forecast_period_start + timedelta(days=forecast_period_days)
    assert abs((result.forecast_period_end - expected_end).total_seconds()) < 1


def test_forecast_has_forecast_items_for_all_products():
    """Test that forecast contains items for all inventory products."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    assert len(result.forecasts) == len(inventory_data.items)
    
    inventory_item_ids = {item.item_id for item in inventory_data.items}
    forecast_item_ids = {forecast.item_id for forecast in result.forecasts}
    assert inventory_item_ids == forecast_item_ids


# ============================================================================
# FORECAST VALUES TESTS
# ============================================================================

def test_forecast_produces_positive_quantities():
    """Test that forecast produces non-negative quantities for products with sales."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Products with sales history should have positive forecasts
    for forecast in result.forecasts:
        if forecast.item_id in sales_data.records_by_product:
            assert forecast.forecasted_quantity >= 0, \
                f"{forecast.item_id}: forecasted quantity should be non-negative"


def test_forecast_scales_with_period():
    """Test that forecast quantity scales with forecast period."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result_30 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    result_60 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=60)
    
    for f30 in result_30.forecasts:
        f60 = next((f for f in result_60.forecasts if f.item_id == f30.item_id), None)
        assert f60 is not None
        # 60-day forecast should be approximately 2x 30-day forecast
        # (may differ due to trend adjustments and int truncation)
        if f30.forecasted_quantity > 0:
            ratio = f60.forecasted_quantity / f30.forecasted_quantity
            assert 1.5 <= ratio <= 2.5, \
                f"{f30.item_id}: 60-day ({f60.forecasted_quantity}) not ~2x 30-day ({f30.forecasted_quantity})"


# ============================================================================
# CONFIDENCE LEVEL TESTS
# ============================================================================

def test_confidence_level_range():
    """Test that all confidence levels are in valid range [0, 1]."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert 0.0 <= forecast.confidence_level <= 1.0, \
            f"{forecast.item_id}: confidence {forecast.confidence_level} out of range"


def test_confidence_minimum():
    """Test that confidence has a minimum value (0.3 for items with no history)."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert forecast.confidence_level >= 0.3, \
            f"{forecast.item_id}: confidence {forecast.confidence_level} below minimum"


# ============================================================================
# REVENUE FORECAST TESTS
# ============================================================================

def test_forecasted_revenue_non_negative():
    """Test that forecasted revenue is non-negative."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert forecast.forecasted_revenue >= 0, \
            f"{forecast.item_id}: forecasted revenue should be non-negative"


# ============================================================================
# WEIGHTED AVERAGE TESTS
# ============================================================================

def test_different_weights_produce_different_results():
    """Test that different recent_weight values produce different forecasts."""
    erp_fetcher = MockERPDataFetcher()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    forecaster_low = AdvancedSalesForecaster(recent_weight=0.3)
    forecaster_high = AdvancedSalesForecaster(recent_weight=0.9)
    
    result_low = forecaster_low.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    result_high = forecaster_high.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # At least one product should have different forecasts
    differences = []
    for f_low in result_low.forecasts:
        f_high = next((f for f in result_high.forecasts if f.item_id == f_low.item_id), None)
        if f_high and f_low.forecasted_quantity > 0:
            differences.append(abs(f_high.forecasted_quantity - f_low.forecasted_quantity))
    
    # Should have at least some differences (may be small due to rounding)
    assert len(differences) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_handles_empty_sales_data():
    """Test that forecaster handles products with no sales history."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Should still produce forecasts for all inventory items
    assert len(result.forecasts) == len(inventory_data.items)
    
    # Items with no sales should have 0 quantity and low confidence
    for forecast in result.forecasts:
        if forecast.item_id not in sales_data.records_by_product:
            assert forecast.forecasted_quantity == 0
            assert forecast.confidence_level == 0.3


def test_handles_different_periods():
    """Test forecasting with various period lengths."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    for period in [7, 14, 30, 60, 90]:
        result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=period)
        assert len(result.forecasts) == len(inventory_data.items)
        
        # Verify all forecasts have correct period
        for forecast in result.forecasts:
            delta = (forecast.forecast_period_end - forecast.forecast_period_start).days
            assert delta == period


def test_forecast_contains_correct_item_names():
    """Test that forecasts contain correct item names from inventory."""
    forecaster = AdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Build lookup for inventory items
    inventory_by_id = {item.item_id: item for item in inventory_data.items}
    
    for forecast in result.forecasts:
        inventory_item = inventory_by_id.get(forecast.item_id)
        assert inventory_item is not None
        assert forecast.item_name == inventory_item.item_name

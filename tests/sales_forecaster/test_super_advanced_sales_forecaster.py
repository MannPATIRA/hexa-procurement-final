"""Test cases for SuperAdvancedSalesForecaster."""

from datetime import datetime, timedelta
from sales_forecaster.super_advanced_sales_forecaster import (
    SuperAdvancedSalesForecaster,
    ModelType,
    ProductDiagnostics,
)
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.sales_forecast import SalesForecast


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

def test_forecast_sales_returns_sales_forecast():
    """Test that forecast_sales returns a SalesForecast instance."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert isinstance(result, SalesForecast)


def test_forecast_sales_has_forecasts():
    """Test that returned sales forecast contains forecast items."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) > 0


def test_forecast_has_forecast_items_for_all_products():
    """Test that forecast contains items for all inventory products."""
    forecaster = SuperAdvancedSalesForecaster()
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

def test_forecast_produces_non_negative_quantities():
    """Test that forecast produces non-negative quantities."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert forecast.forecasted_quantity >= 0, \
            f"{forecast.item_id}: forecasted quantity should be non-negative"


def test_forecast_produces_non_negative_revenue():
    """Test that forecast produces non-negative revenue."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert forecast.forecasted_revenue >= 0, \
            f"{forecast.item_id}: forecasted revenue should be non-negative"


# ============================================================================
# CONFIDENCE LEVEL TESTS
# ============================================================================

def test_confidence_level_range():
    """Test that all confidence levels are in valid range [0, 1]."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert 0.0 <= forecast.confidence_level <= 1.0, \
            f"{forecast.item_id}: confidence {forecast.confidence_level} out of range"


# ============================================================================
# ROUTING TESTS
# ============================================================================

def test_routing_log_populated():
    """Test that routing log is populated after forecasting."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    routing_log = forecaster.get_routing_log()
    assert len(routing_log) > 0


def test_routing_log_contains_required_fields():
    """Test that routing log entries contain required fields."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    routing_log = forecaster.get_routing_log()
    for entry in routing_log:
        assert 'product_id' in entry
        assert 'recommended_model' in entry
        assert 'history_length' in entry
        assert 'data_quality' in entry


def test_model_summary():
    """Test that model summary is available."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    summary = forecaster.get_model_summary()
    assert isinstance(summary, dict)
    assert len(summary) > 0


# ============================================================================
# FREQUENCY TESTS
# ============================================================================

def test_weekly_frequency():
    """Test forecasting with weekly frequency."""
    forecaster = SuperAdvancedSalesForecaster(frequency="weekly")
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) == len(inventory_data.items)


def test_monthly_frequency():
    """Test forecasting with monthly frequency."""
    forecaster = SuperAdvancedSalesForecaster(frequency="monthly")
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) == len(inventory_data.items)


# ============================================================================
# PARAMETER TESTS
# ============================================================================

def test_custom_smoothing_parameters():
    """Test with custom smoothing parameters."""
    forecaster = SuperAdvancedSalesForecaster(
        alpha=0.5,
        beta=0.2,
        gamma=0.2
    )
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) > 0


def test_different_periods():
    """Test forecasting with different forecast periods."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    for period in [7, 14, 30, 60, 90]:
        result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=period)
        assert len(result.forecasts) == len(inventory_data.items)


# ============================================================================
# PRINT DIAGNOSTICS (for manual inspection)
# ============================================================================

def test_print_diagnostics():
    """Print diagnostics for manual inspection."""
    forecaster = SuperAdvancedSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    print("\n" + "="*80)
    print("SUPER ADVANCED SALES FORECASTER - DIAGNOSTICS")
    print("="*80)
    
    # Print routing log
    print("\nRouting Decisions:")
    print("-"*80)
    for entry in forecaster.get_routing_log():
        print(f"  {entry['product_id']}: {entry['recommended_model']} "
              f"(history={entry['history_length']}, quality={entry['data_quality']:.2f})")
    
    # Print model summary
    print("\nModel Summary:")
    print("-"*80)
    for model, count in forecaster.get_model_summary().items():
        print(f"  {model}: {count} products")
    
    # Print forecasts
    print("\nForecasts:")
    print("-"*80)
    for forecast in result.forecasts:
        print(f"  {forecast.item_name}: qty={forecast.forecasted_quantity}, "
              f"revenue=${forecast.forecasted_revenue:.2f}, "
              f"confidence={forecast.confidence_level:.2f}")
    
    print("="*80)
    
    assert True  # Always pass - this is for inspection

"""Test cases for BasicSalesForecaster with formula verification."""

from datetime import datetime, timedelta
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.sales_forecast import SalesForecast


# ============================================================================
# EXPECTED VALUES FROM MOCK DATA
# ============================================================================
# The forecaster uses:
#   avg_daily_quantity = total_quantity / historical_days (30)
#   forecasted_quantity = avg_daily_quantity * forecast_period_days
#
# From mock_erp.py sales data (30-day historical period):
# PROD-001: total 100 units, avg 3.33/day, 30-day forecast = 100
# PROD-002: total 40 units, avg 1.33/day, 30-day forecast = 40
# PROD-003: total 20 units, avg 0.67/day, 30-day forecast = 20
# PROD-004: total 97 units, avg 3.23/day, 30-day forecast = 97

HISTORICAL_PERIOD_DAYS = 30

EXPECTED_SALES_DATA = {
    "PROD-001": {"total_qty": 100, "sales_count": 5, "total_revenue": 2550.00},
    "PROD-002": {"total_qty": 40, "sales_count": 4, "total_revenue": 1800.00},
    "PROD-003": {"total_qty": 20, "sales_count": 4, "total_revenue": 1500.00},
    "PROD-004": {"total_qty": 97, "sales_count": 5, "total_revenue": 3395.00},
}


def _calculate_expected_forecast(product_id: str, forecast_days: int) -> int:
    """Calculate expected forecast quantity using the forecaster's formula."""
    total_qty = EXPECTED_SALES_DATA[product_id]["total_qty"]
    avg_daily = total_qty / HISTORICAL_PERIOD_DAYS
    return int(avg_daily * forecast_days)


def _calculate_expected_revenue(product_id: str, forecast_days: int) -> float:
    """Calculate expected forecast revenue using the forecaster's formula."""
    total_revenue = EXPECTED_SALES_DATA[product_id]["total_revenue"]
    avg_daily = total_revenue / HISTORICAL_PERIOD_DAYS
    return avg_daily * forecast_days


def _calculate_expected_confidence(product_id: str) -> float:
    """Calculate expected confidence level: min(1.0, sales_count / 10)."""
    sales_count = EXPECTED_SALES_DATA[product_id]["sales_count"]
    return min(1.0, sales_count / 10.0)


# ============================================================================
# BASIC TESTS
# ============================================================================

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


def test_forecast_sales_has_exactly_four_forecasts():
    """Test that forecast contains exactly 4 forecast items (one per product)."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    assert len(result.forecasts) == 4


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
    assert abs((result.forecast_period_end - expected_end).total_seconds()) < 1


def test_forecast_sales_has_forecast_items_for_all_products():
    """Test that forecast contains items for all inventory products."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    assert len(result.forecasts) == len(inventory_data.items)
    
    inventory_item_ids = {item.item_id for item in inventory_data.items}
    forecast_item_ids = {forecast.item_id for forecast in result.forecasts}
    assert inventory_item_ids == forecast_item_ids


# ============================================================================
# FORMULA VERIFICATION TESTS
# ============================================================================

def test_forecast_quantity_formula_prod001():
    """Test forecast quantity formula for PROD-001: (total/30) * forecast_days."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    prod001_forecast = next((f for f in result.forecasts if f.item_id == "PROD-001"), None)
    assert prod001_forecast is not None
    
    # PROD-001: 100 units total / 30 days * 30 = 100
    expected_qty = _calculate_expected_forecast("PROD-001", forecast_period_days)
    assert prod001_forecast.forecasted_quantity == expected_qty, \
        f"PROD-001: expected {expected_qty}, got {prod001_forecast.forecasted_quantity}"


def test_forecast_quantity_formula_prod002():
    """Test forecast quantity formula for PROD-002."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    prod002_forecast = next((f for f in result.forecasts if f.item_id == "PROD-002"), None)
    assert prod002_forecast is not None
    
    # PROD-002: 40 units total / 30 days * 30 = 40
    expected_qty = _calculate_expected_forecast("PROD-002", forecast_period_days)
    assert prod002_forecast.forecasted_quantity == expected_qty, \
        f"PROD-002: expected {expected_qty}, got {prod002_forecast.forecasted_quantity}"


def test_forecast_quantity_formula_prod003():
    """Test forecast quantity formula for PROD-003."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    prod003_forecast = next((f for f in result.forecasts if f.item_id == "PROD-003"), None)
    assert prod003_forecast is not None
    
    # PROD-003: 20 units total / 30 days * 30 = 20
    expected_qty = _calculate_expected_forecast("PROD-003", forecast_period_days)
    assert prod003_forecast.forecasted_quantity == expected_qty, \
        f"PROD-003: expected {expected_qty}, got {prod003_forecast.forecasted_quantity}"


def test_forecast_quantity_formula_prod004():
    """Test forecast quantity formula for PROD-004."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    prod004_forecast = next((f for f in result.forecasts if f.item_id == "PROD-004"), None)
    assert prod004_forecast is not None
    
    # PROD-004: 97 units total / 30 days * 30 = 97
    expected_qty = _calculate_expected_forecast("PROD-004", forecast_period_days)
    assert prod004_forecast.forecasted_quantity == expected_qty, \
        f"PROD-004: expected {expected_qty}, got {prod004_forecast.forecasted_quantity}"


def test_forecast_all_quantities_for_30_days():
    """Test all forecast quantities for 30-day period."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    forecast_map = {f.item_id: f.forecasted_quantity for f in result.forecasts}
    
    # For 30-day forecast over 30-day history, quantity equals total sales
    assert forecast_map["PROD-001"] == 100
    assert forecast_map["PROD-002"] == 40
    assert forecast_map["PROD-003"] == 20
    assert forecast_map["PROD-004"] == 97


def test_forecast_scales_with_period():
    """Test that forecast quantity scales linearly with forecast period."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result_30 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    result_60 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=60)
    
    for f30 in result_30.forecasts:
        f60 = next((f for f in result_60.forecasts if f.item_id == f30.item_id), None)
        assert f60 is not None
        # 60-day forecast should be approximately 2x 30-day forecast
        # (may differ due to int truncation)
        if f30.forecasted_quantity > 0:
            ratio = f60.forecasted_quantity / f30.forecasted_quantity
            assert 1.8 <= ratio <= 2.2, \
                f"{f30.item_id}: 60-day ({f60.forecasted_quantity}) not ~2x 30-day ({f30.forecasted_quantity})"


# ============================================================================
# CONFIDENCE LEVEL TESTS
# ============================================================================

def test_confidence_level_formula():
    """Test confidence level formula: min(1.0, sales_record_count / 10)."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    confidence_map = {f.item_id: f.confidence_level for f in result.forecasts}
    
    # PROD-001: 5 sales records → 5/10 = 0.5
    assert confidence_map["PROD-001"] == _calculate_expected_confidence("PROD-001")
    
    # PROD-002: 4 sales records → 4/10 = 0.4
    assert confidence_map["PROD-002"] == _calculate_expected_confidence("PROD-002")
    
    # PROD-003: 4 sales records → 4/10 = 0.4
    assert confidence_map["PROD-003"] == _calculate_expected_confidence("PROD-003")
    
    # PROD-004: 5 sales records → 5/10 = 0.5
    assert confidence_map["PROD-004"] == _calculate_expected_confidence("PROD-004")


def test_confidence_level_range():
    """Test that all confidence levels are in valid range [0, 1]."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        assert 0.0 <= forecast.confidence_level <= 1.0, \
            f"{forecast.item_id}: confidence {forecast.confidence_level} out of range"


# ============================================================================
# REVENUE FORECAST TESTS
# ============================================================================

def test_forecasted_revenue_formula():
    """Test that forecasted_revenue = (total_revenue/30) * forecast_days."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    for forecast in result.forecasts:
        expected_revenue = _calculate_expected_revenue(forecast.item_id, 30)
        assert abs(forecast.forecasted_revenue - expected_revenue) < 0.01, \
            f"{forecast.item_id}: expected revenue {expected_revenue}, got {forecast.forecasted_revenue}"


def test_forecasted_revenue_exact_values():
    """Test exact revenue values for 30-day forecast."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    revenue_map = {f.item_id: f.forecasted_revenue for f in result.forecasts}
    
    # For 30-day forecast over 30-day history, revenue equals total revenue
    assert abs(revenue_map["PROD-001"] - 2550.00) < 0.01
    assert abs(revenue_map["PROD-002"] - 1800.00) < 0.01
    assert abs(revenue_map["PROD-003"] - 1500.00) < 0.01
    assert abs(revenue_map["PROD-004"] - 3395.00) < 0.01


# ============================================================================
# ITEM METADATA TESTS
# ============================================================================

def test_forecast_contains_correct_item_names():
    """Test that forecasts contain correct item names from inventory."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    name_map = {f.item_id: f.item_name for f in result.forecasts}
    
    assert name_map["PROD-001"] == "Widget A"
    assert name_map["PROD-002"] == "Widget B"
    assert name_map["PROD-003"] == "Widget C"
    assert name_map["PROD-004"] == "Widget D"


def test_forecast_period_dates_on_each_item():
    """Test that each forecast item has correct period dates."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    for forecast in result.forecasts:
        # Each item should have same period as the overall forecast
        assert forecast.forecast_period_start == result.forecast_period_start
        assert forecast.forecast_period_end == result.forecast_period_end
        
        # Period should be exactly forecast_period_days
        delta = (forecast.forecast_period_end - forecast.forecast_period_start).days
        assert delta == forecast_period_days


# ============================================================================
# SCALING TESTS
# ============================================================================

def test_forecast_handles_different_periods():
    """Test forecasting with various period lengths."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    for period in [7, 14, 30, 60, 90]:
        result = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=period)
        assert len(result.forecasts) == 4
        
        # Verify quantities scale with period
        for forecast in result.forecasts:
            expected = _calculate_expected_forecast(forecast.item_id, period)
            assert forecast.forecasted_quantity == expected, \
                f"{forecast.item_id} for {period} days: expected {expected}, got {forecast.forecasted_quantity}"


def test_90_day_forecast_is_3x_30_day():
    """Test that 90-day forecast is approximately 3x 30-day forecast."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    
    result_30 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    result_90 = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=90)
    
    for f30 in result_30.forecasts:
        f90 = next((f for f in result_90.forecasts if f.item_id == f30.item_id), None)
        assert f90 is not None
        if f30.forecasted_quantity > 0:
            ratio = f90.forecasted_quantity / f30.forecasted_quantity
            assert 2.8 <= ratio <= 3.2, \
                f"{f30.item_id}: 90-day not ~3x 30-day"

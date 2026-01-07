"""Test cases for BasicMaterialsForecaster with formula verification."""

from datetime import datetime, timedelta
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.materials_forecast import MaterialsForecast


# ============================================================================
# EXPECTED VALUES FROM MOCK DATA
# ============================================================================
# From sales forecast (30-day forecast over 30-day history):
#   PROD-001: 100 units
#   PROD-002: 40 units
#   PROD-003: 20 units
#   PROD-004: 97 units
#
# BOM requirements:
#   PROD-001: MAT-001 (2.5), MAT-002 (1.0)
#   PROD-002: MAT-001 (3.0), MAT-003 (2.0)
#   PROD-003: MAT-002 (4.5), MAT-004 (1.5)
#   PROD-004: MAT-001 (2.0), MAT-003 (1.5)
#
# Expected material quantities (30 days):
#   MAT-001 = 100*2.5 + 40*3.0 + 97*2.0 = 250 + 120 + 194 = 564
#   MAT-002 = 100*1.0 + 20*4.5 = 100 + 90 = 190
#   MAT-003 = 40*2.0 + 97*1.5 = 80 + 145.5 = 225.5
#   MAT-004 = 20*1.5 = 30

EXPECTED_PRODUCT_SALES_30_DAYS = {
    "PROD-001": 100,
    "PROD-002": 40,
    "PROD-003": 20,
    "PROD-004": 97,
}

BOM_REQUIREMENTS = {
    "PROD-001": {"MAT-001": 2.5, "MAT-002": 1.0},
    "PROD-002": {"MAT-001": 3.0, "MAT-003": 2.0},
    "PROD-003": {"MAT-002": 4.5, "MAT-004": 1.5},
    "PROD-004": {"MAT-001": 2.0, "MAT-003": 1.5},
}

EXPECTED_MATERIAL_QUANTITIES_30_DAYS = {
    "MAT-001": 564.0,   # 100*2.5 + 40*3.0 + 97*2.0
    "MAT-002": 190.0,   # 100*1.0 + 20*4.5
    "MAT-003": 225.5,   # 40*2.0 + 97*1.5
    "MAT-004": 30.0,    # 20*1.5
}

EXPECTED_MATERIAL_NAMES = {
    "MAT-001": "Steel Component",
    "MAT-002": "Plastic Housing",
    "MAT-003": "Electronic Circuit Board",
    "MAT-004": "Rubber Gasket",
}


def _get_materials_forecast(forecast_period_days=30):
    """Helper to generate materials forecast from mock data."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    return materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days)


# ============================================================================
# BASIC TESTS
# ============================================================================

def test_forecast_materials_returns_materials_forecast():
    """Test that forecast_materials returns a MaterialsForecast instance."""
    result = _get_materials_forecast()
    assert isinstance(result, MaterialsForecast)


def test_forecast_materials_has_exactly_four_materials():
    """Test that forecast contains exactly 4 materials."""
    result = _get_materials_forecast()
    assert len(result.forecasts) == 4


def test_forecast_materials_has_correct_material_ids():
    """Test that forecast contains the correct material IDs."""
    result = _get_materials_forecast()
    
    material_ids = {f.material_id for f in result.forecasts}
    expected_ids = {"MAT-001", "MAT-002", "MAT-003", "MAT-004"}
    assert material_ids == expected_ids


def test_forecast_materials_has_correct_period():
    """Test that forecast period dates match the sales forecast period."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    assert result.forecast_period_start == sales_forecast.forecast_period_start
    assert result.forecast_period_end == sales_forecast.forecast_period_end


# ============================================================================
# FORMULA VERIFICATION TESTS
# ============================================================================

def test_material_quantity_formula_mat001():
    """Test MAT-001 quantity: PROD-001*2.5 + PROD-002*3.0 + PROD-004*2.0 = 564."""
    result = _get_materials_forecast(30)
    
    # Use forecasts_by_id index for direct lookup
    mat001 = result.forecasts_by_id.get("MAT-001")
    assert mat001 is not None
    
    # Formula: 100*2.5 + 40*3.0 + 97*2.0 = 250 + 120 + 194 = 564
    expected = EXPECTED_MATERIAL_QUANTITIES_30_DAYS["MAT-001"]
    assert mat001.forecasted_quantity == expected, \
        f"MAT-001: expected {expected}, got {mat001.forecasted_quantity}"


def test_material_quantity_formula_mat002():
    """Test MAT-002 quantity: PROD-001*1.0 + PROD-003*4.5 = 190."""
    result = _get_materials_forecast(30)
    
    # Use forecasts_by_id index for direct lookup
    mat002 = result.forecasts_by_id.get("MAT-002")
    assert mat002 is not None
    
    # Formula: 100*1.0 + 20*4.5 = 100 + 90 = 190
    expected = EXPECTED_MATERIAL_QUANTITIES_30_DAYS["MAT-002"]
    assert mat002.forecasted_quantity == expected, \
        f"MAT-002: expected {expected}, got {mat002.forecasted_quantity}"


def test_material_quantity_formula_mat003():
    """Test MAT-003 quantity: PROD-002*2.0 + PROD-004*1.5 = 225.5."""
    result = _get_materials_forecast(30)
    
    # Use forecasts_by_id index for direct lookup
    mat003 = result.forecasts_by_id.get("MAT-003")
    assert mat003 is not None
    
    # Formula: 40*2.0 + 97*1.5 = 80 + 145.5 = 225.5
    expected = EXPECTED_MATERIAL_QUANTITIES_30_DAYS["MAT-003"]
    assert mat003.forecasted_quantity == expected, \
        f"MAT-003: expected {expected}, got {mat003.forecasted_quantity}"


def test_material_quantity_formula_mat004():
    """Test MAT-004 quantity: PROD-003*1.5 = 30."""
    result = _get_materials_forecast(30)
    
    # Use forecasts_by_id index for direct lookup
    mat004 = result.forecasts_by_id.get("MAT-004")
    assert mat004 is not None
    
    # Formula: 20*1.5 = 30
    expected = EXPECTED_MATERIAL_QUANTITIES_30_DAYS["MAT-004"]
    assert mat004.forecasted_quantity == expected, \
        f"MAT-004: expected {expected}, got {mat004.forecasted_quantity}"


def test_all_material_quantities_30_days():
    """Test all material quantities for 30-day period."""
    result = _get_materials_forecast(30)
    
    # Use forecasts_by_id index for direct lookup
    for mat_id, expected_qty in EXPECTED_MATERIAL_QUANTITIES_30_DAYS.items():
        actual_qty = result.forecasts_by_id.get(mat_id).forecasted_quantity
        assert actual_qty == expected_qty, \
            f"{mat_id}: expected {expected_qty}, got {actual_qty}"


def test_material_quantities_scale_with_period():
    """Test that material quantities scale linearly with forecast period."""
    result_30 = _get_materials_forecast(30)
    result_60 = _get_materials_forecast(60)
    
    # Use forecasts_by_id indexes for direct comparison
    for mat_id in result_30.forecasts_by_id.keys():
        qty_30 = result_30.forecasts_by_id[mat_id].forecasted_quantity
        qty_60 = result_60.forecasts_by_id[mat_id].forecasted_quantity
        if qty_30 > 0:
            ratio = qty_60 / qty_30
            assert 1.8 <= ratio <= 2.2, \
                f"{mat_id}: 60-day ({qty_60}) not ~2x 30-day ({qty_30})"


# ============================================================================
# MATERIAL NAME TESTS
# ============================================================================

def test_forecast_materials_has_correct_material_names():
    """Test that all materials have correct names from lookup."""
    result = _get_materials_forecast()
    
    name_map = {f.material_id: f.material_name for f in result.forecasts}
    
    for mat_id, expected_name in EXPECTED_MATERIAL_NAMES.items():
        assert name_map[mat_id] == expected_name, \
            f"{mat_id}: expected name '{expected_name}', got '{name_map[mat_id]}'"


def test_forecast_materials_names_not_generic():
    """Test that material names are not generic placeholders."""
    result = _get_materials_forecast()
    
    for forecast in result.forecasts:
        # Should not be "Material MAT-XXX" format
        assert forecast.material_name != f"Material {forecast.material_id}"
        # Should be from the lookup
        assert forecast.material_name in EXPECTED_MATERIAL_NAMES.values()


# ============================================================================
# AGGREGATION TESTS
# ============================================================================

def test_mat001_aggregates_three_products():
    """Test that MAT-001 correctly aggregates demand from PROD-001, PROD-002, PROD-004."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Get individual product forecasts
    prod_forecasts = {f.item_id: f.forecasted_quantity for f in sales_forecast.forecasts}
    
    # Verify product forecasts match expected
    assert prod_forecasts["PROD-001"] == EXPECTED_PRODUCT_SALES_30_DAYS["PROD-001"]
    assert prod_forecasts["PROD-002"] == EXPECTED_PRODUCT_SALES_30_DAYS["PROD-002"]
    assert prod_forecasts["PROD-004"] == EXPECTED_PRODUCT_SALES_30_DAYS["PROD-004"]
    
    # Calculate expected MAT-001: PROD-001*2.5 + PROD-002*3.0 + PROD-004*2.0
    expected_mat001 = (
        prod_forecasts["PROD-001"] * 2.5 +
        prod_forecasts["PROD-002"] * 3.0 +
        prod_forecasts["PROD-004"] * 2.0
    )
    
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    mat001 = next((f for f in result.forecasts if f.material_id == "MAT-001"), None)
    assert mat001.forecasted_quantity == expected_mat001


def test_mat004_uses_single_product():
    """Test that MAT-004 only uses PROD-003 (single product dependency)."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Get PROD-003 forecast
    prod003_forecast = next(f.forecasted_quantity for f in sales_forecast.forecasts if f.item_id == "PROD-003")
    
    # Verify PROD-003 forecast
    assert prod003_forecast == EXPECTED_PRODUCT_SALES_30_DAYS["PROD-003"]
    
    # Calculate expected MAT-004: PROD-003*1.5
    expected_mat004 = prod003_forecast * 1.5
    
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    result = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    mat004 = next((f for f in result.forecasts if f.material_id == "MAT-004"), None)
    assert mat004.forecasted_quantity == expected_mat004


# ============================================================================
# PERIOD DATE TESTS
# ============================================================================

def test_forecast_period_matches_overall():
    """Test that individual forecast items have same period as overall."""
    result = _get_materials_forecast(30)
    
    for forecast in result.forecasts:
        assert forecast.forecast_period_start == result.forecast_period_start
        assert forecast.forecast_period_end == result.forecast_period_end


def test_forecast_generated_timestamp():
    """Test that forecast has a valid generated_at timestamp."""
    result = _get_materials_forecast(30)
    
    assert result.forecast_generated_at is not None
    assert result.forecast_generated_at <= datetime.now()
    # Should be generated recently (within last minute)
    assert (datetime.now() - result.forecast_generated_at).total_seconds() < 60


# ============================================================================
# BREAKDOWN VERIFICATION TESTS
# ============================================================================

def test_material_contribution_breakdown_mat001():
    """Verify MAT-001 contributions from each product."""
    # Expected contributions to MAT-001 based on BOM and product forecasts
    prod001_contrib = EXPECTED_PRODUCT_SALES_30_DAYS["PROD-001"] * BOM_REQUIREMENTS["PROD-001"]["MAT-001"]
    prod002_contrib = EXPECTED_PRODUCT_SALES_30_DAYS["PROD-002"] * BOM_REQUIREMENTS["PROD-002"]["MAT-001"]
    prod004_contrib = EXPECTED_PRODUCT_SALES_30_DAYS["PROD-004"] * BOM_REQUIREMENTS["PROD-004"]["MAT-001"]
    
    assert prod001_contrib == 250.0  # 100 * 2.5
    assert prod002_contrib == 120.0  # 40 * 3.0
    assert prod004_contrib == 194.0  # 97 * 2.0
    
    total_expected = prod001_contrib + prod002_contrib + prod004_contrib
    assert total_expected == 564.0


def test_material_contribution_breakdown_mat002():
    """Verify MAT-002 contributions from each product."""
    prod001_contrib = EXPECTED_PRODUCT_SALES_30_DAYS["PROD-001"] * BOM_REQUIREMENTS["PROD-001"]["MAT-002"]
    prod003_contrib = EXPECTED_PRODUCT_SALES_30_DAYS["PROD-003"] * BOM_REQUIREMENTS["PROD-003"]["MAT-002"]
    
    assert prod001_contrib == 100.0  # 100 * 1.0
    assert prod003_contrib == 90.0   # 20 * 4.5
    
    total_expected = prod001_contrib + prod003_contrib
    assert total_expected == 190.0


def test_all_quantities_positive():
    """Test that all forecasted quantities are positive."""
    result = _get_materials_forecast(30)
    
    for forecast in result.forecasts:
        assert forecast.forecasted_quantity > 0, \
            f"{forecast.material_id}: quantity should be positive, got {forecast.forecasted_quantity}"


def test_daily_demand_calculation():
    """Test daily demand calculation for each material."""
    result = _get_materials_forecast(30)
    
    for forecast in result.forecasts:
        expected_daily = EXPECTED_MATERIAL_QUANTITIES_30_DAYS[forecast.material_id] / 30
        actual_daily = forecast.forecasted_quantity / 30
        assert abs(actual_daily - expected_daily) < 0.01, \
            f"{forecast.material_id}: daily demand mismatch"

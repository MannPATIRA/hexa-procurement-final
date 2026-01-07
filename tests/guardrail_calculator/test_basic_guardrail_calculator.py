"""Test cases for BasicGuardrailCalculator with formula verification."""

from datetime import datetime
import sys
import os
# Add guardrail_calculator.py directory to path (conftest.py already adds src)
guardrail_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'guardrail_calculator.py')
sys.path.insert(0, guardrail_path)
from basic_guardrail_calculator import BasicGuardrailCalculator  # type: ignore
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.guardrails import GuardrailStore


# ============================================================================
# EXPECTED VALUES FROM MOCK DATA
# ============================================================================
# From materials forecast (30 days):
#   MAT-001: 564.0 units → daily = 18.8
#   MAT-002: 190.0 units → daily = 6.33
#   MAT-003: 225.5 units → daily = 7.52
#   MAT-004: 30.0 units → daily = 1.0
#
# Default lead time = 7 days
#
# Formulas:
#   safety_stock = int(daily_demand * lead_time * 1.5)
#   reorder_point = int(daily_demand * lead_time) + safety_stock
#   monthly_demand = daily_demand * 30
#   eoq = int(monthly_demand * 2.5), min 10
#   maximum_stock = reorder_point + eoq

DEFAULT_LEAD_TIME = 7.0
FORECAST_PERIOD_DAYS = 30

EXPECTED_MATERIAL_FORECASTS = {
    "MAT-001": 564.0,
    "MAT-002": 190.0,
    "MAT-003": 225.5,
    "MAT-004": 30.0,
}

def _calculate_expected_guardrails(forecasted_qty: float, lead_time: float = DEFAULT_LEAD_TIME) -> dict:
    """Calculate expected guardrail values using the same formulas as the calculator."""
    daily_demand = forecasted_qty / FORECAST_PERIOD_DAYS
    
    safety_stock = int(daily_demand * lead_time * 1.5)
    reorder_point = int(daily_demand * lead_time) + safety_stock
    monthly_demand = daily_demand * 30
    eoq = int(monthly_demand * 2.5)
    if eoq < 10:
        eoq = 10
    maximum_stock = reorder_point + eoq
    
    return {
        "daily_demand": daily_demand,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "eoq": eoq,
        "maximum_stock": maximum_stock,
    }


def _get_guardrail_store():
    """Helper to generate guardrail store from mock data."""
    calculator = BasicGuardrailCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    # Generate supplier state
    supplier_calculator = BasicSupplierStateCalculator()
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    supplier_state_store = supplier_calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    # Generate materials forecast
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    materials_lookup = erp_fetcher.get_materials_lookup()
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    materials_forecast = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    return calculator.calculate_guardrails(supplier_state_store, materials_forecast)


# ============================================================================
# BASIC TESTS
# ============================================================================

def test_calculate_guardrails_returns_guardrail_store():
    """Test that calculate_guardrails returns a GuardrailStore instance."""
    result = _get_guardrail_store()
    assert isinstance(result, GuardrailStore)


def test_calculate_guardrails_has_exactly_four_items():
    """Test that guardrail store contains exactly 4 items (one per material)."""
    result = _get_guardrail_store()
    assert len(result.items) == 4


def test_calculate_guardrails_has_correct_material_ids():
    """Test that guardrails contain correct material IDs."""
    result = _get_guardrail_store()
    
    material_ids = {g.material_id for g in result.items}
    expected_ids = {"MAT-001", "MAT-002", "MAT-003", "MAT-004"}
    assert material_ids == expected_ids


def test_calculate_guardrails_has_correct_timestamp():
    """Test that calculated_at timestamp is set correctly."""
    result = _get_guardrail_store()
    assert result.calculated_at <= datetime.now()


# ============================================================================
# FORMULA VERIFICATION TESTS
# ============================================================================

def test_guardrail_formula_mat001():
    """Test guardrail calculations for MAT-001 using exact formulas."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    mat001 = result.items_by_id.get("MAT-001")
    assert mat001 is not None
    
    expected = _calculate_expected_guardrails(EXPECTED_MATERIAL_FORECASTS["MAT-001"])
    
    # Verify safety stock: int(daily_demand * lead_time * 1.5)
    # MAT-001: int(18.8 * 7 * 1.5) = int(197.4) = 197
    assert mat001.safety_stock == expected["safety_stock"], \
        f"MAT-001 safety_stock: expected {expected['safety_stock']}, got {mat001.safety_stock}"
    
    # Verify reorder point: int(daily_demand * lead_time) + safety_stock
    # MAT-001: int(18.8 * 7) + 197 = 131 + 197 = 328
    assert mat001.reorder_point == expected["reorder_point"], \
        f"MAT-001 reorder_point: expected {expected['reorder_point']}, got {mat001.reorder_point}"
    
    # Verify EOQ: int(monthly_demand * 2.5)
    # MAT-001: int(564 * 2.5) = 1410
    assert mat001.eoq == expected["eoq"], \
        f"MAT-001 eoq: expected {expected['eoq']}, got {mat001.eoq}"
    
    # Verify maximum stock: reorder_point + eoq
    # MAT-001: 328 + 1410 = 1738
    assert mat001.maximum_stock == expected["maximum_stock"], \
        f"MAT-001 maximum_stock: expected {expected['maximum_stock']}, got {mat001.maximum_stock}"


def test_guardrail_formula_mat002():
    """Test guardrail calculations for MAT-002 using exact formulas."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    mat002 = result.items_by_id.get("MAT-002")
    assert mat002 is not None
    
    expected = _calculate_expected_guardrails(EXPECTED_MATERIAL_FORECASTS["MAT-002"])
    
    assert mat002.safety_stock == expected["safety_stock"]
    assert mat002.reorder_point == expected["reorder_point"]
    assert mat002.eoq == expected["eoq"]
    assert mat002.maximum_stock == expected["maximum_stock"]


def test_guardrail_formula_mat003():
    """Test guardrail calculations for MAT-003 using exact formulas."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    mat003 = result.items_by_id.get("MAT-003")
    assert mat003 is not None
    
    expected = _calculate_expected_guardrails(EXPECTED_MATERIAL_FORECASTS["MAT-003"])
    
    assert mat003.safety_stock == expected["safety_stock"]
    assert mat003.reorder_point == expected["reorder_point"]
    assert mat003.eoq == expected["eoq"]
    assert mat003.maximum_stock == expected["maximum_stock"]


def test_guardrail_formula_mat004():
    """Test guardrail calculations for MAT-004 using exact formulas."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    mat004 = result.items_by_id.get("MAT-004")
    assert mat004 is not None
    
    expected = _calculate_expected_guardrails(EXPECTED_MATERIAL_FORECASTS["MAT-004"])
    
    assert mat004.safety_stock == expected["safety_stock"]
    assert mat004.reorder_point == expected["reorder_point"]
    assert mat004.eoq == expected["eoq"]
    assert mat004.maximum_stock == expected["maximum_stock"]


def test_all_guardrails_exact_values():
    """Test exact guardrail values for all materials."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    for mat_id, forecast_qty in EXPECTED_MATERIAL_FORECASTS.items():
        expected = _calculate_expected_guardrails(forecast_qty)
        actual = result.items_by_id[mat_id]
        
        assert actual.safety_stock == expected["safety_stock"], \
            f"{mat_id}: safety_stock mismatch"
        assert actual.reorder_point == expected["reorder_point"], \
            f"{mat_id}: reorder_point mismatch"
        assert actual.eoq == expected["eoq"], \
            f"{mat_id}: eoq mismatch"
        assert actual.maximum_stock == expected["maximum_stock"], \
            f"{mat_id}: maximum_stock mismatch"


# ============================================================================
# CONSTRAINT VALIDATION TESTS
# ============================================================================

def test_calculate_guardrails_has_valid_values():
    """Test that guardrail items have valid calculated values."""
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        assert guardrail.reorder_point >= 0
        assert guardrail.safety_stock >= 0
        assert guardrail.maximum_stock >= 0
        assert guardrail.eoq >= 0
        # Reorder point should be >= safety stock
        assert guardrail.reorder_point >= guardrail.safety_stock
        # Maximum stock should be >= reorder point
        assert guardrail.maximum_stock >= guardrail.reorder_point


def test_safety_stock_formula():
    """Test safety stock formula: int(daily_demand * lead_time * 1.5)."""
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        forecast_qty = EXPECTED_MATERIAL_FORECASTS[guardrail.material_id]
        daily_demand = forecast_qty / FORECAST_PERIOD_DAYS
        expected_safety = int(daily_demand * DEFAULT_LEAD_TIME * 1.5)
        
        assert guardrail.safety_stock == expected_safety, \
            f"{guardrail.material_id}: expected safety_stock {expected_safety}, got {guardrail.safety_stock}"


def test_reorder_point_formula():
    """Test reorder point formula: int(daily_demand * lead_time) + safety_stock."""
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        forecast_qty = EXPECTED_MATERIAL_FORECASTS[guardrail.material_id]
        daily_demand = forecast_qty / FORECAST_PERIOD_DAYS
        expected_reorder = int(daily_demand * DEFAULT_LEAD_TIME) + guardrail.safety_stock
        
        assert guardrail.reorder_point == expected_reorder, \
            f"{guardrail.material_id}: expected reorder_point {expected_reorder}, got {guardrail.reorder_point}"


def test_eoq_formula():
    """Test EOQ formula: int(monthly_demand * 2.5), min 10."""
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        forecast_qty = EXPECTED_MATERIAL_FORECASTS[guardrail.material_id]
        daily_demand = forecast_qty / FORECAST_PERIOD_DAYS
        monthly_demand = daily_demand * 30
        expected_eoq = max(10, int(monthly_demand * 2.5))
        
        assert guardrail.eoq == expected_eoq, \
            f"{guardrail.material_id}: expected eoq {expected_eoq}, got {guardrail.eoq}"


def test_maximum_stock_formula():
    """Test maximum stock formula: reorder_point + eoq."""
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        expected_max = guardrail.reorder_point + guardrail.eoq
        
        assert guardrail.maximum_stock == expected_max, \
            f"{guardrail.material_id}: expected max_stock {expected_max}, got {guardrail.maximum_stock}"


def test_eoq_minimum_threshold():
    """Test that EOQ has minimum threshold of 10."""
    # MAT-004 has lowest demand (30 units/30 days = 1/day)
    # monthly = 30, eoq = int(30 * 2.5) = 75, which is > 10
    # So all our test data should have EOQ > 10
    result = _get_guardrail_store()
    
    for guardrail in result.items:
        assert guardrail.eoq >= 10, \
            f"{guardrail.material_id}: EOQ should be at least 10"


# ============================================================================
# MATERIAL METADATA TESTS
# ============================================================================

def test_guardrails_have_correct_material_names():
    """Test that guardrails have correct material names."""
    result = _get_guardrail_store()
    
    expected_names = {
        "MAT-001": "Steel Component",
        "MAT-002": "Plastic Housing",
        "MAT-003": "Electronic Circuit Board",
        "MAT-004": "Rubber Gasket",
    }
    
    for guardrail in result.items:
        expected_name = expected_names[guardrail.material_id]
        assert guardrail.material_name == expected_name, \
            f"{guardrail.material_id}: expected name '{expected_name}', got '{guardrail.material_name}'"


def test_guardrails_have_valid_period():
    """Test that guardrails have valid period matching materials forecast."""
    calculator = BasicGuardrailCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    supplier_calculator = BasicSupplierStateCalculator()
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    supplier_state_store = supplier_calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    materials_lookup = erp_fetcher.get_materials_lookup()
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    materials_forecast = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    for guardrail in result.items:
        assert guardrail.valid_period_start == materials_forecast.forecast_period_start
        assert guardrail.valid_period_end == materials_forecast.forecast_period_end


# ============================================================================
# PROPORTIONALITY TESTS
# ============================================================================

def test_guardrails_proportional_to_demand():
    """Test that guardrails are proportional to material demand."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    # MAT-001 has highest demand (564), should have highest guardrails
    # MAT-004 has lowest demand (30), should have lowest guardrails
    mat001 = result.items_by_id["MAT-001"]
    mat004 = result.items_by_id["MAT-004"]
    
    assert mat001.safety_stock > mat004.safety_stock
    assert mat001.reorder_point > mat004.reorder_point
    assert mat001.eoq > mat004.eoq
    assert mat001.maximum_stock > mat004.maximum_stock


def test_demand_to_guardrail_ratio():
    """Test that guardrail ratios match demand ratios approximately."""
    result = _get_guardrail_store()
    
    # Use items_by_id index for direct lookup
    # MAT-001 demand is 564/30 = 18.8 (ratio to MAT-004: ~18.8)
    # MAT-004 demand is 30/30 = 1.0
    demand_ratio = EXPECTED_MATERIAL_FORECASTS["MAT-001"] / EXPECTED_MATERIAL_FORECASTS["MAT-004"]
    
    # Safety stock ratio should be similar to demand ratio
    safety_ratio = result.items_by_id["MAT-001"].safety_stock / result.items_by_id["MAT-004"].safety_stock
    assert abs(safety_ratio - demand_ratio) < 1.0, \
        f"Safety stock ratio ({safety_ratio}) should be close to demand ratio ({demand_ratio})"

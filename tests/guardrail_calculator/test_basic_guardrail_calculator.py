"""Test cases for BasicGuardrailCalculator."""

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


def test_calculate_guardrails_returns_guardrail_store():
    """Test that calculate_guardrails returns a GuardrailStore instance."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    assert isinstance(result, GuardrailStore)


def test_calculate_guardrails_has_items():
    """Test that returned guardrail store contains guardrail items."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    assert len(result.items) > 0


def test_calculate_guardrails_has_correct_timestamp():
    """Test that calculated_at timestamp is set correctly."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    assert result.calculated_at <= datetime.now()


def test_calculate_guardrails_has_valid_values():
    """Test that guardrail items have valid calculated values."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    for guardrail in result.items:
        assert guardrail.reorder_point >= 0
        assert guardrail.safety_stock >= 0
        assert guardrail.maximum_stock >= 0
        assert guardrail.eoq >= 0
        # Reorder point should be >= safety stock
        assert guardrail.reorder_point >= guardrail.safety_stock
        # Maximum stock should be >= reorder point
        assert guardrail.maximum_stock >= guardrail.reorder_point


def test_calculate_guardrails_has_correct_period():
    """Test that guardrail valid period matches materials forecast period."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    # All guardrails should have same period as materials forecast
    for guardrail in result.items:
        assert guardrail.valid_period_start == materials_forecast.forecast_period_start
        assert guardrail.valid_period_end == materials_forecast.forecast_period_end


def test_calculate_guardrails_uses_lead_times():
    """Test that guardrails are calculated using default lead time for materials."""
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
    
    result = calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    # Find guardrail for MAT-001 (Steel Component)
    mat_001_guardrail = next((g for g in result.items if g.material_id == "MAT-001"), None)
    assert mat_001_guardrail is not None
    # Reorder point and safety stock should be > 0 if lead time is used
    assert mat_001_guardrail.reorder_point > 0
    assert mat_001_guardrail.safety_stock > 0
    # Verify material_name is set correctly
    assert mat_001_guardrail.material_name == "Steel Component"


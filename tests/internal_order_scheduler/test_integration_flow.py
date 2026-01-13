"""Integration tests for internal orders → materials → external orders flow."""

import sys
import os
from datetime import datetime, timedelta
from internal_order_scheduler.basic_internal_order_scheduler import BasicInternalOrderScheduler
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from order_scheduler.basic_order_scheduler import BasicOrderScheduler
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from models.inventory_data import ItemType, InventoryData

# Add guardrail_calculator.py directory to path
guardrail_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'guardrail_calculator.py')
sys.path.insert(0, guardrail_path)
from basic_guardrail_calculator import BasicGuardrailCalculator  # type: ignore


def test_internal_to_external_order_flow():
    """Test the complete flow: internal orders → materials forecast → external orders."""
    # Setup
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    # Step 1: Get data
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    bom_data = erp_fetcher.fetch_bom_data()
    
    # Step 2: Generate sales forecast
    sales_forecaster = BasicSalesForecaster()
    sales_forecast = sales_forecaster.forecast_sales(
        inventory_data, sales_data, forecast_period_days=30
    )
    
    # Step 3: Schedule internal orders
    product_inventory = InventoryData(
        items=[item for item in inventory_data.items if item.item_type == ItemType.PRODUCT],
        fetched_at=inventory_data.fetched_at,
    )
    
    # Access production info from mock_erp
    from erp_data_fetcher.mock_erp_fetcher import mock_erp
    production_info = mock_erp.product_production_store
    internal_scheduler = BasicInternalOrderScheduler()
    internal_schedule = internal_scheduler.schedule_internal_orders(
        sales_forecast, product_inventory, production_info, num_days=30
    )
    
    # Verify internal orders were created
    assert len(internal_schedule.orders) > 0, "Should have internal production orders"
    
    # Step 4: Generate materials forecast from internal orders
    materials_forecaster = BasicMaterialsForecaster(
        materials_lookup=erp_fetcher.get_materials_lookup()
    )
    materials_forecast = materials_forecaster.forecast_materials_from_internal_orders(
        internal_schedule, bom_data, forecast_period_days=30
    )
    
    # Verify materials forecast was created
    assert len(materials_forecast.forecasts) > 0, "Should have materials forecast"
    
    # Step 5: Calculate supplier state and guardrails
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    supplier_calculator = BasicSupplierStateCalculator()
    supplier_state_store = supplier_calculator.calculate_supplier_state(
        delivery_history, approved_suppliers, blanket_pos
    )
    
    guardrail_calculator = BasicGuardrailCalculator()
    guardrails = guardrail_calculator.calculate_guardrails(
        supplier_state_store, materials_forecast
    )
    
    # Step 6: Schedule external orders
    material_inventory = InventoryData(
        items=[item for item in inventory_data.items if item.item_type == ItemType.MATERIAL],
        fetched_at=inventory_data.fetched_at,
    )
    
    external_scheduler = BasicOrderScheduler()
    external_schedule = external_scheduler.schedule_orders(
        material_inventory, materials_forecast, supplier_state_store, guardrails, num_days=30
    )
    
    # Verify external orders were created (may be 0 if inventory is high)
    assert isinstance(external_schedule.orders, list), "Should return list of orders"
    
    # Verify the flow worked end-to-end
    assert len(internal_schedule.orders) > 0, "Should have internal production orders"
    assert len(materials_forecast.forecasts) > 0, "Should have materials forecast"


def test_materials_forecast_from_internal_orders():
    """Test that materials forecast from internal orders matches production schedule."""
    erp_fetcher = MockERPDataFetcher()
    bom_data = erp_fetcher.fetch_bom_data()
    
    # Create a simple internal order schedule
    from models.internal_order import InternalOrderSchedule, InternalOrder, InternalOrderStatus
    now = datetime.now()
    
    internal_schedule = InternalOrderSchedule(
        orders=[
            InternalOrder(
                product_id="PROD-001",
                product_name="Widget A",
                quantity=100,
                start_date=now,
                completion_date=now + timedelta(days=2),
                status=InternalOrderStatus.SCHEDULED,
            ),
        ],
        schedule_start_date=now,
        schedule_end_date=now + timedelta(days=30),
        generated_at=now,
    )
    
    # Generate materials forecast
    materials_forecaster = BasicMaterialsForecaster(
        materials_lookup=erp_fetcher.get_materials_lookup()
    )
    materials_forecast = materials_forecaster.forecast_materials_from_internal_orders(
        internal_schedule, bom_data, forecast_period_days=30
    )
    
    # PROD-001 uses MAT-001 (2.5 units) and MAT-002 (1.0 unit) according to BOM
    # So 100 units of PROD-001 should require:
    # - MAT-001: 100 * 2.5 = 250
    # - MAT-002: 100 * 1.0 = 100
    
    mat_001 = next((f for f in materials_forecast.forecasts if f.material_id == "MAT-001"), None)
    mat_002 = next((f for f in materials_forecast.forecasts if f.material_id == "MAT-002"), None)
    
    assert mat_001 is not None, "Should have MAT-001 forecast"
    assert mat_002 is not None, "Should have MAT-002 forecast"
    assert mat_001.forecasted_quantity == 250.0, f"Expected 250, got {mat_001.forecasted_quantity}"
    assert mat_002.forecasted_quantity == 100.0, f"Expected 100, got {mat_002.forecasted_quantity}"

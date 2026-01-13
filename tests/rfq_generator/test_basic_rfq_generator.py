"""Test cases for BasicRFQGenerator."""

from datetime import datetime, timedelta
from rfq_generator.basic_rfq_generator import BasicRFQGenerator
from web_scanner.mock_web_scanner import MockWebScanner
from order_scheduler.basic_order_scheduler import BasicOrderScheduler
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.rfq import RFQStore, RFQStatus
from models.inventory_data import InventoryData, InventoryItem, ItemType

import sys
import os
guardrail_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'guardrail_calculator.py')
sys.path.insert(0, guardrail_path)
from basic_guardrail_calculator import BasicGuardrailCalculator  # type: ignore


def _generate_test_data():
    """Helper to generate test data for RFQ generation."""
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    # Create material inventory
    now = datetime.now()
    inventory_data = InventoryData(
        items=[
            InventoryItem(
                item_id="MAT-001",
                item_name="Steel Component",
                item_type=ItemType.MATERIAL,
                quantity=10,
                unit_price=5.0,
                location="Warehouse-1",
                last_updated=now,
                supplier_id="SUP-001",
            ),
        ],
        fetched_at=now,
    )
    
    # Generate materials forecast
    sales_forecaster = BasicSalesForecaster()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(
        erp_fetcher.fetch_inventory_data(), sales_data, forecast_period_days=30
    )
    
    materials_lookup = erp_fetcher.get_materials_lookup()
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    materials_forecast = materials_forecaster.forecast_materials(
        sales_forecast, bom_data, forecast_period_days=30
    )
    
    # Generate supplier state
    supplier_calculator = BasicSupplierStateCalculator()
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos_data = crm_fetcher.fetch_blanket_pos()
    supplier_state_store = supplier_calculator.calculate_supplier_state(
        delivery_history, approved_suppliers, blanket_pos_data
    )
    
    # Generate guardrails
    guardrail_calculator = BasicGuardrailCalculator()
    guardrails = guardrail_calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    # Generate order schedule
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        inventory_data, materials_forecast, supplier_state_store, guardrails, num_days=30
    )
    
    # Get blanket POs from ERP
    blanket_pos = erp_fetcher.fetch_blanket_pos()
    
    # Search for suppliers
    web_scanner = MockWebScanner()
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    return order_schedule, blanket_pos, supplier_results


def test_generate_rfqs_returns_rfq_store():
    """Test that generate_rfqs returns an RFQStore instance."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    assert isinstance(result, RFQStore)


def test_generate_rfqs_has_rfqs():
    """Test that generated RFQStore contains RFQs."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    # Should have RFQs if we have orders and suppliers
    if len(order_schedule.orders) > 0 and len(supplier_results.results) > 0:
        assert len(result.rfqs) > 0


def test_generate_rfqs_one_per_supplier_material():
    """Test that one RFQ is generated per supplier per material."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    # Check for duplicates
    supplier_material_pairs = [(rfq.supplier_id, rfq.material_id) for rfq in result.rfqs]
    assert len(supplier_material_pairs) == len(set(supplier_material_pairs))


def test_generate_rfqs_has_correct_status():
    """Test that generated RFQs have DRAFT status."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.status == RFQStatus.DRAFT


def test_generate_rfqs_has_valid_until():
    """Test that generated RFQs have validity dates."""
    generator = BasicRFQGenerator(rfq_validity_days=14)
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.valid_until is not None
        assert rfq.valid_until > rfq.created_at


def test_generate_rfqs_has_supplier_info():
    """Test that RFQs contain correct supplier information."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.supplier_id
        assert rfq.supplier_name
        assert rfq.supplier_email
        assert "@" in rfq.supplier_email


def test_generate_rfqs_has_material_info():
    """Test that RFQs contain material information."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.material_id
        assert rfq.material_name
        assert rfq.quantity > 0


def test_generate_rfqs_has_delivery_date():
    """Test that RFQs have required delivery dates."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.required_delivery_date is not None


def test_generate_rfqs_has_terms():
    """Test that RFQs include terms and conditions."""
    generator = BasicRFQGenerator()
    order_schedule, blanket_pos, supplier_results = _generate_test_data()
    
    result = generator.generate_rfqs(order_schedule, blanket_pos, supplier_results)
    
    for rfq in result.rfqs:
        assert rfq.terms
        assert len(rfq.terms) > 0


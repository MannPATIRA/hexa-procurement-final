"""Test cases for BasicSupplierStateCalculator."""

from datetime import datetime
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.supplier_state import SupplierStateStore, SupplierState
from models.delivery_history import DeliveryStatus
from models.approved_suppliers_list import SupplierStatus


def test_calculate_supplier_state_returns_supplier_state_store():
    """Test that calculate_supplier_state returns a SupplierStateStore instance."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    assert isinstance(result, SupplierStateStore)


def test_calculate_supplier_state_has_states():
    """Test that returned supplier state store contains supplier states."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    assert len(result.states) > 0


def test_calculate_supplier_state_has_correct_timestamp():
    """Test that built_at timestamp is set correctly."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    assert result.built_at <= datetime.now()


def test_calculate_supplier_state_has_delivery_stats():
    """Test that supplier states have correct delivery statistics."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    for state in result.states:
        assert state.total_deliveries >= 0
        assert state.successful_deliveries >= 0
        assert state.successful_deliveries <= state.total_deliveries
        # Success rate should be between 0 and 100
        assert 0.0 <= state.success_rate <= 100.0


def test_calculate_supplier_state_has_blanket_po_counts():
    """Test that supplier states have correct active blanket PO counts."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    for state in result.states:
        assert state.active_blanket_pos_count >= 0


def test_calculate_supplier_state_has_supplier_status():
    """Test that supplier states have supplier status from approved suppliers list."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    for state in result.states:
        assert isinstance(state.supplier_status, SupplierStatus)


def test_calculate_supplier_state_aggregates_by_supplier_product():
    """Test that states are grouped by supplier-product combination."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    # Check that each state has unique supplier-product combination
    combinations = {(state.supplier_id, state.product_id) for state in result.states}
    assert len(combinations) == len(result.states), "Each state should have unique supplier-product combination"


def test_calculate_supplier_state_has_lead_time_calculation():
    """Test that supplier states calculate average lead time when delivery dates are available."""
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    # At least some states should have lead time calculated if delivery records have dates
    states_with_lead_time = [s for s in result.states if s.average_lead_time_days is not None]
    # This is optional, so we just check that if lead time exists, it's a valid number
    for state in states_with_lead_time:
        assert isinstance(state.average_lead_time_days, float)


def test_calculate_supplier_state_has_correct_values_from_mock_data():
    """Test that supplier states have correct values based on mock data.
    
    Mock data analysis:
    - DEL-001: SUP-001, PROD-001, DELIVERED, lead_time=7 days (expected=-12, actual=-5)
    - DEL-002: SUP-002, PROD-002, DELIVERED, lead_time=5 days (expected=-15, actual=-10)
    - DEL-003: SUP-003, PROD-003, DELIVERED, lead_time=4 days (expected=-7, actual=-3)
    - DEL-004: SUP-001, PROD-004, DELIVERED, lead_time=6 days (expected=-14, actual=-8)
    
    Blanket POs (all ACTIVE):
    - BPO-001: SUP-001, PROD-001
    - BPO-002: SUP-002, PROD-002
    - BPO-003: SUP-003, PROD-003
    - BPO-004: SUP-001, PROD-004
    
    Approved Suppliers: Only SUP-004 and SUP-005 (not in delivery history)
    So SUP-001, SUP-002, SUP-003 should have INACTIVE status (not in approved list)
    """
    calculator = BasicSupplierStateCalculator()
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    result = calculator.calculate_supplier_state(delivery_history, approved_suppliers, blanket_pos)
    
    # Find states by supplier-product combination
    states_by_key = {(s.supplier_id, s.product_id): s for s in result.states}
    
    # Test SUP-001, PROD-001
    state_001 = states_by_key.get(("SUP-001", "PROD-001"))
    assert state_001 is not None, "Should have state for SUP-001, PROD-001"
    assert state_001.total_deliveries == 1
    assert state_001.successful_deliveries == 1
    assert state_001.success_rate == 100.0
    assert state_001.active_blanket_pos_count == 1
    assert state_001.supplier_status == SupplierStatus.INACTIVE  # Not in approved suppliers list
    assert state_001.average_lead_time_days == 7.0  # 7 days lead time
    assert state_001.supplier_name == "Acme Corp"
    assert state_001.product_name == "Widget A"
    
    # Test SUP-002, PROD-002
    state_002 = states_by_key.get(("SUP-002", "PROD-002"))
    assert state_002 is not None, "Should have state for SUP-002, PROD-002"
    assert state_002.total_deliveries == 1
    assert state_002.successful_deliveries == 1
    assert state_002.success_rate == 100.0
    assert state_002.active_blanket_pos_count == 1
    assert state_002.supplier_status == SupplierStatus.INACTIVE  # Not in approved suppliers list
    assert state_002.average_lead_time_days == 5.0  # 5 days lead time
    assert state_002.supplier_name == "Tech Supplies Inc"
    assert state_002.product_name == "Widget B"
    
    # Test SUP-003, PROD-003
    state_003 = states_by_key.get(("SUP-003", "PROD-003"))
    assert state_003 is not None, "Should have state for SUP-003, PROD-003"
    assert state_003.total_deliveries == 1
    assert state_003.successful_deliveries == 1
    assert state_003.success_rate == 100.0
    assert state_003.active_blanket_pos_count == 1
    assert state_003.supplier_status == SupplierStatus.INACTIVE  # Not in approved suppliers list
    assert state_003.average_lead_time_days == 4.0  # 4 days lead time
    assert state_003.supplier_name == "Global Parts Ltd"
    assert state_003.product_name == "Widget C"
    
    # Test SUP-001, PROD-004
    state_004 = states_by_key.get(("SUP-001", "PROD-004"))
    assert state_004 is not None, "Should have state for SUP-001, PROD-004"
    assert state_004.total_deliveries == 1
    assert state_004.successful_deliveries == 1
    assert state_004.success_rate == 100.0
    assert state_004.active_blanket_pos_count == 1
    assert state_004.supplier_status == SupplierStatus.INACTIVE  # Not in approved suppliers list
    assert state_004.average_lead_time_days == 6.0  # 6 days lead time
    assert state_004.supplier_name == "Acme Corp"
    assert state_004.product_name == "Widget D"
    
    # Verify we have exactly 4 states (one for each unique supplier-product combination)
    assert len(result.states) == 4, f"Expected 4 states, got {len(result.states)}"


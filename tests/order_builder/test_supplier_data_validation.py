"""Quick validation test for test supplier data."""

import pytest
from tests.order_builder.test_supplier_data import (
    create_test_suppliers,
    create_test_supplier_states,
    create_test_quotes,
)


def test_suppliers_created():
    """Verify suppliers are created correctly."""
    suppliers = create_test_suppliers()
    assert len(suppliers.suppliers) == 10
    
    # Check complete data suppliers (have rating, phone, and notes)
    complete = [s for s in suppliers.suppliers 
                if s.rating is not None and s.contact_phone is not None and s.notes is not None]
    assert len(complete) >= 5, f"Expected at least 5 complete suppliers, got {len(complete)}"
    
    # Check incomplete data suppliers (missing at least one optional field)
    incomplete = [s for s in suppliers.suppliers 
                 if s.rating is None or s.contact_phone is None or s.notes is None]
    assert len(incomplete) >= 4, f"Expected at least 4 incomplete suppliers, got {len(incomplete)}"
    
    # Verify we have exactly 10 total
    assert len(complete) + len(incomplete) == 10


def test_supplier_states_created():
    """Verify supplier states are created correctly."""
    states = create_test_supplier_states()
    assert len(states.states) == 10
    
    # Check complete data states
    complete = [s for s in states.states 
                if s.average_lead_time_days is not None 
                and s.average_defect_rate is not None 
                and s.last_delivery_date is not None]
    assert len(complete) >= 5, f"Expected at least 5 complete states, got {len(complete)}"
    
    # Check incomplete data states
    incomplete = [s for s in states.states 
                 if s.average_lead_time_days is None 
                 or s.average_defect_rate is None 
                 or s.last_delivery_date is None]
    assert len(incomplete) >= 3, f"Expected at least 3 incomplete states, got {len(incomplete)}"


def test_quotes_created():
    """Verify quotes are created correctly."""
    quotes = create_test_quotes()
    assert len(quotes) == 8
    
    # Check quotes from complete data suppliers
    complete_supplier_ids = {"SUP-PREMIUM-001", "SUP-ESTABLISHED-002", 
                           "SUP-BUDGET-003", "SUP-SPECIALIZED-004"}
    complete_quotes = [q for q in quotes if q.supplier_id in complete_supplier_ids]
    assert len(complete_quotes) >= 4
    
    # Check quotes from incomplete data suppliers
    incomplete_supplier_ids = {"SUP-NEW-006", "SUP-EMERGING-007", 
                              "SUP-REGIONAL-008", "SUP-INTERNATIONAL-009"}
    incomplete_quotes = [q for q in quotes if q.supplier_id in incomplete_supplier_ids]
    assert len(incomplete_quotes) >= 4

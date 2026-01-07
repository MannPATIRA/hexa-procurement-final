"""Test cases for MockCRMDataFetcher with exact value verification."""

from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.blanket_pos import BlanketPOs, BlanketPOStatus
from models.approved_suppliers_list import ApprovedSuppliersList, SupplierStatus


# ============================================================================
# BLANKET POS TESTS
# ============================================================================

def test_fetch_blanket_pos_returns_blanket_pos():
    """Test that fetch_blanket_pos returns a BlanketPOs instance."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert isinstance(result, BlanketPOs)


def test_fetch_blanket_pos_has_exactly_four_records():
    """Test that CRM blanket POs contains exactly 4 records."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert len(result.blanket_pos) == 4


def test_fetch_blanket_pos_all_active_status():
    """Test that all CRM blanket POs have ACTIVE status."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    for bpo in result.blanket_pos:
        assert bpo.status == BlanketPOStatus.ACTIVE, \
            f"BPO {bpo.blanket_po_id} expected ACTIVE, got {bpo.status}"


def test_fetch_blanket_pos_exact_ids():
    """Test that CRM blanket POs have correct IDs."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    bpo_ids = {bpo.blanket_po_id for bpo in result.blanket_pos}
    expected_ids = {"BPO-001", "BPO-002", "BPO-003", "BPO-004"}
    assert bpo_ids == expected_ids


def test_fetch_blanket_pos_supplier_mapping():
    """Test that blanket POs map to correct suppliers."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    bpo_map = {bpo.blanket_po_id: bpo for bpo in result.blanket_pos}
    
    # BPO-001: SUP-001 (Acme Corp) for PROD-001
    assert bpo_map["BPO-001"].supplier_id == "SUP-001"
    assert bpo_map["BPO-001"].supplier_name == "Acme Corp"
    assert bpo_map["BPO-001"].product_id == "PROD-001"
    
    # BPO-002: SUP-002 (Tech Supplies Inc) for PROD-002
    assert bpo_map["BPO-002"].supplier_id == "SUP-002"
    assert bpo_map["BPO-002"].supplier_name == "Tech Supplies Inc"
    assert bpo_map["BPO-002"].product_id == "PROD-002"
    
    # BPO-003: SUP-003 (Global Parts Ltd) for PROD-003
    assert bpo_map["BPO-003"].supplier_id == "SUP-003"
    assert bpo_map["BPO-003"].supplier_name == "Global Parts Ltd"
    assert bpo_map["BPO-003"].product_id == "PROD-003"
    
    # BPO-004: SUP-001 (Acme Corp) for PROD-004
    assert bpo_map["BPO-004"].supplier_id == "SUP-001"
    assert bpo_map["BPO-004"].supplier_name == "Acme Corp"
    assert bpo_map["BPO-004"].product_id == "PROD-004"


def test_fetch_blanket_pos_exact_unit_prices():
    """Test that CRM blanket POs have correct unit prices."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    price_map = {bpo.blanket_po_id: bpo.unit_price for bpo in result.blanket_pos}
    
    assert price_map["BPO-001"] == 25.50
    assert price_map["BPO-002"] == 45.00
    assert price_map["BPO-003"] == 75.00
    assert price_map["BPO-004"] == 35.00


def test_fetch_blanket_pos_exact_total_quantities():
    """Test that blanket POs have correct total quantities."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    qty_map = {bpo.blanket_po_id: bpo.total_quantity for bpo in result.blanket_pos}
    
    assert qty_map["BPO-001"] == 1000
    assert qty_map["BPO-002"] == 500
    assert qty_map["BPO-003"] == 800
    assert qty_map["BPO-004"] == 600


def test_fetch_blanket_pos_exact_remaining_quantities():
    """Test that blanket POs have correct remaining quantities."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    remaining_map = {bpo.blanket_po_id: bpo.remaining_quantity for bpo in result.blanket_pos}
    
    assert remaining_map["BPO-001"] == 750
    assert remaining_map["BPO-002"] == 450
    assert remaining_map["BPO-003"] == 600
    assert remaining_map["BPO-004"] == 500


def test_fetch_blanket_pos_terms_contain_payment_info():
    """Test that blanket PO terms contain payment information."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    for bpo in result.blanket_pos:
        assert bpo.terms is not None
        assert "Net" in bpo.terms, f"BPO {bpo.blanket_po_id} terms should contain 'Net'"
        assert "FOB" in bpo.terms, f"BPO {bpo.blanket_po_id} terms should contain 'FOB'"


def test_fetch_blanket_pos_acme_corp_has_two_bpos():
    """Test that Acme Corp (SUP-001) has exactly 2 blanket POs."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    acme_bpos = [bpo for bpo in result.blanket_pos if bpo.supplier_id == "SUP-001"]
    assert len(acme_bpos) == 2
    
    # Verify the products covered
    acme_products = {bpo.product_id for bpo in acme_bpos}
    assert acme_products == {"PROD-001", "PROD-004"}


# ============================================================================
# APPROVED SUPPLIERS TESTS
# ============================================================================

def test_fetch_approved_suppliers_returns_approved_suppliers_list():
    """Test that fetch_approved_suppliers returns an ApprovedSuppliersList instance."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    assert isinstance(result, ApprovedSuppliersList)


def test_fetch_approved_suppliers_has_exactly_two_suppliers():
    """Test that approved suppliers list contains exactly 2 suppliers."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    assert len(result.suppliers) == 2


def test_fetch_approved_suppliers_exact_ids():
    """Test that approved suppliers have correct IDs."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    supplier_ids = {s.supplier_id for s in result.suppliers}
    expected_ids = {"SUP-004", "SUP-005"}
    assert supplier_ids == expected_ids


def test_fetch_approved_suppliers_all_pending_status():
    """Test that all approved suppliers have PENDING_APPROVAL status."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    for supplier in result.suppliers:
        assert supplier.status == SupplierStatus.PENDING_APPROVAL, \
            f"Supplier {supplier.supplier_id} expected PENDING_APPROVAL, got {supplier.status}"


def test_fetch_approved_suppliers_exact_names():
    """Test that approved suppliers have correct names."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    name_map = {s.supplier_id: s.supplier_name for s in result.suppliers}
    
    assert name_map["SUP-004"] == "Premium Parts Co"
    assert name_map["SUP-005"] == "Fast Logistics Inc"


def test_fetch_approved_suppliers_have_contact_info():
    """Test that approved suppliers have valid contact information."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    for supplier in result.suppliers:
        assert supplier.contact_email is not None
        assert "@" in supplier.contact_email
        assert supplier.contact_phone is not None
        assert supplier.contact_phone.startswith("+1-555-")


def test_fetch_approved_suppliers_exact_contact_emails():
    """Test that approved suppliers have correct contact emails."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    email_map = {s.supplier_id: s.contact_email for s in result.suppliers}
    
    assert email_map["SUP-004"] == "sales@premiumparts.com"
    assert email_map["SUP-005"] == "orders@fastlogistics.com"


def test_fetch_approved_suppliers_have_ratings():
    """Test that approved suppliers have ratings in valid range."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    for supplier in result.suppliers:
        assert supplier.rating is not None
        assert 0.0 <= supplier.rating <= 5.0


def test_fetch_approved_suppliers_exact_ratings():
    """Test that approved suppliers have correct ratings."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    rating_map = {s.supplier_id: s.rating for s in result.suppliers}
    
    assert rating_map["SUP-004"] == 4.6
    assert rating_map["SUP-005"] == 4.3


def test_fetch_approved_suppliers_have_categories():
    """Test that approved suppliers have category assignments."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    for supplier in result.suppliers:
        assert supplier.categories is not None
        assert len(supplier.categories) >= 1
        assert "Electronics" in supplier.categories


def test_fetch_approved_suppliers_have_notes():
    """Test that approved suppliers have notes."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    for supplier in result.suppliers:
        assert supplier.notes is not None
        assert len(supplier.notes) > 0


def test_fetch_approved_suppliers_source_is_crm():
    """Test that approved suppliers list source is CRM."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    
    assert result.source == "CRM"

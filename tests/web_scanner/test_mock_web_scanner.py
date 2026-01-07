"""Test cases for MockWebScanner with exact value verification."""

from datetime import datetime
from web_scanner.mock_web_scanner import MockWebScanner
from models.supplier_search import SupplierSearchStore, SupplierSearchResult


# ============================================================================
# EXPECTED VALUES FROM MOCK DATA
# ============================================================================
# From mock_web_scanner.py:
# MAT-001: 3 suppliers (WEB-SUP-001, WEB-SUP-002, WEB-SUP-003)
# MAT-002: 2 suppliers (WEB-SUP-004, WEB-SUP-005)
# MAT-003: 2 suppliers (WEB-SUP-006, WEB-SUP-007)
# MAT-004: 2 suppliers (WEB-SUP-008, WEB-SUP-009)

EXPECTED_SUPPLIER_COUNTS = {
    "MAT-001": 3,
    "MAT-002": 2,
    "MAT-003": 2,
    "MAT-004": 2,
}

EXPECTED_SUPPLIER_IDS = {
    "MAT-001": ["WEB-SUP-001", "WEB-SUP-002", "WEB-SUP-003"],
    "MAT-002": ["WEB-SUP-004", "WEB-SUP-005"],
    "MAT-003": ["WEB-SUP-006", "WEB-SUP-007"],
    "MAT-004": ["WEB-SUP-008", "WEB-SUP-009"],
}

EXPECTED_SUPPLIER_DETAILS = {
    "WEB-SUP-001": {
        "name": "Global Steel Industries",
        "email": "sales@globalsteel.mock",
        "price_range": (4.50, 6.00),
        "lead_time": 5,
        "rating": 4.5,
        "certifications": ["ISO 9001", "ISO 14001"],
    },
    "WEB-SUP-004": {
        "name": "PlastiCorp International",
        "email": "rfq@plasticorp.mock",
        "price_range": (2.00, 4.00),
        "lead_time": 10,
        "rating": 4.3,
        "certifications": ["ISO 9001", "RoHS Compliant"],
    },
    "WEB-SUP-006": {
        "name": "CircuitPro Electronics",
        "email": "quotes@circuitpro.mock",
        "price_range": (8.00, 15.00),
        "lead_time": 14,
        "rating": 4.7,
        "certifications": ["ISO 9001", "IPC-A-610", "UL Listed"],
    },
    "WEB-SUP-008": {
        "name": "RubberSeal Corp",
        "email": "sales@rubberseal.mock",
        "price_range": (0.50, 2.00),
        "lead_time": 6,
        "rating": 4.1,
        "certifications": ["ISO 9001", "FDA Compliant"],
    },
}


# ============================================================================
# BASIC TESTS
# ============================================================================

def test_search_suppliers_returns_supplier_search_store():
    """Test that search_suppliers returns a SupplierSearchStore instance."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    assert isinstance(result, SupplierSearchStore)


def test_search_suppliers_has_results():
    """Test that search returns results for known materials."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    assert len(result.results) > 0


def test_search_suppliers_has_correct_structure():
    """Test that search results have correct structure."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    for supplier in result.results:
        assert isinstance(supplier, SupplierSearchResult)
        assert supplier.supplier_id
        assert supplier.name
        assert supplier.contact_email
        assert "@" in supplier.contact_email
        assert supplier.materials_offered
        assert len(supplier.estimated_price_range) == 2


# ============================================================================
# EXACT COUNT TESTS
# ============================================================================

def test_mat001_returns_exactly_three_suppliers():
    """Test that MAT-001 search returns exactly 3 suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    assert len(result.results) == EXPECTED_SUPPLIER_COUNTS["MAT-001"]


def test_mat002_returns_exactly_two_suppliers():
    """Test that MAT-002 search returns exactly 2 suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-002"], ["Plastic Housing"])
    assert len(result.results) == EXPECTED_SUPPLIER_COUNTS["MAT-002"]


def test_mat003_returns_exactly_two_suppliers():
    """Test that MAT-003 search returns exactly 2 suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-003"], ["Electronic Circuit Board"])
    assert len(result.results) == EXPECTED_SUPPLIER_COUNTS["MAT-003"]


def test_mat004_returns_exactly_two_suppliers():
    """Test that MAT-004 search returns exactly 2 suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-004"], ["Rubber Gasket"])
    assert len(result.results) == EXPECTED_SUPPLIER_COUNTS["MAT-004"]


def test_all_materials_returns_nine_suppliers():
    """Test that searching all materials returns exactly 9 unique suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    assert len(result.results) == 9


# ============================================================================
# EXACT SUPPLIER ID TESTS
# ============================================================================

def test_mat001_returns_correct_supplier_ids():
    """Test that MAT-001 returns the correct supplier IDs."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    supplier_ids = {s.supplier_id for s in result.results}
    expected_ids = set(EXPECTED_SUPPLIER_IDS["MAT-001"])
    assert supplier_ids == expected_ids


def test_mat002_returns_correct_supplier_ids():
    """Test that MAT-002 returns the correct supplier IDs."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-002"], ["Plastic Housing"])
    
    supplier_ids = {s.supplier_id for s in result.results}
    expected_ids = set(EXPECTED_SUPPLIER_IDS["MAT-002"])
    assert supplier_ids == expected_ids


def test_mat003_returns_correct_supplier_ids():
    """Test that MAT-003 returns the correct supplier IDs."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-003"], ["Electronic Circuit Board"])
    
    supplier_ids = {s.supplier_id for s in result.results}
    expected_ids = set(EXPECTED_SUPPLIER_IDS["MAT-003"])
    assert supplier_ids == expected_ids


def test_mat004_returns_correct_supplier_ids():
    """Test that MAT-004 returns the correct supplier IDs."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-004"], ["Rubber Gasket"])
    
    supplier_ids = {s.supplier_id for s in result.results}
    expected_ids = set(EXPECTED_SUPPLIER_IDS["MAT-004"])
    assert supplier_ids == expected_ids


# ============================================================================
# EXACT SUPPLIER DETAIL TESTS
# ============================================================================

def test_web_sup_001_exact_details():
    """Test WEB-SUP-001 has correct exact details."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    sup = next((s for s in result.results if s.supplier_id == "WEB-SUP-001"), None)
    assert sup is not None
    
    expected = EXPECTED_SUPPLIER_DETAILS["WEB-SUP-001"]
    assert sup.name == expected["name"]
    assert sup.contact_email == expected["email"]
    assert sup.estimated_price_range == expected["price_range"]
    assert sup.estimated_lead_time_days == expected["lead_time"]
    assert sup.rating == expected["rating"]
    assert set(sup.certifications) == set(expected["certifications"])


def test_web_sup_004_exact_details():
    """Test WEB-SUP-004 has correct exact details."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-002"], ["Plastic Housing"])
    
    sup = next((s for s in result.results if s.supplier_id == "WEB-SUP-004"), None)
    assert sup is not None
    
    expected = EXPECTED_SUPPLIER_DETAILS["WEB-SUP-004"]
    assert sup.name == expected["name"]
    assert sup.contact_email == expected["email"]
    assert sup.estimated_price_range == expected["price_range"]
    assert sup.estimated_lead_time_days == expected["lead_time"]
    assert sup.rating == expected["rating"]
    assert set(sup.certifications) == set(expected["certifications"])


def test_web_sup_006_exact_details():
    """Test WEB-SUP-006 has correct exact details."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-003"], ["Electronic Circuit Board"])
    
    sup = next((s for s in result.results if s.supplier_id == "WEB-SUP-006"), None)
    assert sup is not None
    
    expected = EXPECTED_SUPPLIER_DETAILS["WEB-SUP-006"]
    assert sup.name == expected["name"]
    assert sup.contact_email == expected["email"]
    assert sup.estimated_price_range == expected["price_range"]
    assert sup.estimated_lead_time_days == expected["lead_time"]
    assert sup.rating == expected["rating"]
    assert set(sup.certifications) == set(expected["certifications"])


def test_web_sup_008_exact_details():
    """Test WEB-SUP-008 has correct exact details."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-004"], ["Rubber Gasket"])
    
    sup = next((s for s in result.results if s.supplier_id == "WEB-SUP-008"), None)
    assert sup is not None
    
    expected = EXPECTED_SUPPLIER_DETAILS["WEB-SUP-008"]
    assert sup.name == expected["name"]
    assert sup.contact_email == expected["email"]
    assert sup.estimated_price_range == expected["price_range"]
    assert sup.estimated_lead_time_days == expected["lead_time"]
    assert sup.rating == expected["rating"]
    assert set(sup.certifications) == set(expected["certifications"])


# ============================================================================
# NO DUPLICATE TESTS
# ============================================================================

def test_search_suppliers_no_duplicates():
    """Test that search results don't contain duplicate suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    supplier_ids = [s.supplier_id for s in result.results]
    assert len(supplier_ids) == len(set(supplier_ids))


def test_search_same_material_twice_no_duplicates():
    """Test that searching same material twice doesn't create duplicates."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-001"],  # Same material twice
        ["Steel", "Steel Component"]
    )
    
    supplier_ids = [s.supplier_id for s in result.results]
    assert len(supplier_ids) == len(set(supplier_ids))
    assert len(supplier_ids) == 3  # Should still be 3 suppliers


# ============================================================================
# METADATA TESTS
# ============================================================================

def test_search_suppliers_has_timestamp():
    """Test that search results have a timestamp."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    assert result.searched_at is not None
    assert result.searched_at <= datetime.now()


def test_search_suppliers_has_search_query():
    """Test that search results include the search query."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    assert result.search_query is not None
    assert "Steel Component" in result.search_query


def test_search_suppliers_query_contains_all_materials():
    """Test that search query contains all searched material names."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002"],
        ["Steel Component", "Plastic Housing"]
    )
    
    assert "Steel Component" in result.search_query
    assert "Plastic Housing" in result.search_query


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_search_suppliers_unknown_material():
    """Test searching for unknown material returns empty results."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["UNKNOWN-999"], ["Unknown Material"])
    
    assert len(result.results) == 0


def test_search_suppliers_empty_input():
    """Test searching with empty input returns empty results."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers([], [])
    
    assert len(result.results) == 0


def test_search_suppliers_mixed_known_unknown():
    """Test searching with mix of known and unknown materials."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "UNKNOWN-999"],
        ["Steel Component", "Unknown Material"]
    )
    
    # Should return suppliers for known material only
    assert len(result.results) == 3  # MAT-001 suppliers only


# ============================================================================
# PRICE AND LEAD TIME VERIFICATION
# ============================================================================

def test_price_range_is_valid():
    """Test that all price ranges have min <= max."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    for supplier in result.results:
        min_price, max_price = supplier.estimated_price_range
        assert min_price <= max_price, \
            f"{supplier.supplier_id}: min price {min_price} > max price {max_price}"


def test_lead_times_positive():
    """Test that all lead times are positive."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    for supplier in result.results:
        assert supplier.estimated_lead_time_days > 0, \
            f"{supplier.supplier_id}: lead time should be positive"


def test_ratings_in_valid_range():
    """Test that all ratings are in valid range [0, 5]."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    for supplier in result.results:
        if supplier.rating is not None:
            assert 0.0 <= supplier.rating <= 5.0, \
                f"{supplier.supplier_id}: rating {supplier.rating} out of range"


def test_all_suppliers_have_iso9001():
    """Test that all mock suppliers have ISO 9001 certification."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    for supplier in result.results:
        assert "ISO 9001" in supplier.certifications, \
            f"{supplier.supplier_id}: should have ISO 9001 certification"

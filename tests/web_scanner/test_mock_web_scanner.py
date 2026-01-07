"""Test cases for MockWebScanner."""

from datetime import datetime
from web_scanner.mock_web_scanner import MockWebScanner
from models.supplier_search import SupplierSearchStore, SupplierSearchResult


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


def test_search_suppliers_multiple_materials():
    """Test searching for multiple materials."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002"],
        ["Steel Component", "Plastic Housing"]
    )
    
    # Should have suppliers for both materials
    assert len(result.results) > 3


def test_search_suppliers_no_duplicates():
    """Test that search results don't contain duplicate suppliers."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(
        ["MAT-001", "MAT-002", "MAT-003", "MAT-004"],
        ["Steel", "Plastic", "Electronics", "Rubber"]
    )
    
    supplier_ids = [s.supplier_id for s in result.results]
    assert len(supplier_ids) == len(set(supplier_ids))


def test_search_suppliers_has_timestamp():
    """Test that search results have a timestamp."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    assert result.searched_at is not None
    assert result.searched_at <= datetime.now()


def test_search_suppliers_unknown_material():
    """Test searching for unknown material returns empty results."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["UNKNOWN-999"], ["Unknown Material"])
    
    assert len(result.results) == 0


def test_search_suppliers_has_search_query():
    """Test that search results include the search query."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    assert result.search_query is not None
    assert "Steel Component" in result.search_query


def test_supplier_has_certifications():
    """Test that suppliers have certification information."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    # At least one supplier should have certifications
    has_certs = any(len(s.certifications) > 0 for s in result.results)
    assert has_certs


def test_supplier_has_rating():
    """Test that suppliers have rating information."""
    scanner = MockWebScanner()
    result = scanner.search_suppliers(["MAT-001"], ["Steel Component"])
    
    for supplier in result.results:
        if supplier.rating is not None:
            assert 0.0 <= supplier.rating <= 5.0


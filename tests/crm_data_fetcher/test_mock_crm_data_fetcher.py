"""Test cases for MockCRMDataFetcher."""

from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.blanket_pos import BlanketPOs
from models.approved_suppliers_list import ApprovedSuppliersList


def test_fetch_blanket_pos_returns_blanket_pos():
    """Test that fetch_blanket_pos returns a BlanketPOs instance."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert isinstance(result, BlanketPOs)


def test_fetch_blanket_pos_has_blanket_pos():
    """Test that returned blanket POs contain blanket purchase orders."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert len(result.blanket_pos) > 0


def test_fetch_approved_suppliers_returns_approved_suppliers_list():
    """Test that fetch_approved_suppliers returns an ApprovedSuppliersList instance."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    assert isinstance(result, ApprovedSuppliersList)


def test_fetch_approved_suppliers_has_suppliers():
    """Test that returned approved suppliers list contains suppliers."""
    fetcher = MockCRMDataFetcher()
    result = fetcher.fetch_approved_suppliers()
    assert len(result.suppliers) > 0


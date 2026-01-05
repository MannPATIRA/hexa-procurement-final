"""Test cases for MockERPDataFetcher."""

from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.inventory_data import InventoryData
from models.delivery_history import DeliveryHistory
from models.sales_data import SalesData
from models.bom import BOMData
from models.blanket_pos import BlanketPOs


def test_fetch_inventory_data_returns_inventory_data():
    """Test that fetch_inventory_data returns an InventoryData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    assert isinstance(result, InventoryData)


def test_fetch_inventory_data_has_items():
    """Test that returned inventory data contains items."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    assert len(result.items) > 0


def test_fetch_delivery_history_returns_delivery_history():
    """Test that fetch_delivery_history returns a DeliveryHistory instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    assert isinstance(result, DeliveryHistory)


def test_fetch_delivery_history_has_records():
    """Test that returned delivery history contains records."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    assert len(result.records) > 0


def test_fetch_sales_data_returns_sales_data():
    """Test that fetch_sales_data returns a SalesData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    assert isinstance(result, SalesData)


def test_fetch_sales_data_has_records():
    """Test that returned sales data contains records."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    assert len(result.records) > 0


def test_fetch_bom_data_returns_bom_data():
    """Test that fetch_bom_data returns a BOMData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    assert isinstance(result, BOMData)


def test_fetch_bom_data_has_items():
    """Test that returned BOM data contains items."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    assert len(result.items) > 0


def test_fetch_blanket_pos_returns_blanket_pos():
    """Test that fetch_blanket_pos returns a BlanketPOs instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert isinstance(result, BlanketPOs)


def test_fetch_blanket_pos_has_blanket_pos():
    """Test that returned blanket POs contain blanket purchase orders."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert len(result.blanket_pos) > 0

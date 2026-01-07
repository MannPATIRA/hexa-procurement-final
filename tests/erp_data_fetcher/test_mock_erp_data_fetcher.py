"""Test cases for MockERPDataFetcher with exact value verification."""

from datetime import datetime, timedelta
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from models.inventory_data import InventoryData
from models.delivery_history import DeliveryHistory, DeliveryStatus
from models.sales_data import SalesData
from models.bom import BOMData
from models.blanket_pos import BlanketPOs, BlanketPOStatus


# ============================================================================
# INVENTORY DATA TESTS
# ============================================================================

def test_fetch_inventory_data_returns_inventory_data():
    """Test that fetch_inventory_data returns an InventoryData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    assert isinstance(result, InventoryData)


def test_fetch_inventory_data_has_exactly_four_items():
    """Test that inventory contains exactly 4 products (PROD-001 to PROD-004)."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    assert len(result.items) == 4


def test_fetch_inventory_data_exact_product_ids():
    """Test that inventory contains specific product IDs."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    product_ids = {item.item_id for item in result.items}
    expected_ids = {"PROD-001", "PROD-002", "PROD-003", "PROD-004"}
    assert product_ids == expected_ids


def test_fetch_inventory_data_exact_quantities():
    """Test that inventory items have correct quantities."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    
    # Use items_by_id index for direct lookup
    assert result.items_by_id["PROD-001"].quantity == 30
    assert result.items_by_id["PROD-002"].quantity == 200
    assert result.items_by_id["PROD-003"].quantity == 3
    assert result.items_by_id["PROD-004"].quantity == 150


def test_fetch_inventory_data_exact_prices():
    """Test that inventory items have correct unit prices."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    
    # Use items_by_id index for direct lookup
    assert result.items_by_id["PROD-001"].unit_price == 25.50
    assert result.items_by_id["PROD-002"].unit_price == 45.00
    assert result.items_by_id["PROD-003"].unit_price == 75.00
    assert result.items_by_id["PROD-004"].unit_price == 35.00


def test_fetch_inventory_data_exact_product_names():
    """Test that inventory items have correct product names."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    
    # Use items_by_id index for direct lookup
    assert result.items_by_id["PROD-001"].item_name == "Widget A"
    assert result.items_by_id["PROD-002"].item_name == "Widget B"
    assert result.items_by_id["PROD-003"].item_name == "Widget C"
    assert result.items_by_id["PROD-004"].item_name == "Widget D"


def test_fetch_inventory_data_supplier_assignments():
    """Test that inventory items are assigned to correct suppliers."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_inventory_data()
    
    # Use items_by_id index for direct lookup
    assert result.items_by_id["PROD-001"].supplier_id == "SUP-001"  # Acme Corp
    assert result.items_by_id["PROD-002"].supplier_id == "SUP-002"  # Tech Supplies Inc
    assert result.items_by_id["PROD-003"].supplier_id == "SUP-003"  # Global Parts Ltd
    assert result.items_by_id["PROD-004"].supplier_id == "SUP-001"  # Acme Corp (same as PROD-001)


# ============================================================================
# DELIVERY HISTORY TESTS
# ============================================================================

def test_fetch_delivery_history_returns_delivery_history():
    """Test that fetch_delivery_history returns a DeliveryHistory instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    assert isinstance(result, DeliveryHistory)


def test_fetch_delivery_history_has_exactly_four_records():
    """Test that delivery history contains exactly 4 records."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    assert len(result.records) == 4


def test_fetch_delivery_history_exact_delivery_ids():
    """Test that delivery history contains specific delivery IDs."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    
    delivery_ids = {record.delivery_id for record in result.records}
    expected_ids = {"DEL-001", "DEL-002", "DEL-003", "DEL-004"}
    assert delivery_ids == expected_ids


def test_fetch_delivery_history_all_delivered_status():
    """Test that all delivery records have DELIVERED status."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    
    for record in result.records:
        assert record.status == DeliveryStatus.DELIVERED


def test_fetch_delivery_history_supplier_product_mapping():
    """Test that deliveries map to correct supplier-product combinations."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    
    # Use records_by_id index for direct lookup
    # DEL-001: SUP-001 delivers PROD-001
    assert result.records_by_id["DEL-001"].supplier_id == "SUP-001"
    assert result.records_by_id["DEL-001"].product_id == "PROD-001"
    assert result.records_by_id["DEL-001"].supplier_name == "Acme Corp"
    
    # DEL-002: SUP-002 delivers PROD-002
    assert result.records_by_id["DEL-002"].supplier_id == "SUP-002"
    assert result.records_by_id["DEL-002"].product_id == "PROD-002"
    assert result.records_by_id["DEL-002"].supplier_name == "Tech Supplies Inc"
    
    # DEL-003: SUP-003 delivers PROD-003
    assert result.records_by_id["DEL-003"].supplier_id == "SUP-003"
    assert result.records_by_id["DEL-003"].product_id == "PROD-003"
    assert result.records_by_id["DEL-003"].supplier_name == "Global Parts Ltd"
    
    # DEL-004: SUP-001 delivers PROD-004
    assert result.records_by_id["DEL-004"].supplier_id == "SUP-001"
    assert result.records_by_id["DEL-004"].product_id == "PROD-004"
    assert result.records_by_id["DEL-004"].supplier_name == "Acme Corp"


def test_fetch_delivery_history_exact_quantities():
    """Test that delivery records have correct quantities."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    
    # Use records_by_id index for direct lookup
    assert result.records_by_id["DEL-001"].quantity == 100
    assert result.records_by_id["DEL-002"].quantity == 50
    assert result.records_by_id["DEL-003"].quantity == 200
    assert result.records_by_id["DEL-004"].quantity == 150


def test_fetch_delivery_history_lead_time_calculation():
    """Test that lead times can be calculated from expected vs actual delivery dates."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_delivery_history()
    
    # Expected lead times from mock_erp.py comments:
    # DEL-001: 7 days (expected -12, actual -5)
    # DEL-002: 5 days (expected -15, actual -10)
    # DEL-003: 4 days (expected -7, actual -3)
    # DEL-004: 6 days (expected -14, actual -8)
    expected_lead_times = {
        "DEL-001": 7,
        "DEL-002": 5,
        "DEL-003": 4,
        "DEL-004": 6,
    }
    
    for record in result.records:
        if record.expected_delivery_date and record.actual_delivery_date:
            # Lead time = actual_delivery_date - expected_delivery_date
            lead_time = abs((record.actual_delivery_date - record.expected_delivery_date).days)
            expected = expected_lead_times.get(record.delivery_id)
            assert lead_time == expected, \
                f"Lead time for {record.delivery_id}: expected {expected}, got {lead_time}"


# ============================================================================
# SALES DATA TESTS
# ============================================================================

def test_fetch_sales_data_returns_sales_data():
    """Test that fetch_sales_data returns a SalesData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    assert isinstance(result, SalesData)


def test_fetch_sales_data_has_exactly_eighteen_records():
    """Test that sales data contains exactly 18 records."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    # PROD-001: 5 sales, PROD-002: 4 sales, PROD-003: 4 sales, PROD-004: 5 sales = 18
    assert len(result.records) == 18


def test_fetch_sales_data_total_quantity_per_product():
    """Test that total sales quantity per product matches expected values."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    
    # Use records_by_product index for aggregation
    sales_by_product = {}
    for product_id, records in result.records_by_product.items():
        sales_by_product[product_id] = sum(r.quantity_sold for r in records)
    
    # Expected totals from mock data:
    # PROD-001: 15+20+10+25+30 = 100
    # PROD-002: 8+12+5+15 = 40
    # PROD-003: 5+3+8+4 = 20
    # PROD-004: 20+18+12+25+22 = 97
    assert sales_by_product["PROD-001"] == 100
    assert sales_by_product["PROD-002"] == 40
    assert sales_by_product["PROD-003"] == 20
    assert sales_by_product["PROD-004"] == 97


def test_fetch_sales_data_total_revenue_per_product():
    """Test that total revenue per product matches expected values."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    
    # Use records_by_product index for aggregation
    revenue_by_product = {}
    for product_id, records in result.records_by_product.items():
        revenue_by_product[product_id] = sum(r.total_revenue for r in records)
    
    # Expected totals from mock data:
    # PROD-001: 382.50+510.00+255.00+637.50+765.00 = 2550.00
    # PROD-002: 360.00+540.00+225.00+675.00 = 1800.00
    # PROD-003: 375.00+225.00+600.00+300.00 = 1500.00
    # PROD-004: 700.00+630.00+420.00+875.00+770.00 = 3395.00
    assert abs(revenue_by_product["PROD-001"] - 2550.00) < 0.01
    assert abs(revenue_by_product["PROD-002"] - 1800.00) < 0.01
    assert abs(revenue_by_product["PROD-003"] - 1500.00) < 0.01
    assert abs(revenue_by_product["PROD-004"] - 3395.00) < 0.01


def test_fetch_sales_data_days_with_sales_per_product():
    """Test that each product has correct number of days with sales."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    
    # Use records_by_product index to count unique days
    days_by_product = {}
    for product_id, records in result.records_by_product.items():
        days_by_product[product_id] = {r.timestamp.date() for r in records}
    
    # PROD-001: 5 different days, PROD-002: 4, PROD-003: 4, PROD-004: 5
    assert len(days_by_product["PROD-001"]) == 5
    assert len(days_by_product["PROD-002"]) == 4
    assert len(days_by_product["PROD-003"]) == 4
    assert len(days_by_product["PROD-004"]) == 5


def test_fetch_sales_data_revenue_equals_quantity_times_price():
    """Test that total_revenue = quantity_sold * unit_price for each record."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_sales_data()
    
    for record in result.records:
        expected_revenue = record.quantity_sold * record.unit_price
        assert abs(record.total_revenue - expected_revenue) < 0.01, \
            f"Revenue mismatch for {record.product_id}: expected {expected_revenue}, got {record.total_revenue}"


# ============================================================================
# BOM DATA TESTS
# ============================================================================

def test_fetch_bom_data_returns_bom_data():
    """Test that fetch_bom_data returns a BOMData instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    assert isinstance(result, BOMData)


def test_fetch_bom_data_has_exactly_eight_items():
    """Test that BOM data contains exactly 8 items."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    assert len(result.items) == 8


def test_fetch_bom_data_exact_material_requirements():
    """Test that BOM items have exact material requirements per product."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    
    # Build mapping: (product_id, material_id) -> quantity_required
    bom_map = {(item.product_id, item.material_id): item.quantity_required for item in result.items}
    
    # PROD-001 requires: MAT-001 (2.5), MAT-002 (1.0)
    assert bom_map[("PROD-001", "MAT-001")] == 2.5
    assert bom_map[("PROD-001", "MAT-002")] == 1.0
    
    # PROD-002 requires: MAT-001 (3.0), MAT-003 (2.0)
    assert bom_map[("PROD-002", "MAT-001")] == 3.0
    assert bom_map[("PROD-002", "MAT-003")] == 2.0
    
    # PROD-003 requires: MAT-002 (4.5), MAT-004 (1.5)
    assert bom_map[("PROD-003", "MAT-002")] == 4.5
    assert bom_map[("PROD-003", "MAT-004")] == 1.5
    
    # PROD-004 requires: MAT-001 (2.0), MAT-003 (1.5)
    assert bom_map[("PROD-004", "MAT-001")] == 2.0
    assert bom_map[("PROD-004", "MAT-003")] == 1.5


def test_fetch_bom_data_materials_used_by_each_product():
    """Test which materials are used by each product."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    
    # Build mapping: product_id -> set of material_ids
    product_materials = {}
    for item in result.items:
        if item.product_id not in product_materials:
            product_materials[item.product_id] = set()
        product_materials[item.product_id].add(item.material_id)
    
    assert product_materials["PROD-001"] == {"MAT-001", "MAT-002"}
    assert product_materials["PROD-002"] == {"MAT-001", "MAT-003"}
    assert product_materials["PROD-003"] == {"MAT-002", "MAT-004"}
    assert product_materials["PROD-004"] == {"MAT-001", "MAT-003"}


def test_fetch_bom_data_products_using_each_material():
    """Test which products use each material."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_bom_data()
    
    # Build mapping: material_id -> set of product_ids
    material_products = {}
    for item in result.items:
        if item.material_id not in material_products:
            material_products[item.material_id] = set()
        material_products[item.material_id].add(item.product_id)
    
    # MAT-001 used by PROD-001, PROD-002, PROD-004
    assert material_products["MAT-001"] == {"PROD-001", "PROD-002", "PROD-004"}
    # MAT-002 used by PROD-001, PROD-003
    assert material_products["MAT-002"] == {"PROD-001", "PROD-003"}
    # MAT-003 used by PROD-002, PROD-004
    assert material_products["MAT-003"] == {"PROD-002", "PROD-004"}
    # MAT-004 used only by PROD-003
    assert material_products["MAT-004"] == {"PROD-003"}


# ============================================================================
# BLANKET POS TESTS
# ============================================================================

def test_fetch_blanket_pos_returns_blanket_pos():
    """Test that fetch_blanket_pos returns a BlanketPOs instance."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert isinstance(result, BlanketPOs)


def test_fetch_blanket_pos_has_exactly_four_records():
    """Test that blanket POs contains exactly 4 records."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    assert len(result.blanket_pos) == 4


def test_fetch_blanket_pos_exact_ids():
    """Test that blanket POs have correct IDs."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    bpo_ids = {bpo.blanket_po_id for bpo in result.blanket_pos}
    expected_ids = {"BPO-001", "BPO-002", "BPO-003", "BPO-004"}
    assert bpo_ids == expected_ids


def test_fetch_blanket_pos_status_counts():
    """Test that blanket POs have correct status distribution."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    status_counts = {}
    for bpo in result.blanket_pos:
        status_counts[bpo.status] = status_counts.get(bpo.status, 0) + 1
    
    # Based on mock_erp.py: 3 ACTIVE, 1 EXPIRED (BPO-003)
    assert status_counts.get(BlanketPOStatus.ACTIVE, 0) == 3
    assert status_counts.get(BlanketPOStatus.EXPIRED, 0) == 1


def test_fetch_blanket_pos_exact_unit_prices():
    """Test that blanket POs have correct unit prices matching product prices."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    # Use blanket_pos_by_id index for direct lookup
    assert result.blanket_pos_by_id["BPO-001"].unit_price == 25.50  # PROD-001 price
    assert result.blanket_pos_by_id["BPO-002"].unit_price == 45.00  # PROD-002 price
    assert result.blanket_pos_by_id["BPO-003"].unit_price == 75.00  # PROD-003 price
    assert result.blanket_pos_by_id["BPO-004"].unit_price == 35.00  # PROD-004 price


def test_fetch_blanket_pos_remaining_less_than_total():
    """Test that remaining quantity is less than or equal to total quantity."""
    fetcher = MockERPDataFetcher()
    result = fetcher.fetch_blanket_pos()
    
    for bpo in result.blanket_pos:
        assert bpo.remaining_quantity <= bpo.total_quantity, \
            f"BPO {bpo.blanket_po_id}: remaining ({bpo.remaining_quantity}) > total ({bpo.total_quantity})"


# ============================================================================
# MATERIALS LOOKUP TESTS
# ============================================================================

def test_get_materials_lookup_returns_dict():
    """Test that get_materials_lookup returns a dictionary."""
    fetcher = MockERPDataFetcher()
    result = fetcher.get_materials_lookup()
    assert isinstance(result, dict)


def test_get_materials_lookup_has_exactly_four_materials():
    """Test that materials lookup has exactly 4 materials."""
    fetcher = MockERPDataFetcher()
    result = fetcher.get_materials_lookup()
    assert len(result) == 4


def test_get_materials_lookup_exact_names():
    """Test that materials lookup has correct material names."""
    fetcher = MockERPDataFetcher()
    result = fetcher.get_materials_lookup()
    
    assert result["MAT-001"] == "Steel Component"
    assert result["MAT-002"] == "Plastic Housing"
    assert result["MAT-003"] == "Electronic Circuit Board"
    assert result["MAT-004"] == "Rubber Gasket"

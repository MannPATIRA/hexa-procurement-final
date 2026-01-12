"""Tests for BasicPurchaseOrderBuilder."""

import pytest
from datetime import datetime, timedelta

from purchase_order_builder.basic_purchase_order_builder import BasicPurchaseOrderBuilder
from models.order_schedule import OrderSchedule, OrderItem, OrderStatus
from models.quote import Quote, QuoteStatus
from models.purchase_order import POStatus


def create_test_order_schedule() -> OrderSchedule:
    """Create a test order schedule with multiple suppliers."""
    now = datetime.now()
    orders = [
        # Supplier A - 2 materials
        OrderItem(
            material_id="MAT-001",
            material_name="Steel Component",
            supplier_id="SUP-A",
            supplier_name="Supplier A",
            order_date=now,
            expected_delivery_date=now + timedelta(days=7),
            order_quantity=100,
            order_status=OrderStatus.SCHEDULED,
        ),
        OrderItem(
            material_id="MAT-002",
            material_name="Plastic Housing",
            supplier_id="SUP-A",
            supplier_name="Supplier A",
            order_date=now,
            expected_delivery_date=now + timedelta(days=10),
            order_quantity=50,
            order_status=OrderStatus.SCHEDULED,
        ),
        # Supplier B - 1 material
        OrderItem(
            material_id="MAT-003",
            material_name="Circuit Board",
            supplier_id="SUP-B",
            supplier_name="Supplier B",
            order_date=now,
            expected_delivery_date=now + timedelta(days=14),
            order_quantity=200,
            order_status=OrderStatus.SCHEDULED,
        ),
        # Already delivered - should be excluded
        OrderItem(
            material_id="MAT-004",
            material_name="Rubber Gasket",
            supplier_id="SUP-C",
            supplier_name="Supplier C",
            order_date=now - timedelta(days=7),
            expected_delivery_date=now,
            order_quantity=75,
            order_status=OrderStatus.DELIVERED,
        ),
    ]
    return OrderSchedule(
        orders=orders,
        projected_levels=[],
        schedule_start_date=now,
        schedule_end_date=now + timedelta(days=30),
        generated_at=now,
    )


def create_test_quotes() -> list[Quote]:
    """Create test quotes matching the order schedule."""
    now = datetime.now()
    return [
        Quote(
            quote_id="Q-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-A",
            supplier_name="Supplier A",
            material_id="MAT-001",
            material_name="Steel Component",
            unit_price=5.50,
            quantity=100,
            total_price=550.0,
            lead_time_days=7,
            valid_until=now + timedelta(days=14),
            received_at=now,
            status=QuoteStatus.ACCEPTED,
        ),
        Quote(
            quote_id="Q-002",
            rfq_id="RFQ-002",
            supplier_id="SUP-A",
            supplier_name="Supplier A",
            material_id="MAT-002",
            material_name="Plastic Housing",
            unit_price=3.25,
            quantity=50,
            total_price=162.50,
            lead_time_days=10,
            valid_until=now + timedelta(days=14),
            received_at=now,
            status=QuoteStatus.ACCEPTED,
        ),
        Quote(
            quote_id="Q-003",
            rfq_id="RFQ-003",
            supplier_id="SUP-B",
            supplier_name="Supplier B",
            material_id="MAT-003",
            material_name="Circuit Board",
            unit_price=12.00,
            quantity=200,
            total_price=2400.0,
            lead_time_days=14,
            valid_until=now + timedelta(days=14),
            received_at=now,
            status=QuoteStatus.ACCEPTED,
        ),
    ]


class TestBasicPurchaseOrderBuilder:
    """Tests for BasicPurchaseOrderBuilder."""

    def test_builds_purchase_orders_grouped_by_supplier(self):
        """Should create one PO per supplier."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # Should have 2 POs (SUP-A and SUP-B, not SUP-C which is delivered)
        assert len(result.orders) == 2
        assert result.supplier_count == 2

    def test_consolidates_line_items_per_supplier(self):
        """Should consolidate multiple orders into line items."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # Find Supplier A's PO
        supplier_a_pos = result.orders_by_supplier.get("SUP-A", [])
        assert len(supplier_a_pos) == 1
        
        po = supplier_a_pos[0]
        assert po.item_count == 2
        assert po.total_quantity == 150  # 100 + 50

    def test_applies_pricing_from_quotes(self):
        """Should use unit prices from accepted quotes."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # Find Supplier A's PO
        po = result.orders_by_supplier["SUP-A"][0]
        
        # Check line items have correct pricing
        mat_001 = next(li for li in po.line_items if li.material_id == "MAT-001")
        assert mat_001.unit_price == 5.50
        assert mat_001.total_price == 550.0
        
        mat_002 = next(li for li in po.line_items if li.material_id == "MAT-002")
        assert mat_002.unit_price == 3.25
        assert mat_002.total_price == 162.50

    def test_calculates_totals_correctly(self):
        """Should calculate subtotal, tax, and total correctly."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes, tax_rate=0.1)
        
        # Check Supplier A's PO totals
        po = result.orders_by_supplier["SUP-A"][0]
        expected_subtotal = 550.0 + 162.50  # 712.50
        expected_tax = 71.25  # 10% of 712.50
        expected_total = 783.75
        
        assert po.subtotal == expected_subtotal
        assert po.tax_amount == expected_tax
        assert po.total_amount == expected_total

    def test_uses_default_price_when_no_quote(self):
        """Should use default unit price when no quote exists."""
        builder = BasicPurchaseOrderBuilder(default_unit_price=15.0)
        schedule = create_test_order_schedule()
        quotes = []  # No quotes
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # All line items should use default price
        for po in result.orders:
            for li in po.line_items:
                assert li.unit_price == 15.0

    def test_excludes_delivered_orders(self):
        """Should not include already delivered orders."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # SUP-C should not have a PO (order was delivered)
        assert "SUP-C" not in result.orders_by_supplier

    def test_sets_earliest_delivery_date(self):
        """Should use earliest required delivery date for PO."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # Supplier A has deliveries at day 7 and day 10
        po = result.orders_by_supplier["SUP-A"][0]
        now = datetime.now()
        expected_delivery = now + timedelta(days=7)
        
        # Check it's the earlier date (within a second)
        assert abs((po.expected_delivery_date - expected_delivery).total_seconds()) < 1

    def test_generates_unique_po_numbers(self):
        """Should generate unique PO numbers."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        po_numbers = [po.po_number for po in result.orders]
        assert len(po_numbers) == len(set(po_numbers))
        
        for po_number in po_numbers:
            assert po_number.startswith("PO-")

    def test_sets_draft_status(self):
        """Should create POs in draft status."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        for po in result.orders:
            assert po.status == POStatus.DRAFT

    def test_total_value_calculation(self):
        """Should calculate total value across all POs."""
        builder = BasicPurchaseOrderBuilder()
        schedule = create_test_order_schedule()
        quotes = create_test_quotes()
        
        result = builder.build_purchase_orders(schedule, quotes)
        
        # SUP-A: 550 + 162.50 = 712.50
        # SUP-B: 200 * 12.00 = 2400.00
        # Total: 3112.50
        assert result.total_value == 3112.50

    def test_empty_schedule_returns_empty_store(self):
        """Should return empty store for empty schedule."""
        builder = BasicPurchaseOrderBuilder()
        now = datetime.now()
        schedule = OrderSchedule(
            orders=[],
            projected_levels=[],
            schedule_start_date=now,
            schedule_end_date=now + timedelta(days=30),
            generated_at=now,
        )
        
        result = builder.build_purchase_orders(schedule, [])
        
        assert len(result.orders) == 0
        assert result.total_value == 0

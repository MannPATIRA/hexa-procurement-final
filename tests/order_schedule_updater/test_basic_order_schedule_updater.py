"""Test cases for BasicOrderScheduleUpdater."""

from datetime import datetime, timedelta
from order_schedule_updater.basic_order_schedule_updater import BasicOrderScheduleUpdater
from models.order_schedule import OrderSchedule, OrderItem, ProjectedInventoryLevel, OrderStatus
from models.quote import Quote, QuoteStatus
from models.evaluation_result import EvaluationResult


def _create_test_order_schedule():
    """Create a test order schedule."""
    now = datetime.now()
    orders = [
        OrderItem(
            material_id="MAT-001",
            material_name="Steel Component",
            supplier_id="OLD-SUP-001",
            supplier_name="Old Supplier",
            order_date=now,
            expected_delivery_date=now + timedelta(days=14),
            order_quantity=100,
            order_status=OrderStatus.SCHEDULED,
        ),
        OrderItem(
            material_id="MAT-002",
            material_name="Plastic Housing",
            supplier_id="OLD-SUP-002",
            supplier_name="Old Supplier 2",
            order_date=now + timedelta(days=5),
            expected_delivery_date=now + timedelta(days=19),
            order_quantity=50,
            order_status=OrderStatus.SCHEDULED,
        ),
    ]
    
    projected_levels = [
        ProjectedInventoryLevel(
            material_id="MAT-001",
            date=now,
            projected_quantity=10,
            is_below_reorder_point=True,
            is_above_maximum_stock=False,
        ),
    ]
    
    return OrderSchedule(
        orders=orders,
        projected_levels=projected_levels,
        schedule_start_date=now,
        schedule_end_date=now + timedelta(days=30),
        generated_at=now,
    )


def _create_test_quote():
    """Create a test quote."""
    now = datetime.now()
    return Quote(
        quote_id="QUOTE-NEW-001",
        rfq_id="RFQ-001",
        supplier_id="NEW-SUP-001",
        supplier_name="New Better Supplier",
        material_id="MAT-001",
        material_name="Steel Component",
        unit_price=4.0,
        quantity=100,
        total_price=400.0,
        lead_time_days=5,
        valid_until=now + timedelta(days=30),
        received_at=now,
        status=QuoteStatus.RECEIVED,
    )


def _create_better_evaluation():
    """Create an evaluation result that indicates quote is better."""
    return EvaluationResult(
        quote_id="QUOTE-NEW-001",
        overall_score=75.0,
        price_score=80.0,
        lead_time_score=70.0,
        reliability_score=75.0,
        is_better_than_current=True,
        current_supplier_score=50.0,
        improvement_percentage=50.0,
        recommendation="RECOMMEND: Quote is better than current suppliers.",
    )


def _create_worse_evaluation():
    """Create an evaluation result that indicates quote is worse."""
    return EvaluationResult(
        quote_id="QUOTE-NEW-001",
        overall_score=30.0,
        price_score=20.0,
        lead_time_score=40.0,
        reliability_score=30.0,
        is_better_than_current=False,
        current_supplier_score=60.0,
        improvement_percentage=-50.0,
        recommendation="NOT RECOMMENDED: Current suppliers are more favorable.",
    )


def test_update_if_better_returns_order_schedule():
    """Test that update_if_better returns an OrderSchedule."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    assert isinstance(result, OrderSchedule)


def test_update_if_better_updates_supplier():
    """Test that better quote updates the supplier."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # Find the updated order
    mat_001_orders = [o for o in result.orders if o.material_id == "MAT-001"]
    assert len(mat_001_orders) == 1
    assert mat_001_orders[0].supplier_id == quote.supplier_id
    assert mat_001_orders[0].supplier_name == quote.supplier_name


def test_update_if_better_no_update_when_worse():
    """Test that worse quote doesn't update schedule."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_worse_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # Should return original schedule unchanged
    assert result == schedule


def test_update_if_better_updates_delivery_date():
    """Test that delivery date is updated based on new lead time."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()  # 5 day lead time
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # Find the updated order
    mat_001_orders = [o for o in result.orders if o.material_id == "MAT-001"]
    updated_order = mat_001_orders[0]
    
    # New delivery date should be order_date + new lead time
    expected_delivery = updated_order.order_date + timedelta(days=quote.lead_time_days)
    assert updated_order.expected_delivery_date == expected_delivery


def test_update_if_better_adds_metadata():
    """Test that update adds metadata about the change."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # Find the updated order
    mat_001_orders = [o for o in result.orders if o.material_id == "MAT-001"]
    updated_order = mat_001_orders[0]
    
    assert "updated_from_quote" in updated_order.metadata
    assert "previous_supplier" in updated_order.metadata


def test_update_if_better_only_updates_matching_material():
    """Test that only orders for matching material are updated."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()  # For MAT-001
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # MAT-002 order should be unchanged
    mat_002_orders = [o for o in result.orders if o.material_id == "MAT-002"]
    assert len(mat_002_orders) == 1
    assert mat_002_orders[0].supplier_id == "OLD-SUP-002"


def test_update_if_better_only_updates_pending_scheduled():
    """Test that only PENDING or SCHEDULED orders are updated."""
    updater = BasicOrderScheduleUpdater()
    now = datetime.now()
    
    # Create schedule with one DELIVERED order
    orders = [
        OrderItem(
            material_id="MAT-001",
            material_name="Steel Component",
            supplier_id="OLD-SUP-001",
            supplier_name="Old Supplier",
            order_date=now - timedelta(days=10),
            expected_delivery_date=now - timedelta(days=3),
            order_quantity=100,
            order_status=OrderStatus.DELIVERED,  # Already delivered
        ),
        OrderItem(
            material_id="MAT-001",
            material_name="Steel Component",
            supplier_id="OLD-SUP-001",
            supplier_name="Old Supplier",
            order_date=now,
            expected_delivery_date=now + timedelta(days=14),
            order_quantity=100,
            order_status=OrderStatus.SCHEDULED,  # Can be updated
        ),
    ]
    
    schedule = OrderSchedule(
        orders=orders,
        projected_levels=[],
        schedule_start_date=now - timedelta(days=10),
        schedule_end_date=now + timedelta(days=30),
        generated_at=now,
    )
    
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    # DELIVERED order should be unchanged
    delivered_orders = [o for o in result.orders if o.order_status == OrderStatus.DELIVERED]
    assert len(delivered_orders) == 1
    assert delivered_orders[0].supplier_id == "OLD-SUP-001"
    
    # SCHEDULED order should be updated
    scheduled_orders = [o for o in result.orders if o.order_status == OrderStatus.SCHEDULED]
    assert len(scheduled_orders) == 1
    assert scheduled_orders[0].supplier_id == quote.supplier_id


def test_update_if_better_preserves_projected_levels():
    """Test that projected inventory levels are preserved."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    assert len(result.projected_levels) == len(schedule.projected_levels)


def test_update_if_better_updates_generated_at():
    """Test that generated_at timestamp is updated."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    original_generated_at = schedule.generated_at
    result = updater.update_if_better(schedule, quote, evaluation)
    
    assert result.generated_at >= original_generated_at


def test_update_if_better_preserves_schedule_dates():
    """Test that schedule start and end dates are preserved."""
    updater = BasicOrderScheduleUpdater()
    schedule = _create_test_order_schedule()
    quote = _create_test_quote()
    evaluation = _create_better_evaluation()
    
    result = updater.update_if_better(schedule, quote, evaluation)
    
    assert result.schedule_start_date == schedule.schedule_start_date
    assert result.schedule_end_date == schedule.schedule_end_date


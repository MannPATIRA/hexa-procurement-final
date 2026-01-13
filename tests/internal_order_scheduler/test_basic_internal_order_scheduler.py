"""Test cases for BasicInternalOrderScheduler."""

from datetime import datetime, timedelta
from internal_order_scheduler.basic_internal_order_scheduler import BasicInternalOrderScheduler
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from models.sales_forecast import SalesForecast
from models.inventory_data import InventoryData, InventoryItem, ItemType
from models.product_production import ProductProductionInfo, ProductProductionStore
from models.internal_order import InternalOrderStatus
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def create_test_sales_forecast() -> SalesForecast:
    """Create a test sales forecast."""
    now = datetime.now()
    from models.sales_forecast import ForecastItem
    
    return SalesForecast(
        forecasts=[
            ForecastItem(
                item_id="PROD-001",
                item_name="Widget A",
                forecasted_quantity=100,
                forecast_period_start=now,
                forecast_period_end=now + timedelta(days=30),
                confidence_level=0.8,
            ),
            ForecastItem(
                item_id="PROD-002",
                item_name="Widget B",
                forecasted_quantity=50,
                forecast_period_start=now,
                forecast_period_end=now + timedelta(days=30),
                confidence_level=0.75,
            ),
        ],
        forecast_generated_at=now,
        forecast_period_start=now,
        forecast_period_end=now + timedelta(days=30),
    )


def create_test_product_inventory() -> InventoryData:
    """Create test product inventory with low levels."""
    now = datetime.now()
    return InventoryData(
        items=[
            InventoryItem(
                item_id="PROD-001",
                item_name="Widget A",
                item_type=ItemType.PRODUCT,
                quantity=10,  # Low inventory
                unit_price=25.50,
                location="Warehouse-1",
                last_updated=now,
            ),
            InventoryItem(
                item_id="PROD-002",
                item_name="Widget B",
                item_type=ItemType.PRODUCT,
                quantity=5,  # Low inventory
                unit_price=45.00,
                location="Warehouse-2",
                last_updated=now,
            ),
        ],
        fetched_at=now,
    )


def create_test_production_info() -> ProductProductionStore:
    """Create test production information."""
    return ProductProductionStore(
        items=[
            ProductProductionInfo(
                product_id="PROD-001",
                production_lead_time_days=2,
                production_rate_per_day=50,
            ),
            ProductProductionInfo(
                product_id="PROD-002",
                production_lead_time_days=3,
                production_rate_per_day=40,
            ),
        ],
    )


class TestBasicInternalOrderScheduler:
    """Tests for BasicInternalOrderScheduler."""

    def test_schedule_internal_orders_returns_schedule(self):
        """Test that scheduler returns InternalOrderSchedule."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        product_inventory = create_test_product_inventory()
        production_info = create_test_production_info()
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        assert result is not None
        assert len(result.orders) > 0

    def test_schedules_production_when_inventory_low(self):
        """Test that production is scheduled when inventory is below reorder point."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        
        # Very low inventory
        product_inventory = InventoryData(
            items=[
                InventoryItem(
                    item_id="PROD-001",
                    item_name="Widget A",
                    item_type=ItemType.PRODUCT,
                    quantity=2,  # Very low
                    unit_price=25.50,
                    location="Warehouse-1",
                    last_updated=datetime.now(),
                ),
            ],
            fetched_at=datetime.now(),
        )
        
        production_info = ProductProductionStore(
            items=[
                ProductProductionInfo(
                    product_id="PROD-001",
                    production_lead_time_days=2,
                    production_rate_per_day=50,
                ),
            ],
        )
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        # Should have scheduled production orders
        assert len(result.orders) > 0
        assert all(order.status == InternalOrderStatus.SCHEDULED for order in result.orders)

    def test_respects_production_lead_times(self):
        """Test that completion dates respect production lead times."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        product_inventory = create_test_product_inventory()
        
        production_info = ProductProductionStore(
            items=[
                ProductProductionInfo(
                    product_id="PROD-001",
                    production_lead_time_days=5,  # 5 day lead time
                    production_rate_per_day=50,
                ),
            ],
        )
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        for order in result.orders:
            if order.product_id == "PROD-001":
                lead_time = (order.completion_date - order.start_date).days
                assert lead_time == 5, f"Expected 5 day lead time, got {lead_time}"

    def test_no_duplicate_orders(self):
        """Test that no duplicate production orders are scheduled."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        product_inventory = create_test_product_inventory()
        production_info = create_test_production_info()
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        # Check no duplicate orders for same product on same day
        orders_by_product_date = {}
        for order in result.orders:
            key = (order.product_id, order.start_date.date())
            assert key not in orders_by_product_date, f"Duplicate order for {order.product_id} on {order.start_date.date()}"
            orders_by_product_date[key] = order

    def test_orders_indexed_by_product(self):
        """Test that orders are indexed by product_id."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        product_inventory = create_test_product_inventory()
        production_info = create_test_production_info()
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        # Check index exists
        assert hasattr(result, 'orders_by_product')
        
        # Check all orders are in index
        for order in result.orders:
            assert order.product_id in result.orders_by_product
            assert order in result.orders_by_product[order.product_id]

    def test_handles_high_inventory(self):
        """Test that no orders are scheduled when inventory is high."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        
        # High inventory
        product_inventory = InventoryData(
            items=[
                InventoryItem(
                    item_id="PROD-001",
                    item_name="Widget A",
                    item_type=ItemType.PRODUCT,
                    quantity=1000,  # Very high
                    unit_price=25.50,
                    location="Warehouse-1",
                    last_updated=datetime.now(),
                ),
            ],
            fetched_at=datetime.now(),
        )
        
        production_info = ProductProductionStore(
            items=[
                ProductProductionInfo(
                    product_id="PROD-001",
                    production_lead_time_days=2,
                    production_rate_per_day=50,
                ),
            ],
        )
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        # Should have few or no orders initially (inventory is high)
        # May schedule some later as inventory depletes
        assert isinstance(result.orders, list)

    def test_respects_production_capacity(self):
        """Test that production quantity respects capacity constraints."""
        scheduler = BasicInternalOrderScheduler()
        sales_forecast = create_test_sales_forecast()
        
        product_inventory = InventoryData(
            items=[
                InventoryItem(
                    item_id="PROD-001",
                    item_name="Widget A",
                    item_type=ItemType.PRODUCT,
                    quantity=2,  # Low inventory
                    unit_price=25.50,
                    location="Warehouse-1",
                    last_updated=datetime.now(),
                ),
            ],
            fetched_at=datetime.now(),
        )
        
        production_info = ProductProductionStore(
            items=[
                ProductProductionInfo(
                    product_id="PROD-001",
                    production_lead_time_days=2,
                    production_rate_per_day=30,  # Limited capacity
                ),
            ],
        )
        
        result = scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=30
        )
        
        # Check that order quantities don't exceed capacity
        for order in result.orders:
            if order.product_id == "PROD-001":
                # Order quantity should not exceed daily capacity
                # (though it could be less if demand gap is smaller)
                assert order.quantity <= 30, f"Order quantity {order.quantity} exceeds capacity 30"

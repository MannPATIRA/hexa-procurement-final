"""Mock ERP system implementation."""

from datetime import datetime, timedelta
from typing import List
from models.inventory_data import InventoryItem, InventoryData, ItemType
from models.delivery_history import DeliveryRecord, DeliveryHistory, DeliveryStatus
from models.sales_data import SalesRecord, SalesData
from models.bom import BOMItem, BOMData
from models.blanket_pos import BlanketPO, BlanketPOs, BlanketPOStatus
from models.product_production import ProductProductionInfo, ProductProductionStore

class MockERP:
    """Mock implementation of ERP system for testing and development.

    This class provides mock data that satisfies the ERPDataFetcherProtocol
    interface without requiring an actual ERP system connection.
    """

    def __init__(self) -> None:
        """Initialize mock ERP with default test data."""
        self.inventory_items: List[InventoryItem] = [
            # Product inventory (finished goods)
            InventoryItem(
                item_id="PROD-001",
                item_name="Widget A",
                item_type=ItemType.PRODUCT,
                quantity=30,  # Lower inventory to trigger scheduled order
                unit_price=25.50,
                location="Warehouse-1",
                last_updated=datetime.now() - timedelta(days=1),
                supplier_id="SUP-001",
            ),
            InventoryItem(
                item_id="PROD-002",
                item_name="Widget B",
                item_type=ItemType.PRODUCT,
                quantity=200,  # Higher inventory - no scheduled order needed
                unit_price=45.00,
                location="Warehouse-2",
                last_updated=datetime.now() - timedelta(hours=6),
                supplier_id="SUP-002",
            ),
            InventoryItem(
                item_id="PROD-003",
                item_name="Widget C",
                item_type=ItemType.PRODUCT,
                quantity=3,  # Very low inventory - but has scheduled order today
                unit_price=75.00,
                location="Warehouse-3",
                last_updated=datetime.now() - timedelta(hours=2),
                supplier_id="SUP-003",
            ),
            InventoryItem(
                item_id="PROD-004",
                item_name="Widget D",
                item_type=ItemType.PRODUCT,
                quantity=150,  # Above reorder point - use simulate_inventory_drop to trigger breach
                unit_price=35.00,
                location="Warehouse-1",
                last_updated=datetime.now() - timedelta(hours=4),
                supplier_id="SUP-001",  # Supplied by Acme Corp
            ),
            # Material inventory (raw materials/components)
            InventoryItem(
                item_id="MAT-001",
                item_name="Steel Component",
                item_type=ItemType.MATERIAL,
                quantity=500,
                unit_price=5.0,
                location="Raw Materials Warehouse",
                last_updated=datetime.now() - timedelta(hours=12),
                supplier_id="SUP-001",
            ),
            InventoryItem(
                item_id="MAT-002",
                item_name="Plastic Housing",
                item_type=ItemType.MATERIAL,
                quantity=200,
                unit_price=3.0,
                location="Raw Materials Warehouse",
                last_updated=datetime.now() - timedelta(hours=8),
                supplier_id="SUP-002",
            ),
            InventoryItem(
                item_id="MAT-003",
                item_name="Electronic Circuit Board",
                item_type=ItemType.MATERIAL,
                quantity=150,
                unit_price=12.0,
                location="Raw Materials Warehouse",
                last_updated=datetime.now() - timedelta(hours=6),
                supplier_id="SUP-003",
            ),
            InventoryItem(
                item_id="MAT-004",
                item_name="Rubber Gasket",
                item_type=ItemType.MATERIAL,
                quantity=100,
                unit_price=2.5,
                location="Raw Materials Warehouse",
                last_updated=datetime.now() - timedelta(hours=4),
                supplier_id="SUP-001",
            ),
        ]

        self.inventory_data = InventoryData(
            items=self.inventory_items,
            fetched_at=datetime.now(),
        )

        self.records: List[DeliveryRecord] = [
            DeliveryRecord(
                delivery_id="DEL-001",
                order_id="ORD-001",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-001",
                product_name="Widget A",
                quantity=100,
                delivery_date=datetime.now() - timedelta(days=5),
                status=DeliveryStatus.DELIVERED,
                expected_delivery_date=datetime.now() - timedelta(days=12),  # Ordered 12 days ago
                actual_delivery_date=datetime.now() - timedelta(days=5),  # Delivered 5 days ago (7 day lead time)
            ),
            DeliveryRecord(
                delivery_id="DEL-002",
                order_id="ORD-002",
                supplier_id="SUP-002",
                supplier_name="Tech Supplies Inc",
                product_id="PROD-002",
                product_name="Widget B",
                quantity=50,
                delivery_date=datetime.now() - timedelta(days=10),
                status=DeliveryStatus.DELIVERED,
                expected_delivery_date=datetime.now() - timedelta(days=15),  # 5 day lead time
                actual_delivery_date=datetime.now() - timedelta(days=10),
            ),
            DeliveryRecord(
                delivery_id="DEL-003",
                order_id="ORD-003",
                supplier_id="SUP-003",
                supplier_name="Global Parts Ltd",
                product_id="PROD-003",
                product_name="Widget C",
                quantity=200,
                delivery_date=datetime.now() - timedelta(days=3),
                status=DeliveryStatus.DELIVERED,
                expected_delivery_date=datetime.now() - timedelta(days=7),  # 4 day lead time
                actual_delivery_date=datetime.now() - timedelta(days=3),
            ),
            DeliveryRecord(
                delivery_id="DEL-004",
                order_id="ORD-004",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-004",
                product_name="Widget D",
                quantity=150,
                delivery_date=datetime.now() - timedelta(days=8),
                status=DeliveryStatus.DELIVERED,
                expected_delivery_date=datetime.now() - timedelta(days=14),  # 6 day lead time
                actual_delivery_date=datetime.now() - timedelta(days=8),
            ),
        ]

        self.delivery_history = DeliveryHistory(
            records=self.records,
            fetched_at=datetime.now(),
        )

        # Sales data - time series over the past 30 days
        now = datetime.now()
        start_date = now - timedelta(days=30)
        
        self.sales_records: List[SalesRecord] = [
            # PROD-001 (Widget A) sales
            SalesRecord(
                timestamp=now - timedelta(days=28),
                product_id="PROD-001",
                product_name="Widget A",
                quantity_sold=15,
                unit_price=25.50,
                total_revenue=382.50,
                customer_id="CUST-001",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=25),
                product_id="PROD-001",
                product_name="Widget A",
                quantity_sold=20,
                unit_price=25.50,
                total_revenue=510.00,
                customer_id="CUST-002",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=20),
                product_id="PROD-001",
                product_name="Widget A",
                quantity_sold=10,
                unit_price=25.50,
                total_revenue=255.00,
                customer_id="CUST-001",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=15),
                product_id="PROD-001",
                product_name="Widget A",
                quantity_sold=25,
                unit_price=25.50,
                total_revenue=637.50,
                customer_id="CUST-003",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=5),
                product_id="PROD-001",
                product_name="Widget A",
                quantity_sold=30,
                unit_price=25.50,
                total_revenue=765.00,
                customer_id="CUST-002",
            ),
            # PROD-002 (Widget B) sales
            SalesRecord(
                timestamp=now - timedelta(days=27),
                product_id="PROD-002",
                product_name="Widget B",
                quantity_sold=8,
                unit_price=45.00,
                total_revenue=360.00,
                customer_id="CUST-002",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=22),
                product_id="PROD-002",
                product_name="Widget B",
                quantity_sold=12,
                unit_price=45.00,
                total_revenue=540.00,
                customer_id="CUST-004",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=18),
                product_id="PROD-002",
                product_name="Widget B",
                quantity_sold=5,
                unit_price=45.00,
                total_revenue=225.00,
                customer_id="CUST-001",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=10),
                product_id="PROD-002",
                product_name="Widget B",
                quantity_sold=15,
                unit_price=45.00,
                total_revenue=675.00,
                customer_id="CUST-003",
            ),
            # PROD-003 (Widget C) sales
            SalesRecord(
                timestamp=now - timedelta(days=26),
                product_id="PROD-003",
                product_name="Widget C",
                quantity_sold=5,
                unit_price=75.00,
                total_revenue=375.00,
                customer_id="CUST-004",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=21),
                product_id="PROD-003",
                product_name="Widget C",
                quantity_sold=3,
                unit_price=75.00,
                total_revenue=225.00,
                customer_id="CUST-002",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=12),
                product_id="PROD-003",
                product_name="Widget C",
                quantity_sold=8,
                unit_price=75.00,
                total_revenue=600.00,
                customer_id="CUST-001",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=7),
                product_id="PROD-003",
                product_name="Widget C",
                quantity_sold=4,
                unit_price=75.00,
                total_revenue=300.00,
                customer_id="CUST-003",
            ),
            # PROD-004 (Widget D) sales
            SalesRecord(
                timestamp=now - timedelta(days=29),
                product_id="PROD-004",
                product_name="Widget D",
                quantity_sold=20,
                unit_price=35.00,
                total_revenue=700.00,
                customer_id="CUST-001",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=24),
                product_id="PROD-004",
                product_name="Widget D",
                quantity_sold=18,
                unit_price=35.00,
                total_revenue=630.00,
                customer_id="CUST-004",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=19),
                product_id="PROD-004",
                product_name="Widget D",
                quantity_sold=12,
                unit_price=35.00,
                total_revenue=420.00,
                customer_id="CUST-002",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=14),
                product_id="PROD-004",
                product_name="Widget D",
                quantity_sold=25,
                unit_price=35.00,
                total_revenue=875.00,
                customer_id="CUST-003",
            ),
            SalesRecord(
                timestamp=now - timedelta(days=3),
                product_id="PROD-004",
                product_name="Widget D",
                quantity_sold=22,
                unit_price=35.00,
                total_revenue=770.00,
                customer_id="CUST-001",
            ),
        ]

        self.sales_data = SalesData(
            records=self.sales_records,
            start_date=start_date,
            end_date=now,
            fetched_at=now,
        )

        # Materials lookup - mapping material IDs to names
        self.materials_lookup: dict[str, str] = {
            "MAT-001": "Steel Component",
            "MAT-002": "Plastic Housing",
            "MAT-003": "Electronic Circuit Board",
            "MAT-004": "Rubber Gasket",
        }

        # BOM data - mapping products to materials
        self.bom_items: List[BOMItem] = [
            BOMItem(
                product_id="PROD-001",
                material_id="MAT-001",
                quantity_required=2.5,
            ),
            BOMItem(
                product_id="PROD-001",
                material_id="MAT-002",
                quantity_required=1.0,
            ),
            BOMItem(
                product_id="PROD-002",
                material_id="MAT-001",
                quantity_required=3.0,
            ),
            BOMItem(
                product_id="PROD-002",
                material_id="MAT-003",
                quantity_required=2.0,
            ),
            BOMItem(
                product_id="PROD-003",
                material_id="MAT-002",
                quantity_required=4.5,
            ),
            BOMItem(
                product_id="PROD-003",
                material_id="MAT-004",
                quantity_required=1.5,
            ),
            BOMItem(
                product_id="PROD-004",
                material_id="MAT-001",
                quantity_required=2.0,
            ),
            BOMItem(
                product_id="PROD-004",
                material_id="MAT-003",
                quantity_required=1.5,
            ),
        ]

        self.bom_data = BOMData(
            items=self.bom_items,
            fetched_at=datetime.now(),
        )

        # Blanket purchase orders
        self.blanket_pos: List[BlanketPO] = [
            BlanketPO(
                blanket_po_id="BPO-001",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-001",
                product_name="Widget A",
                total_quantity=1000,
                remaining_quantity=750,
                unit_price=25.50,
                start_date=datetime.now() - timedelta(days=60),
                end_date=datetime.now() + timedelta(days=30),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 30",
            ),
            BlanketPO(
                blanket_po_id="BPO-002",
                supplier_id="SUP-002",
                supplier_name="Tech Supplies Inc",
                product_id="PROD-002",
                product_name="Widget B",
                total_quantity=500,
                remaining_quantity=300,
                unit_price=45.00,
                start_date=datetime.now() - timedelta(days=45),
                end_date=datetime.now() + timedelta(days=45),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 45",
            ),
            BlanketPO(
                blanket_po_id="BPO-003",
                supplier_id="SUP-003",
                supplier_name="Global Parts Ltd",
                product_id="PROD-003",
                product_name="Widget C",
                total_quantity=300,
                remaining_quantity=50,
                unit_price=75.00,
                start_date=datetime.now() - timedelta(days=90),
                end_date=datetime.now() - timedelta(days=5),
                status=BlanketPOStatus.EXPIRED,
                terms="Net 30",
            ),
            BlanketPO(
                blanket_po_id="BPO-004",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-004",
                product_name="Widget D",
                total_quantity=800,
                remaining_quantity=650,
                unit_price=35.00,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() + timedelta(days=60),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 30",
            ),
        ]

        self.blanket_pos_data = BlanketPOs(
            blanket_pos=self.blanket_pos,
            fetched_at=datetime.now(),
        )

        # Product production information
        self.product_production_info: List[ProductProductionInfo] = [
            ProductProductionInfo(
                product_id="PROD-001",
                production_lead_time_days=2,
                production_rate_per_day=50,  # Can produce 50 units per day
                setup_time_hours=2.0,
            ),
            ProductProductionInfo(
                product_id="PROD-002",
                production_lead_time_days=3,
                production_rate_per_day=40,
                setup_time_hours=3.0,
            ),
            ProductProductionInfo(
                product_id="PROD-003",
                production_lead_time_days=4,
                production_rate_per_day=30,
                setup_time_hours=4.0,
            ),
            ProductProductionInfo(
                product_id="PROD-004",
                production_lead_time_days=2,
                production_rate_per_day=60,
                setup_time_hours=1.5,
            ),
        ]

        self.product_production_store = ProductProductionStore(
            items=self.product_production_info,
        )

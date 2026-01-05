"""Mock CRM system implementation."""

from datetime import datetime, timedelta
from typing import List
from models.blanket_pos import BlanketPO, BlanketPOStatus, BlanketPOs
from models.approved_suppliers_list import Supplier, SupplierStatus, ApprovedSuppliersList

class MockCRM:
    def __init__(self) -> None:
        self._blanket_po_list: List[BlanketPO] = [
            BlanketPO(
                blanket_po_id="BPO-001",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-001",
                product_name="Widget A",
                total_quantity=1000,
                remaining_quantity=750,
                unit_price=25.50,
                start_date=datetime.now() - timedelta(days=90),
                end_date=datetime.now() + timedelta(days=275),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 30, FOB Destination",
            ),
            BlanketPO(
                blanket_po_id="BPO-002",
                supplier_id="SUP-002",
                supplier_name="Tech Supplies Inc",
                product_id="PROD-002",
                product_name="Widget B",
                total_quantity=500,
                remaining_quantity=450,
                unit_price=45.00,
                start_date=datetime.now() - timedelta(days=60),
                end_date=datetime.now() + timedelta(days=305),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 45, FOB Origin",
            ),
            BlanketPO(
                blanket_po_id="BPO-003",
                supplier_id="SUP-003",
                supplier_name="Global Parts Ltd",
                product_id="PROD-003",
                product_name="Widget C",
                total_quantity=800,
                remaining_quantity=600,
                unit_price=75.00,
                start_date=datetime.now() - timedelta(days=45),
                end_date=datetime.now() + timedelta(days=320),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 30, FOB Destination",
            ),
            BlanketPO(
                blanket_po_id="BPO-004",
                supplier_id="SUP-001",
                supplier_name="Acme Corp",
                product_id="PROD-004",
                product_name="Widget D",
                total_quantity=600,
                remaining_quantity=500,
                unit_price=35.00,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() + timedelta(days=335),
                status=BlanketPOStatus.ACTIVE,
                terms="Net 30, FOB Destination",
            ),
        ]

        self._researched_suppliers: List[Supplier] = [
            Supplier(
                supplier_id="SUP-004",
                supplier_name="Premium Parts Co",
                contact_email="sales@premiumparts.com",
                contact_phone="+1-555-0202",
                status=SupplierStatus.PENDING_APPROVAL,
                approved_date=datetime.now() - timedelta(days=15),
                categories=["Electronics"],
                rating=4.6,
                notes="Specializes in high-end components. Quality assessment in progress.",
            ),
            Supplier(
                supplier_id="SUP-005",
                supplier_name="Fast Logistics Inc",
                contact_email="orders@fastlogistics.com",
                contact_phone="+1-555-0203",
                status=SupplierStatus.PENDING_APPROVAL,
                approved_date=datetime.now() - timedelta(days=7),
                categories=["Electronics", "Components"],
                rating=4.3,
                notes="New supplier - quick delivery times. Under evaluation.",
            ),
        ]

        self.blanket_pos = BlanketPOs(
            blanket_pos=self._blanket_po_list,
            fetched_at=datetime.now(),
        )

        self.approved_suppliers = ApprovedSuppliersList(
            suppliers=self._researched_suppliers,
            source="CRM",
            fetched_at=datetime.now(),
        )

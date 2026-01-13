"""Test supplier data generator for order builder tests.

Creates 10 imaginary suppliers with varying levels of data completeness:
- 5 suppliers with complete data (all fields filled)
- 5 suppliers with realistic incomplete data (missing optional fields)
"""

from datetime import datetime, timedelta
from typing import List

from models.approved_suppliers_list import ApprovedSuppliersList, Supplier, SupplierStatus
from models.supplier_state import SupplierStateStore, SupplierState
from models.quote import Quote, QuoteStatus


def create_test_suppliers() -> ApprovedSuppliersList:
    """Create 10 test suppliers with varying data completeness.
    
    Returns:
        ApprovedSuppliersList with 10 suppliers:
        - 5 with complete data (all fields)
        - 5 with incomplete data (missing optional fields)
    """
    now = datetime.now()
    
    suppliers = [
        # ===== COMPLETE DATA SUPPLIERS (5) =====
        
        # 1. Premium Supplier - High-end manufacturer
        Supplier(
            supplier_id="SUP-PREMIUM-001",
            supplier_name="Elite Components Manufacturing",
            contact_email="procurement@elitecomponents.com",
            contact_phone="+1-555-0101",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=730),  # 2 years ago
            categories=["Electronics", "Precision Components", "Aerospace"],
            rating=4.9,
            notes="Premium supplier with excellent quality. ISO 9001 certified. Preferred for critical components.",
        ),
        
        # 2. Established Supplier - Reliable long-term partner
        Supplier(
            supplier_id="SUP-ESTABLISHED-002",
            supplier_name="Reliable Metals Corp",
            contact_email="orders@reliablemetals.com",
            contact_phone="+1-555-0202",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=1095),  # 3 years ago
            categories=["Metals", "Raw Materials", "Steel"],
            rating=4.6,
            notes="Long-standing relationship. Consistent delivery performance. Volume discounts available.",
        ),
        
        # 3. Budget Supplier - Cost-effective option
        Supplier(
            supplier_id="SUP-BUDGET-003",
            supplier_name="Value Parts Distributors",
            contact_email="sales@valueparts.com",
            contact_phone="+1-555-0303",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=365),  # 1 year ago
            categories=["General Parts", "Plastics", "Fasteners"],
            rating=3.8,
            notes="Cost-effective supplier. Good for non-critical components. Longer lead times acceptable.",
        ),
        
        # 4. Specialized Supplier - Niche expertise
        Supplier(
            supplier_id="SUP-SPECIALIZED-004",
            supplier_name="Advanced Polymer Solutions",
            contact_email="info@advancedpolymers.com",
            contact_phone="+1-555-0404",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=545),  # 1.5 years ago
            categories=["Polymers", "Specialty Materials", "Custom Molding"],
            rating=4.7,
            notes="Specialized in custom polymer components. Excellent technical support. R&D partnership.",
        ),
        
        # 5. Inactive Supplier - Complete data but inactive
        Supplier(
            supplier_id="SUP-INACTIVE-005",
            supplier_name="Legacy Components Inc",
            contact_email="contact@legacycomponents.com",
            contact_phone="+1-555-0505",
            status=SupplierStatus.INACTIVE,
            approved_date=now - timedelta(days=1825),  # 5 years ago
            categories=["Electronics", "Legacy Parts"],
            rating=4.2,
            notes="Previously active supplier. Currently inactive due to business restructuring. May reactivate.",
        ),
        
        # ===== INCOMPLETE DATA SUPPLIERS (5) =====
        
        # 6. New Supplier - Pending approval, minimal data
        Supplier(
            supplier_id="SUP-NEW-006",
            supplier_name="Innovation Materials Ltd",
            contact_email="hello@innovationmaterials.com",
            contact_phone=None,  # Missing phone
            status=SupplierStatus.PENDING_APPROVAL,
            approved_date=now - timedelta(days=30),  # Recently added
            categories=["New Materials", "Composites"],
            rating=None,  # No rating yet
            notes=None,  # No notes yet
        ),
        
        # 7. Emerging Supplier - Active but limited history
        Supplier(
            supplier_id="SUP-EMERGING-007",
            supplier_name="Rapid Supply Co",
            contact_email="orders@rapidsupply.com",
            contact_phone="+1-555-0707",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=90),  # 3 months ago
            categories=["General Supplies"],
            rating=4.0,  # Limited reviews
            notes=None,  # No detailed notes
        ),
        
        # 8. Regional Supplier - Missing contact details
        Supplier(
            supplier_id="SUP-REGIONAL-008",
            supplier_name="Regional Manufacturing Partners",
            contact_email="info@regionalmfg.com",
            contact_phone=None,  # Missing phone
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=180),  # 6 months ago
            categories=["Local Manufacturing", "Assembly"],
            rating=3.5,
            notes="Regional supplier with local presence. Good for quick turnaround.",
        ),
        
        # 9. International Supplier - Missing rating
        Supplier(
            supplier_id="SUP-INTERNATIONAL-009",
            supplier_name="Global Sourcing Solutions",
            contact_email="procurement@globalsourcing.com",
            contact_phone="+86-21-1234-5678",
            status=SupplierStatus.ACTIVE,
            approved_date=now - timedelta(days=120),  # 4 months ago
            categories=["Global Sourcing", "Electronics", "Components"],
            rating=None,  # No rating yet (new relationship)
            notes="International supplier. Competitive pricing. Longer lead times expected.",
        ),
        
        # 10. Suspended Supplier - Complete data but suspended
        Supplier(
            supplier_id="SUP-SUSPENDED-010",
            supplier_name="Troubled Parts Supply",
            contact_email="admin@troubledparts.com",
            contact_phone="+1-555-1010",
            status=SupplierStatus.SUSPENDED,
            approved_date=now - timedelta(days=450),  # 1.25 years ago
            categories=["General Parts"],
            rating=2.5,  # Low rating
            notes="Suspended due to quality issues and delivery delays. Under review for reinstatement.",
        ),
    ]
    
    return ApprovedSuppliersList(
        suppliers=suppliers,
        source="MERGED",
        fetched_at=now,
    )


def create_test_supplier_states() -> SupplierStateStore:
    """Create supplier states with varying data completeness.
    
    Returns:
        SupplierStateStore with states for suppliers:
        - Complete data: full delivery history, lead times, defect rates
        - Incomplete data: missing optional fields
    """
    now = datetime.now()
    
    states = [
        # ===== COMPLETE DATA STATES =====
        
        # Premium Supplier - Excellent performance
        SupplierState(
            supplier_id="SUP-PREMIUM-001",
            supplier_name="Elite Components Manufacturing",
            product_id="PROD-001",
            product_name="Precision Circuit Board",
            total_deliveries=45,
            successful_deliveries=44,
            active_blanket_pos_count=2,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=5.2,
            average_defect_rate=0.02,  # 2% defect rate
            last_delivery_date=now - timedelta(days=3),
            metadata={"quality_cert": "ISO9001", "preferred": "true"},
        ),
        
        # Established Supplier - Reliable performance
        SupplierState(
            supplier_id="SUP-ESTABLISHED-002",
            supplier_name="Reliable Metals Corp",
            product_id="PROD-002",
            product_name="Steel Sheet",
            total_deliveries=120,
            successful_deliveries=118,
            active_blanket_pos_count=3,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=7.5,
            average_defect_rate=0.05,  # 5% defect rate
            last_delivery_date=now - timedelta(days=5),
            metadata={"volume_discount": "true"},
        ),
        
        # Budget Supplier - Acceptable performance
        SupplierState(
            supplier_id="SUP-BUDGET-003",
            supplier_name="Value Parts Distributors",
            product_id="PROD-003",
            product_name="Plastic Housing",
            total_deliveries=85,
            successful_deliveries=80,
            active_blanket_pos_count=1,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=12.3,
            average_defect_rate=0.08,  # 8% defect rate
            last_delivery_date=now - timedelta(days=8),
            metadata={"cost_effective": "true"},
        ),
        
        # Specialized Supplier - Good performance
        SupplierState(
            supplier_id="SUP-SPECIALIZED-004",
            supplier_name="Advanced Polymer Solutions",
            product_id="PROD-004",
            product_name="Custom Polymer Component",
            total_deliveries=28,
            successful_deliveries=27,
            active_blanket_pos_count=1,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=14.0,
            average_defect_rate=0.03,  # 3% defect rate
            last_delivery_date=now - timedelta(days=10),
            metadata={"custom": "true", "rd_partner": "true"},
        ),
        
        # Inactive Supplier - Historical data
        SupplierState(
            supplier_id="SUP-INACTIVE-005",
            supplier_name="Legacy Components Inc",
            product_id="PROD-005",
            product_name="Legacy Electronic Part",
            total_deliveries=200,
            successful_deliveries=195,
            active_blanket_pos_count=0,  # No active BPOs
            supplier_status=SupplierStatus.INACTIVE,
            average_lead_time_days=8.0,
            average_defect_rate=0.04,
            last_delivery_date=now - timedelta(days=180),  # 6 months ago
            metadata={"legacy": "true"},
        ),
        
        # ===== INCOMPLETE DATA STATES =====
        
        # New Supplier - No delivery history yet
        SupplierState(
            supplier_id="SUP-NEW-006",
            supplier_name="Innovation Materials Ltd",
            product_id="PROD-006",
            product_name="Composite Material",
            total_deliveries=0,
            successful_deliveries=0,
            active_blanket_pos_count=0,
            supplier_status=SupplierStatus.PENDING_APPROVAL,
            average_lead_time_days=None,  # No history
            average_defect_rate=None,  # No history
            last_delivery_date=None,  # No deliveries yet
            metadata={"new_supplier": "true"},
        ),
        
        # Emerging Supplier - Limited history, missing defect rate
        SupplierState(
            supplier_id="SUP-EMERGING-007",
            supplier_name="Rapid Supply Co",
            product_id="PROD-007",
            product_name="General Component",
            total_deliveries=5,
            successful_deliveries=5,
            active_blanket_pos_count=0,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=9.0,
            average_defect_rate=None,  # Not tracked yet
            last_delivery_date=now - timedelta(days=7),
            metadata={"emerging": "true"},
        ),
        
        # Regional Supplier - Missing lead time data
        SupplierState(
            supplier_id="SUP-REGIONAL-008",
            supplier_name="Regional Manufacturing Partners",
            product_id="PROD-008",
            product_name="Assembled Unit",
            total_deliveries=15,
            successful_deliveries=14,
            active_blanket_pos_count=1,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=None,  # Not consistently tracked
            average_defect_rate=0.06,
            last_delivery_date=now - timedelta(days=4),
            metadata={"regional": "true"},
        ),
        
        # International Supplier - Missing defect rate
        SupplierState(
            supplier_id="SUP-INTERNATIONAL-009",
            supplier_name="Global Sourcing Solutions",
            product_id="PROD-009",
            product_name="Sourced Component",
            total_deliveries=12,
            successful_deliveries=11,
            active_blanket_pos_count=0,
            supplier_status=SupplierStatus.ACTIVE,
            average_lead_time_days=21.5,  # Longer international lead time
            average_defect_rate=None,  # Not tracked for international
            last_delivery_date=now - timedelta(days=15),
            metadata={"international": "true", "long_lead_time": "true"},
        ),
        
        # Suspended Supplier - Complete but poor performance
        SupplierState(
            supplier_id="SUP-SUSPENDED-010",
            supplier_name="Troubled Parts Supply",
            product_id="PROD-010",
            product_name="General Part",
            total_deliveries=30,
            successful_deliveries=22,  # Poor success rate
            active_blanket_pos_count=0,
            supplier_status=SupplierStatus.SUSPENDED,
            average_lead_time_days=18.5,  # Often late
            average_defect_rate=0.15,  # High defect rate (15%)
            last_delivery_date=now - timedelta(days=45),  # No recent deliveries
            metadata={"suspended": "true", "quality_issues": "true"},
        ),
    ]
    
    return SupplierStateStore(
        states=states,
        built_at=now,
    )


def create_test_quotes() -> List[Quote]:
    """Create sample quotes from different suppliers.
    
    Returns:
        List of Quote objects from suppliers with varying data completeness
    """
    now = datetime.now()
    
    quotes = [
        # Quotes from complete data suppliers
        Quote(
            quote_id="Q-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-PREMIUM-001",
            supplier_name="Elite Components Manufacturing",
            material_id="MAT-001",
            material_name="Precision Circuit Board",
            unit_price=45.50,
            quantity=100,
            total_price=4550.00,
            lead_time_days=5,
            valid_until=now + timedelta(days=30),
            received_at=now - timedelta(days=1),
            status=QuoteStatus.ACCEPTED,
            terms="Net 30, FOB Destination",
        ),
        
        Quote(
            quote_id="Q-002",
            rfq_id="RFQ-002",
            supplier_id="SUP-ESTABLISHED-002",
            supplier_name="Reliable Metals Corp",
            material_id="MAT-002",
            material_name="Steel Sheet",
            unit_price=12.75,
            quantity=500,
            total_price=6375.00,
            lead_time_days=7,
            valid_until=now + timedelta(days=21),
            received_at=now - timedelta(days=2),
            status=QuoteStatus.ACCEPTED,
            terms="Net 30, Volume discount applied",
        ),
        
        Quote(
            quote_id="Q-003",
            rfq_id="RFQ-003",
            supplier_id="SUP-BUDGET-003",
            supplier_name="Value Parts Distributors",
            material_id="MAT-003",
            material_name="Plastic Housing",
            unit_price=3.25,
            quantity=200,
            total_price=650.00,
            lead_time_days=12,
            valid_until=now + timedelta(days=14),
            received_at=now - timedelta(days=1),
            status=QuoteStatus.UNDER_REVIEW,
            terms="Net 15",
        ),
        
        Quote(
            quote_id="Q-004",
            rfq_id="RFQ-004",
            supplier_id="SUP-SPECIALIZED-004",
            supplier_name="Advanced Polymer Solutions",
            material_id="MAT-004",
            material_name="Custom Polymer Component",
            unit_price=28.90,
            quantity=50,
            total_price=1445.00,
            lead_time_days=14,
            valid_until=now + timedelta(days=30),
            received_at=now - timedelta(days=3),
            status=QuoteStatus.ACCEPTED,
            terms="Net 30, Custom tooling included",
        ),
        
        # Quotes from incomplete data suppliers
        Quote(
            quote_id="Q-005",
            rfq_id="RFQ-005",
            supplier_id="SUP-NEW-006",
            supplier_name="Innovation Materials Ltd",
            material_id="MAT-005",
            material_name="Composite Material",
            unit_price=35.00,
            quantity=75,
            total_price=2625.00,
            lead_time_days=10,  # Estimated
            valid_until=now + timedelta(days=14),
            received_at=now - timedelta(days=1),
            status=QuoteStatus.UNDER_REVIEW,
            terms="Net 30, First order discount",
        ),
        
        Quote(
            quote_id="Q-006",
            rfq_id="RFQ-006",
            supplier_id="SUP-EMERGING-007",
            supplier_name="Rapid Supply Co",
            material_id="MAT-006",
            material_name="General Component",
            unit_price=8.50,
            quantity=150,
            total_price=1275.00,
            lead_time_days=9,
            valid_until=now + timedelta(days=21),
            received_at=now - timedelta(days=2),
            status=QuoteStatus.RECEIVED,
            terms="Net 20",
        ),
        
        Quote(
            quote_id="Q-007",
            rfq_id="RFQ-007",
            supplier_id="SUP-REGIONAL-008",
            supplier_name="Regional Manufacturing Partners",
            material_id="MAT-007",
            material_name="Assembled Unit",
            unit_price=22.00,
            quantity=100,
            total_price=2200.00,
            lead_time_days=6,  # Regional advantage
            valid_until=now + timedelta(days=14),
            received_at=now - timedelta(days=1),
            status=QuoteStatus.ACCEPTED,
            terms="Net 30, Local pickup available",
        ),
        
        Quote(
            quote_id="Q-008",
            rfq_id="RFQ-008",
            supplier_id="SUP-INTERNATIONAL-009",
            supplier_name="Global Sourcing Solutions",
            material_id="MAT-008",
            material_name="Sourced Component",
            unit_price=6.25,
            quantity=300,
            total_price=1875.00,
            lead_time_days=21,  # International shipping
            valid_until=now + timedelta(days=30),
            received_at=now - timedelta(days=3),
            status=QuoteStatus.UNDER_REVIEW,
            terms="Net 45, FOB Origin, Import duties extra",
        ),
    ]
    
    return quotes

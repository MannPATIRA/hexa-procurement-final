"""Mock Web Scanner implementation."""

from datetime import datetime
from typing import List
from web_scanner.interface import WebScannerInterface
from models.supplier_search import SupplierSearchResult, SupplierSearchStore


class MockWebScanner(WebScannerInterface):
    """Mock web scanner that returns predefined supplier results."""

    def __init__(self) -> None:
        """Initialize mock web scanner with predefined supplier data."""
        # Mock supplier database
        self._mock_suppliers = {
            "MAT-001": [  # Steel Component
                SupplierSearchResult(
                    supplier_id="WEB-SUP-001",
                    name="Global Steel Industries",
                    contact_email="sales@globalsteel.mock",
                    website="https://globalsteel.mock",
                    materials_offered=["MAT-001", "Steel Components", "Metal Parts"],
                    estimated_price_range=(4.50, 6.00),
                    estimated_lead_time_days=5,
                    certifications=["ISO 9001", "ISO 14001"],
                    rating=4.5,
                ),
                SupplierSearchResult(
                    supplier_id="WEB-SUP-002",
                    name="Premium Metals Co",
                    contact_email="quotes@premiummetals.mock",
                    website="https://premiummetals.mock",
                    materials_offered=["MAT-001", "Steel", "Aluminum"],
                    estimated_price_range=(5.00, 7.00),
                    estimated_lead_time_days=7,
                    certifications=["ISO 9001"],
                    rating=4.2,
                ),
                SupplierSearchResult(
                    supplier_id="WEB-SUP-003",
                    name="Quick Steel Supply",
                    contact_email="info@quicksteel.mock",
                    website="https://quicksteel.mock",
                    materials_offered=["MAT-001", "Steel Parts"],
                    estimated_price_range=(5.50, 8.00),
                    estimated_lead_time_days=3,
                    certifications=["ISO 9001", "AS9100"],
                    rating=4.0,
                ),
            ],
            "MAT-002": [  # Plastic Housing
                SupplierSearchResult(
                    supplier_id="WEB-SUP-004",
                    name="PlastiCorp International",
                    contact_email="rfq@plasticorp.mock",
                    website="https://plasticorp.mock",
                    materials_offered=["MAT-002", "Plastic Housings", "Enclosures"],
                    estimated_price_range=(2.00, 4.00),
                    estimated_lead_time_days=10,
                    certifications=["ISO 9001", "RoHS Compliant"],
                    rating=4.3,
                ),
                SupplierSearchResult(
                    supplier_id="WEB-SUP-005",
                    name="MoldMaster Inc",
                    contact_email="sales@moldmaster.mock",
                    website="https://moldmaster.mock",
                    materials_offered=["MAT-002", "Plastic Components"],
                    estimated_price_range=(2.50, 3.50),
                    estimated_lead_time_days=8,
                    certifications=["ISO 9001", "ISO 13485"],
                    rating=4.6,
                ),
            ],
            "MAT-003": [  # Electronic Circuit Board
                SupplierSearchResult(
                    supplier_id="WEB-SUP-006",
                    name="CircuitPro Electronics",
                    contact_email="quotes@circuitpro.mock",
                    website="https://circuitpro.mock",
                    materials_offered=["MAT-003", "PCBs", "Circuit Boards"],
                    estimated_price_range=(8.00, 15.00),
                    estimated_lead_time_days=14,
                    certifications=["ISO 9001", "IPC-A-610", "UL Listed"],
                    rating=4.7,
                ),
                SupplierSearchResult(
                    supplier_id="WEB-SUP-007",
                    name="TechBoard Solutions",
                    contact_email="rfq@techboard.mock",
                    website="https://techboard.mock",
                    materials_offered=["MAT-003", "Electronic Components"],
                    estimated_price_range=(10.00, 18.00),
                    estimated_lead_time_days=12,
                    certifications=["ISO 9001", "IATF 16949"],
                    rating=4.4,
                ),
            ],
            "MAT-004": [  # Rubber Gasket
                SupplierSearchResult(
                    supplier_id="WEB-SUP-008",
                    name="RubberSeal Corp",
                    contact_email="sales@rubberseal.mock",
                    website="https://rubberseal.mock",
                    materials_offered=["MAT-004", "Rubber Gaskets", "Seals"],
                    estimated_price_range=(0.50, 2.00),
                    estimated_lead_time_days=6,
                    certifications=["ISO 9001", "FDA Compliant"],
                    rating=4.1,
                ),
                SupplierSearchResult(
                    supplier_id="WEB-SUP-009",
                    name="GasketWorld Inc",
                    contact_email="info@gasketworld.mock",
                    website="https://gasketworld.mock",
                    materials_offered=["MAT-004", "Rubber Products"],
                    estimated_price_range=(0.75, 1.50),
                    estimated_lead_time_days=5,
                    certifications=["ISO 9001"],
                    rating=4.3,
                ),
            ],
        }

    def search_suppliers(self, material_ids: List[str], material_names: List[str]) -> SupplierSearchStore:
        """Search for suppliers that can provide the specified materials.
        
        Args:
            material_ids: List of material IDs to search for
            material_names: List of material names to use in search queries
            
        Returns:
            SupplierSearchStore containing all found suppliers
        """
        now = datetime.now()
        results: List[SupplierSearchResult] = []
        seen_suppliers: set = set()
        
        # Search by material ID
        for material_id in material_ids:
            if material_id in self._mock_suppliers:
                for supplier in self._mock_suppliers[material_id]:
                    if supplier.supplier_id not in seen_suppliers:
                        results.append(supplier)
                        seen_suppliers.add(supplier.supplier_id)
        
        # Build search query string for logging/tracking
        search_query = f"materials: {', '.join(material_names)}"
        
        return SupplierSearchStore(
            results=results,
            searched_at=now,
            search_query=search_query,
        )


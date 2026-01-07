"""Web Scanner interface."""

from abc import ABC, abstractmethod
from typing import List
from models.supplier_search import SupplierSearchStore


class WebScannerInterface(ABC):
    """Interface for searching suppliers on the web."""

    @abstractmethod
    def search_suppliers(self, material_ids: List[str], material_names: List[str]) -> SupplierSearchStore:
        """Search for suppliers that can provide the specified materials.
        
        Args:
            material_ids: List of material IDs to search for
            material_names: List of material names to use in search queries
            
        Returns:
            SupplierSearchStore containing all found suppliers
        """
        pass


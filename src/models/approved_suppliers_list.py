"""Approved suppliers data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class SupplierStatus(str, Enum):
    """Supplier status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class Supplier:
    """Represents a single approved supplier."""

    supplier_id: str
    supplier_name: str
    contact_email: str
    contact_phone: Optional[str]
    status: SupplierStatus
    approved_date: datetime
    categories: List[str]  # Product/service categories
    rating: Optional[float] = None  # 0.0 to 5.0
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate supplier data."""
        if not self.categories:
            raise ValueError("Supplier must have at least one category")
        if self.rating is not None and not (0.0 <= self.rating <= 5.0):
            raise ValueError("Rating must be between 0.0 and 5.0")


@dataclass(frozen=True)
class ApprovedSuppliersList:
    """Represents approved suppliers list from ERP and CRM systems."""

    suppliers: List[Supplier]
    source: str  # "ERP" or "CRM" or "MERGED"
    fetched_at: datetime

    def __post_init__(self) -> None:
        """Validate approved suppliers list."""
        if self.fetched_at > datetime.now():
            raise ValueError("Fetched timestamp cannot be in the future")
        if self.source not in ["ERP", "CRM", "MERGED"]:
            raise ValueError("Source must be 'ERP', 'CRM', or 'MERGED'")


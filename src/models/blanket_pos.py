"""Blanket purchase orders data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class BlanketPOStatus(str, Enum):
    """Blanket PO status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class BlanketPO:
    """Represents a single blanket purchase order."""

    blanket_po_id: str
    supplier_id: str
    supplier_name: str
    product_id: str
    product_name: str
    total_quantity: int
    remaining_quantity: int
    unit_price: float
    start_date: datetime
    end_date: datetime
    status: BlanketPOStatus
    terms: Optional[str] = None

@dataclass(frozen=True)
class BlanketPOs:
    """Represents blanket purchase orders from CRM system."""

    blanket_pos: List[BlanketPO]
    fetched_at: datetime



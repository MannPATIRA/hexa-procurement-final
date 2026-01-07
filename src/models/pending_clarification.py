"""Pending clarification data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ClarificationPriority(str, Enum):
    """Clarification priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ClarificationStatus(str, Enum):
    """Clarification status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESPONDED = "responded"
    CLOSED = "closed"


@dataclass(frozen=True)
class PendingClarification:
    """Represents a clarification question that needs human review."""

    clarification_id: str
    original_email_id: str
    rfq_id: str
    supplier_id: str
    supplier_name: str
    supplier_email: str
    question_text: str
    priority: ClarificationPriority
    created_at: datetime
    status: ClarificationStatus = ClarificationStatus.PENDING
    assigned_to: Optional[str] = None
    response_text: Optional[str] = None
    responded_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PendingClarificationQueue:
    """Queue of pending clarifications awaiting human review."""

    items: List[PendingClarification]
    updated_at: datetime
    items_by_id: Dict[str, PendingClarification] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Build index by clarification_id."""
        index = {item.clarification_id: item for item in self.items}
        object.__setattr__(self, 'items_by_id', index)

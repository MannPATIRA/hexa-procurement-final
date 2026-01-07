"""Classification result data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ReplyType(str, Enum):
    """Type of reply from supplier."""

    QUOTE = "quote"
    CLARIFICATION_SIMPLE = "clarification_simple"
    CLARIFICATION_COMPLEX = "clarification_complex"
    REJECTION = "rejection"
    OUT_OF_OFFICE = "out_of_office"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying an email reply."""

    reply_type: ReplyType
    confidence: float  # 0.0 to 1.0
    extracted_data: Dict[str, str] = field(default_factory=dict)
    reasoning: Optional[str] = None
    classified_at: datetime = field(default_factory=datetime.now)


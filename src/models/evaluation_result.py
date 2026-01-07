"""Evaluation result data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating a quote against current suppliers."""

    quote_id: str
    overall_score: float  # 0.0 to 100.0
    price_score: float  # 0.0 to 100.0
    lead_time_score: float  # 0.0 to 100.0
    reliability_score: float  # 0.0 to 100.0
    is_better_than_current: bool
    current_supplier_score: Optional[float] = None
    improvement_percentage: Optional[float] = None
    recommendation: str = ""
    evaluated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, str] = field(default_factory=dict)


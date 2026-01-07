"""Basic Quote Evaluator implementation."""

from datetime import datetime
from typing import Optional
from quote_evaluator.interface import QuoteEvaluatorInterface
from models.quote import Quote
from models.supplier_state import SupplierStateStore, SupplierState
from models.evaluation_result import EvaluationResult


class BasicQuoteEvaluator(QuoteEvaluatorInterface):
    """Basic quote evaluator using comprehensive scoring.
    
    Scoring weights:
    - Price: 40%
    - Lead time: 30%
    - Supplier reliability: 30%
    """

    def __init__(
        self,
        price_weight: float = 0.4,
        lead_time_weight: float = 0.3,
        reliability_weight: float = 0.3,
    ) -> None:
        """Initialize evaluator with scoring weights.
        
        Args:
            price_weight: Weight for price score (default 40%)
            lead_time_weight: Weight for lead time score (default 30%)
            reliability_weight: Weight for reliability score (default 30%)
        """
        # Normalize weights
        total = price_weight + lead_time_weight + reliability_weight
        self.price_weight = price_weight / total
        self.lead_time_weight = lead_time_weight / total
        self.reliability_weight = reliability_weight / total

    def evaluate(
        self,
        quote: Quote,
        supplier_state_store: SupplierStateStore,
        current_unit_price: float,
        current_lead_time_days: int,
    ) -> EvaluationResult:
        """Evaluate a quote against current supplier performance.
        
        Calculates scores for price, lead time, and reliability, then
        computes an overall score to determine if the quote is better
        than current suppliers.
        
        Args:
            quote: Quote to evaluate
            supplier_state_store: Current supplier performance data
            current_unit_price: Current unit price for the material
            current_lead_time_days: Current lead time for the material
            
        Returns:
            EvaluationResult with scores and recommendation
        """
        now = datetime.now()
        
        # Calculate price score (lower is better)
        price_score = self._calculate_price_score(quote.unit_price, current_unit_price)
        
        # Calculate lead time score (lower is better)
        lead_time_score = self._calculate_lead_time_score(
            quote.lead_time_days, current_lead_time_days
        )
        
        # Calculate reliability score for the quoting supplier
        reliability_score = self._calculate_reliability_score(
            quote.supplier_id, supplier_state_store
        )
        
        # Calculate overall score
        overall_score = (
            price_score * self.price_weight +
            lead_time_score * self.lead_time_weight +
            reliability_score * self.reliability_weight
        )
        
        # Calculate current supplier score for comparison
        current_reliability = self._get_current_supplier_reliability(supplier_state_store)
        current_supplier_score = (
            50.0 * self.price_weight +  # Baseline price score
            50.0 * self.lead_time_weight +  # Baseline lead time score
            current_reliability * self.reliability_weight
        )
        
        # Determine if quote is better
        is_better = overall_score > current_supplier_score
        
        # Calculate improvement percentage
        if current_supplier_score > 0:
            improvement = ((overall_score - current_supplier_score) / current_supplier_score) * 100
        else:
            improvement = 0.0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_score, current_supplier_score, price_score, lead_time_score, reliability_score
        )
        
        return EvaluationResult(
            quote_id=quote.quote_id,
            overall_score=overall_score,
            price_score=price_score,
            lead_time_score=lead_time_score,
            reliability_score=reliability_score,
            is_better_than_current=is_better,
            current_supplier_score=current_supplier_score,
            improvement_percentage=improvement,
            recommendation=recommendation,
            evaluated_at=now,
        )

    def _calculate_price_score(self, quote_price: float, current_price: float) -> float:
        """Calculate price score (0-100). Higher score = better price.
        
        Args:
            quote_price: Price from quote
            current_price: Current/baseline price
            
        Returns:
            Score from 0-100
        """
        if current_price <= 0:
            return 50.0  # Neutral score if no baseline
        
        if quote_price <= 0:
            return 0.0
        
        # Calculate percentage difference
        price_ratio = quote_price / current_price
        
        # Convert to score: 50% price = 100 score, 100% price = 50 score, 150% price = 0 score
        if price_ratio <= 0.5:
            return 100.0
        elif price_ratio >= 1.5:
            return 0.0
        else:
            # Linear interpolation
            return 100.0 - ((price_ratio - 0.5) * 100.0)

    def _calculate_lead_time_score(
        self, quote_lead_time: int, current_lead_time: int
    ) -> float:
        """Calculate lead time score (0-100). Higher score = better (shorter) lead time.
        
        Args:
            quote_lead_time: Lead time from quote (days)
            current_lead_time: Current/baseline lead time (days)
            
        Returns:
            Score from 0-100
        """
        if current_lead_time <= 0:
            return 50.0  # Neutral score if no baseline
        
        if quote_lead_time <= 0:
            return 100.0  # Immediate delivery is best
        
        # Calculate ratio
        time_ratio = quote_lead_time / current_lead_time
        
        # Convert to score: 50% lead time = 100 score, 100% = 50 score, 200% = 0 score
        if time_ratio <= 0.5:
            return 100.0
        elif time_ratio >= 2.0:
            return 0.0
        else:
            # Linear interpolation
            return 100.0 - ((time_ratio - 0.5) * 66.67)

    def _calculate_reliability_score(
        self, supplier_id: str, supplier_state_store: SupplierStateStore
    ) -> float:
        """Calculate supplier reliability score (0-100).
        
        Args:
            supplier_id: Supplier to evaluate
            supplier_state_store: Supplier performance data
            
        Returns:
            Score from 0-100
        """
        # Find supplier states for this supplier
        supplier_states = [
            s for s in supplier_state_store.states
            if s.supplier_id == supplier_id
        ]
        
        if not supplier_states:
            # New supplier, give neutral score
            return 50.0
        
        # Calculate average success rate across all products
        total_deliveries = sum(s.total_deliveries for s in supplier_states)
        successful_deliveries = sum(s.successful_deliveries for s in supplier_states)
        
        if total_deliveries == 0:
            return 50.0
        
        success_rate = (successful_deliveries / total_deliveries) * 100.0
        return success_rate

    def _get_current_supplier_reliability(
        self, supplier_state_store: SupplierStateStore
    ) -> float:
        """Get average reliability of current suppliers.
        
        Args:
            supplier_state_store: Supplier performance data
            
        Returns:
            Average reliability score
        """
        if not supplier_state_store.states:
            return 50.0
        
        total_deliveries = sum(s.total_deliveries for s in supplier_state_store.states)
        successful_deliveries = sum(s.successful_deliveries for s in supplier_state_store.states)
        
        if total_deliveries == 0:
            return 50.0
        
        return (successful_deliveries / total_deliveries) * 100.0

    def _generate_recommendation(
        self,
        overall_score: float,
        current_score: float,
        price_score: float,
        lead_time_score: float,
        reliability_score: float,
    ) -> str:
        """Generate a recommendation based on scores.
        
        Args:
            overall_score: Overall quote score
            current_score: Current supplier score
            price_score: Price component score
            lead_time_score: Lead time component score
            reliability_score: Reliability component score
            
        Returns:
            Recommendation string
        """
        if overall_score > current_score + 10:
            rec = "STRONGLY RECOMMEND: Quote significantly outperforms current suppliers."
        elif overall_score > current_score:
            rec = "RECOMMEND: Quote is better than current suppliers."
        elif overall_score >= current_score - 5:
            rec = "CONSIDER: Quote is comparable to current suppliers."
        else:
            rec = "NOT RECOMMENDED: Current suppliers are more favorable."
        
        # Add specific insights
        insights = []
        if price_score >= 70:
            insights.append("Excellent pricing")
        elif price_score < 40:
            insights.append("Price is higher than target")
        
        if lead_time_score >= 70:
            insights.append("Fast delivery")
        elif lead_time_score < 40:
            insights.append("Longer lead time")
        
        if reliability_score >= 70:
            insights.append("Reliable supplier")
        elif reliability_score < 40:
            insights.append("Limited reliability data")
        
        if insights:
            rec += f" ({'; '.join(insights)})"
        
        return rec


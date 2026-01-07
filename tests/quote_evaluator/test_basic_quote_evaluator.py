"""Test cases for BasicQuoteEvaluator."""

from datetime import datetime, timedelta
from quote_evaluator.basic_quote_evaluator import BasicQuoteEvaluator
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.quote import Quote, QuoteStatus
from models.evaluation_result import EvaluationResult


def _create_test_quote(unit_price: float = 5.0, lead_time_days: int = 7):
    """Create a test quote."""
    now = datetime.now()
    return Quote(
        quote_id="QUOTE-TEST-001",
        rfq_id="RFQ-TEST-001",
        supplier_id="SUP-001",
        supplier_name="Test Supplier",
        material_id="MAT-001",
        material_name="Steel Component",
        unit_price=unit_price,
        quantity=100,
        total_price=unit_price * 100,
        lead_time_days=lead_time_days,
        valid_until=now + timedelta(days=30),
        received_at=now,
        status=QuoteStatus.RECEIVED,
    )


def _get_supplier_state_store():
    """Get supplier state store from mock data."""
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    supplier_calculator = BasicSupplierStateCalculator()
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    
    return supplier_calculator.calculate_supplier_state(
        delivery_history, approved_suppliers, blanket_pos
    )


def test_evaluate_returns_evaluation_result():
    """Test that evaluate returns an EvaluationResult."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    assert isinstance(result, EvaluationResult)


def test_evaluate_has_quote_id():
    """Test that result references the quote."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    assert result.quote_id == quote.quote_id


def test_evaluate_has_scores():
    """Test that result contains all score components."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    
    assert 0 <= result.price_score <= 100
    assert 0 <= result.lead_time_score <= 100
    assert 0 <= result.reliability_score <= 100
    assert 0 <= result.overall_score <= 100


def test_evaluate_better_price_higher_score():
    """Test that better price yields higher score."""
    evaluator = BasicQuoteEvaluator()
    supplier_state_store = _get_supplier_state_store()
    
    # Quote with price lower than current
    cheap_quote = _create_test_quote(unit_price=5.0)
    cheap_result = evaluator.evaluate(
        cheap_quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=7
    )
    
    # Quote with price higher than current
    expensive_quote = _create_test_quote(unit_price=15.0)
    expensive_result = evaluator.evaluate(
        expensive_quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=7
    )
    
    assert cheap_result.price_score > expensive_result.price_score


def test_evaluate_faster_lead_time_higher_score():
    """Test that faster lead time yields higher score."""
    evaluator = BasicQuoteEvaluator()
    supplier_state_store = _get_supplier_state_store()
    
    # Quote with faster lead time
    fast_quote = _create_test_quote(lead_time_days=3)
    fast_result = evaluator.evaluate(
        fast_quote, supplier_state_store, current_unit_price=5.0, current_lead_time_days=10
    )
    
    # Quote with slower lead time
    slow_quote = _create_test_quote(lead_time_days=20)
    slow_result = evaluator.evaluate(
        slow_quote, supplier_state_store, current_unit_price=5.0, current_lead_time_days=10
    )
    
    assert fast_result.lead_time_score > slow_result.lead_time_score


def test_evaluate_is_better_than_current():
    """Test that better quote is flagged as better."""
    evaluator = BasicQuoteEvaluator()
    supplier_state_store = _get_supplier_state_store()
    
    # Quote that's significantly better
    better_quote = _create_test_quote(unit_price=3.0, lead_time_days=3)
    result = evaluator.evaluate(
        better_quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14
    )
    
    assert result.is_better_than_current is True


def test_evaluate_worse_quote_not_better():
    """Test that worse quote is not flagged as better."""
    evaluator = BasicQuoteEvaluator()
    supplier_state_store = _get_supplier_state_store()
    
    # Quote that's significantly worse
    worse_quote = _create_test_quote(unit_price=20.0, lead_time_days=30)
    result = evaluator.evaluate(
        worse_quote, supplier_state_store, current_unit_price=5.0, current_lead_time_days=7
    )
    
    assert result.is_better_than_current is False


def test_evaluate_has_improvement_percentage():
    """Test that result includes improvement percentage."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    
    assert result.improvement_percentage is not None


def test_evaluate_has_recommendation():
    """Test that result includes recommendation."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    
    assert result.recommendation
    assert len(result.recommendation) > 0


def test_evaluate_custom_weights():
    """Test evaluator with custom weights."""
    # Price-only evaluator
    price_evaluator = BasicQuoteEvaluator(price_weight=1.0, lead_time_weight=0.0, reliability_weight=0.0)
    
    quote = _create_test_quote(unit_price=3.0, lead_time_days=30)
    supplier_state_store = _get_supplier_state_store()
    
    result = price_evaluator.evaluate(
        quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=7
    )
    
    # With price-only weighting, good price should dominate
    assert result.overall_score > 50


def test_evaluate_has_timestamp():
    """Test that result has evaluation timestamp."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    
    assert result.evaluated_at is not None


def test_evaluate_current_supplier_score():
    """Test that result includes current supplier score for comparison."""
    evaluator = BasicQuoteEvaluator()
    quote = _create_test_quote()
    supplier_state_store = _get_supplier_state_store()
    
    result = evaluator.evaluate(quote, supplier_state_store, current_unit_price=10.0, current_lead_time_days=14)
    
    assert result.current_supplier_score is not None


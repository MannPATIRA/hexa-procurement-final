"""Test cases for MockReplyClassifier."""

from datetime import datetime
from reply_classifier.mock_reply_classifier import MockReplyClassifier
from models.email_message import EmailReply
from models.classification_result import ClassificationResult, ReplyType


def _create_quote_reply():
    """Create a reply that looks like a quote."""
    return EmailReply(
        reply_id="REPLY-001",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="""Dear Procurement Team,

Thank you for your RFQ. Here is our quote:

QUOTE DETAILS:
Unit Price: $5.50
Quantity: 100 units
Total Price: $550.00
Lead Time: 7 days
Quote Valid Until: 2025-02-15

Terms: Net 30, FOB Destination

Best regards,
Sales Team
""",
        received_at=datetime.now(),
    )


def _create_simple_clarification_reply():
    """Create a reply with a simple clarification question."""
    return EmailReply(
        reply_id="REPLY-002",
        original_email_id="EMAIL-002",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="""Dear Procurement Team,

Thank you for your RFQ. Before we can provide a quote, we have a quick question:

Could you please confirm the delivery address for this order?

Once we have this information, we will promptly send our quote.

Best regards,
Sales Team
""",
        received_at=datetime.now(),
    )


def _create_complex_clarification_reply():
    """Create a reply with complex clarification questions."""
    return EmailReply(
        reply_id="REPLY-003",
        original_email_id="EMAIL-003",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="""Dear Procurement Team,

We have several questions that need clarification before we can provide a quote:

1. Technical specifications - could you clarify the tolerance requirements?
2. We would like to schedule a technical discussion with your engineering team.
3. Our payment arrangements require a letter of credit for new customers.
4. We have multiple material grade options available.

Please let us know when would be a good time for a call to discuss these points.

Best regards,
Technical Sales Team
""",
        received_at=datetime.now(),
    )


def test_classify_returns_classification_result():
    """Test that classify returns a ClassificationResult."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    assert isinstance(result, ClassificationResult)


def test_classify_quote_reply():
    """Test classification of a quote reply."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    assert result.reply_type == ReplyType.QUOTE


def test_classify_simple_clarification():
    """Test classification of a simple clarification."""
    classifier = MockReplyClassifier()
    reply = _create_simple_clarification_reply()
    
    result = classifier.classify(reply)
    assert result.reply_type == ReplyType.CLARIFICATION_SIMPLE


def test_classify_complex_clarification():
    """Test classification of a complex clarification."""
    classifier = MockReplyClassifier()
    reply = _create_complex_clarification_reply()
    
    result = classifier.classify(reply)
    assert result.reply_type == ReplyType.CLARIFICATION_COMPLEX


def test_classify_has_confidence():
    """Test that classification includes confidence score."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    assert 0.0 <= result.confidence <= 1.0


def test_classify_has_reasoning():
    """Test that classification includes reasoning."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    assert result.reasoning is not None
    assert len(result.reasoning) > 0


def test_classify_quote_extracts_price():
    """Test that quote classification extracts price data."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    # Should extract price from the email
    if result.reply_type == ReplyType.QUOTE:
        assert "price" in result.extracted_data or len(result.extracted_data) > 0


def test_classify_uses_hint_metadata():
    """Test that classifier uses hint metadata if available."""
    classifier = MockReplyClassifier()
    
    reply_with_hint = EmailReply(
        reply_id="REPLY-HINT",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Generic reply without clear indicators.",
        received_at=datetime.now(),
        metadata={"reply_type_hint": "quote"},
    )
    
    result = classifier.classify(reply_with_hint)
    # Hint should boost quote classification
    assert result.reply_type == ReplyType.QUOTE


def test_classify_out_of_office():
    """Test classification of out-of-office reply."""
    classifier = MockReplyClassifier()
    
    ooo_reply = EmailReply(
        reply_id="REPLY-OOO",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Out of Office Auto-Reply",
        body="""I am currently out of the office and will return on January 15th.

For urgent matters, please contact support@company.mock.

Thank you.""",
        received_at=datetime.now(),
    )
    
    result = classifier.classify(ooo_reply)
    assert result.reply_type == ReplyType.OUT_OF_OFFICE


def test_classify_rejection():
    """Test classification of rejection reply."""
    classifier = MockReplyClassifier()
    
    rejection_reply = EmailReply(
        reply_id="REPLY-REJ",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="""Dear Procurement Team,

We regret to inform you that we are unable to quote on this item.
We no longer manufacture this type of component.

Best regards,
Sales Team
""",
        received_at=datetime.now(),
    )
    
    result = classifier.classify(rejection_reply)
    assert result.reply_type == ReplyType.REJECTION


def test_classify_unknown():
    """Test classification of ambiguous reply."""
    classifier = MockReplyClassifier()
    
    vague_reply = EmailReply(
        reply_id="REPLY-VAGUE",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Thanks for reaching out.",
        received_at=datetime.now(),
    )
    
    result = classifier.classify(vague_reply)
    # Should have low confidence or unknown type
    assert result.confidence < 0.5 or result.reply_type == ReplyType.UNKNOWN


def test_classify_has_timestamp():
    """Test that classification result has timestamp."""
    classifier = MockReplyClassifier()
    reply = _create_quote_reply()
    
    result = classifier.classify(reply)
    assert result.classified_at is not None


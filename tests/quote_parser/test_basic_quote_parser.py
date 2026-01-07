"""Test cases for BasicQuoteParser."""

from datetime import datetime, timedelta
from quote_parser.basic_quote_parser import BasicQuoteParser
from models.email_message import EmailReply
from models.rfq import RFQ, RFQStatus
from models.quote import Quote, QuoteStatus


def _create_test_rfq():
    """Create a test RFQ."""
    now = datetime.now()
    return RFQ(
        rfq_id="RFQ-TEST-001",
        material_id="MAT-001",
        material_name="Steel Component",
        quantity=100,
        required_delivery_date=now + timedelta(days=14),
        supplier_id="SUP-001",
        supplier_name="Test Supplier",
        supplier_email="test@supplier.mock",
        terms="Net 30",
        status=RFQStatus.SENT,
        created_at=now,
    )


def _create_quote_reply():
    """Create a reply containing a quote."""
    return EmailReply(
        reply_id="REPLY-001",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="""Dear Procurement Team,

Thank you for your RFQ. Here is our quote:

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


def test_parse_returns_quote():
    """Test that parse returns a Quote object."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert isinstance(result, Quote)


def test_parse_extracts_unit_price():
    """Test that parser extracts unit price."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.unit_price == 5.50


def test_parse_extracts_quantity():
    """Test that parser extracts quantity."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.quantity == 100


def test_parse_extracts_total_price():
    """Test that parser extracts or calculates total price."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.total_price == 550.00


def test_parse_extracts_lead_time():
    """Test that parser extracts lead time."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.lead_time_days == 7


def test_parse_has_rfq_reference():
    """Test that quote references the original RFQ."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.rfq_id == rfq.rfq_id


def test_parse_has_supplier_info():
    """Test that quote contains supplier information."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.supplier_id == rfq.supplier_id
    assert result.supplier_name == rfq.supplier_name


def test_parse_has_material_info():
    """Test that quote contains material information."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.material_id == rfq.material_id
    assert result.material_name == rfq.material_name


def test_parse_has_received_timestamp():
    """Test that quote has received timestamp."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.received_at == reply.received_at


def test_parse_status_is_received():
    """Test that parsed quote has RECEIVED status."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.status == QuoteStatus.RECEIVED


def test_parse_has_valid_until():
    """Test that quote has validity date."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    assert result.valid_until is not None


def test_parse_extracts_terms():
    """Test that parser extracts terms if available."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    reply = _create_quote_reply()
    
    result = parser.parse(reply, rfq)
    # Should extract Net 30 and/or FOB terms
    if result.terms:
        assert "net 30" in result.terms.lower() or "fob" in result.terms.lower()


def test_parse_per_unit_price_format():
    """Test parsing price in '$X per unit' format."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    
    reply = EmailReply(
        reply_id="REPLY-002",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="We can offer this at $8.25 per unit with 10 days lead time.",
        received_at=datetime.now(),
    )
    
    result = parser.parse(reply, rfq)
    assert result.unit_price == 8.25


def test_parse_uses_rfq_quantity_as_default():
    """Test that parser uses RFQ quantity when not specified in reply."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    
    reply = EmailReply(
        reply_id="REPLY-003",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Unit Price: $10.00. Lead Time: 5 days.",
        received_at=datetime.now(),
    )
    
    result = parser.parse(reply, rfq)
    assert result.quantity == rfq.quantity


def test_parse_calculates_total_when_missing():
    """Test that parser calculates total price when not provided."""
    parser = BasicQuoteParser()
    rfq = _create_test_rfq()
    
    reply = EmailReply(
        reply_id="REPLY-004",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Unit Price: $5.00 for 100 units. Lead Time: 7 days.",
        received_at=datetime.now(),
    )
    
    result = parser.parse(reply, rfq)
    assert result.total_price == result.unit_price * result.quantity


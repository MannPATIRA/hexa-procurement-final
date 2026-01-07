"""Test cases for BasicAutoResponder."""

from datetime import datetime, timedelta
from auto_responder.basic_auto_responder import BasicAutoResponder
from models.email_message import EmailReply, Email, EmailStatus
from models.rfq import RFQ, RFQStatus


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


def _create_delivery_address_reply():
    """Create a reply asking about delivery address."""
    return EmailReply(
        reply_id="REPLY-001",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Could you please confirm the delivery address for this order?",
        received_at=datetime.now(),
    )


def _create_packaging_reply():
    """Create a reply asking about packaging."""
    return EmailReply(
        reply_id="REPLY-002",
        original_email_id="EMAIL-002",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Is there a specific packaging requirement we should follow?",
        received_at=datetime.now(),
    )


def _create_certification_reply():
    """Create a reply asking about certifications."""
    return EmailReply(
        reply_id="REPLY-003",
        original_email_id="EMAIL-003",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Do you require any specific certifications with this shipment?",
        received_at=datetime.now(),
    )


def test_respond_returns_email():
    """Test that respond returns an Email object."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    assert isinstance(result, Email)


def test_respond_has_correct_addresses():
    """Test that response has correct to and from addresses."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    assert result.to_address == reply.from_address
    assert result.from_address == "procurement@company.mock"


def test_respond_has_subject():
    """Test that response has a reply subject."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    assert result.subject.startswith("Re:")


def test_respond_has_body():
    """Test that response has body content."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    assert result.body
    assert len(result.body) > 50


def test_respond_delivery_address_question():
    """Test response to delivery address question."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    # Should contain address information
    assert "delivery" in result.body.lower() or "address" in result.body.lower()


def test_respond_packaging_question():
    """Test response to packaging question."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_packaging_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    # Should contain packaging information
    assert "packag" in result.body.lower()


def test_respond_certification_question():
    """Test response to certification question."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_certification_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    # Should contain certification information
    assert "certif" in result.body.lower()


def test_respond_has_rfq_reference():
    """Test that response references the RFQ."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    assert result.rfq_id == rfq.rfq_id


def test_respond_status_is_draft():
    """Test that response email has DRAFT status."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    reply = _create_delivery_address_reply()
    
    result = responder.respond(reply, rfq, "procurement@company.mock")
    
    assert result.status == EmailStatus.DRAFT


def test_respond_generic_question():
    """Test response to generic question."""
    responder = BasicAutoResponder()
    rfq = _create_test_rfq()
    
    generic_reply = EmailReply(
        reply_id="REPLY-GEN",
        original_email_id="EMAIL-001",
        from_address="sales@supplier.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="We need more information before we can quote.",
        received_at=datetime.now(),
    )
    
    result = responder.respond(generic_reply, rfq, "procurement@company.mock")
    
    # Should contain material info in generic response
    assert rfq.material_name in result.body or rfq.material_id in result.body


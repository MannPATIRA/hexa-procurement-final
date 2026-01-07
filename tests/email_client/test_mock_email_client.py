"""Test cases for MockEmailClient."""

from datetime import datetime, timedelta
import uuid
from email_client.mock_email_client import MockEmailClient, clear_mock_email_storage, get_mock_email_storage
from models.rfq import RFQ, RFQStore, RFQStatus
from models.email_message import Email, EmailStatus


def _create_test_rfq():
    """Create a test RFQ for testing."""
    now = datetime.now()
    return RFQ(
        rfq_id=f"RFQ-{uuid.uuid4().hex[:8].upper()}",
        material_id="MAT-001",
        material_name="Steel Component",
        quantity=100,
        required_delivery_date=now + timedelta(days=14),
        supplier_id="SUP-001",
        supplier_name="Test Supplier",
        supplier_email="test@supplier.mock",
        terms="Net 30, FOB Destination",
        status=RFQStatus.DRAFT,
        created_at=now,
        valid_until=now + timedelta(days=14),
    )


def test_send_rfqs_returns_emails():
    """Test that send_rfqs returns a list of Email objects."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Email)


def test_send_rfqs_has_correct_status():
    """Test that sent emails have SENT status."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert email.status == EmailStatus.SENT


def test_send_rfqs_has_correct_addresses():
    """Test that emails have correct sender and recipient addresses."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    from_address = "procurement@company.mock"
    
    result = client.send_rfqs(rfq_store, from_address)
    
    for email in result:
        assert email.from_address == from_address
        assert email.to_address == rfq.supplier_email


def test_send_rfqs_has_rfq_reference():
    """Test that emails reference the RFQ ID."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert email.rfq_id == rfq.rfq_id


def test_send_rfqs_has_subject():
    """Test that emails have meaningful subjects."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert email.subject
        assert "Request for Quote" in email.subject or "RFQ" in email.subject


def test_send_rfqs_has_body():
    """Test that emails have body content."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert email.body
        assert len(email.body) > 100  # Should have substantial content


def test_send_rfqs_body_contains_material_info():
    """Test that email body contains material information."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert rfq.material_name in email.body
        assert str(rfq.quantity) in email.body


def test_send_rfqs_stores_in_global_storage():
    """Test that sent emails are stored in global mock storage."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    storage = get_mock_email_storage()
    assert len(storage) == 1
    assert result[0].email_id in storage


def test_send_rfqs_multiple_rfqs():
    """Test sending multiple RFQs at once."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfqs = [_create_test_rfq() for _ in range(3)]
    rfq_store = RFQStore(rfqs=rfqs, created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    assert len(result) == 3
    storage = get_mock_email_storage()
    assert len(storage) == 3


def test_send_email_updates_status():
    """Test that sending individual email updates its status."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    email = Email(
        email_id=f"EMAIL-{uuid.uuid4().hex[:8].upper()}",
        to_address="recipient@test.mock",
        from_address="sender@test.mock",
        subject="Test Subject",
        body="Test body content.",
        sent_at=None,
        status=EmailStatus.DRAFT,
    )
    
    result = client.send_email(email)
    
    assert result.status == EmailStatus.SENT
    assert result.sent_at is not None


def test_send_rfqs_has_sent_timestamp():
    """Test that sent emails have a sent timestamp."""
    clear_mock_email_storage()
    client = MockEmailClient()
    
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    
    result = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    for email in result:
        assert email.sent_at is not None
        assert email.sent_at <= datetime.now()


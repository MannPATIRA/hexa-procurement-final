"""Test cases for MockEmailListener."""

from datetime import datetime, timedelta
import uuid
from email_listener.mock_email_listener import MockEmailListener
from email_client.mock_email_client import MockEmailClient, clear_mock_email_storage
from models.rfq import RFQ, RFQStore, RFQStatus
from models.email_message import EmailReply


def _create_test_rfq():
    """Create a test RFQ."""
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
        terms="Net 30",
        status=RFQStatus.DRAFT,
        created_at=now,
        valid_until=now + timedelta(days=14),
    )


def test_get_replies_returns_list():
    """Test that get_replies returns a list."""
    clear_mock_email_storage()
    listener = MockEmailListener(auto_generate_replies=False)
    
    result = listener.get_replies()
    assert isinstance(result, list)


def test_get_replies_auto_generates_for_sent_emails():
    """Test that replies are auto-generated for sent emails."""
    clear_mock_email_storage()
    
    # Send an email first
    client = MockEmailClient()
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    client.send_rfqs(rfq_store, "procurement@company.mock")
    
    # Now listen for replies
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    assert len(replies) == 1
    assert isinstance(replies[0], EmailReply)


def test_get_replies_has_correct_structure():
    """Test that generated replies have correct structure."""
    clear_mock_email_storage()
    
    client = MockEmailClient()
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    sent_emails = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    for reply in replies:
        assert reply.reply_id
        assert reply.original_email_id
        assert reply.from_address
        assert reply.to_address
        assert reply.subject
        assert reply.body


def test_get_replies_references_original_email():
    """Test that replies reference the original email."""
    clear_mock_email_storage()
    
    client = MockEmailClient()
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    sent_emails = client.send_rfqs(rfq_store, "procurement@company.mock")
    
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    assert replies[0].original_email_id == sent_emails[0].email_id


def test_mark_processed_removes_from_pending():
    """Test that marking as processed removes from pending replies."""
    clear_mock_email_storage()
    
    client = MockEmailClient()
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    client.send_rfqs(rfq_store, "procurement@company.mock")
    
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    assert len(replies) == 1
    reply_id = replies[0].reply_id
    
    # Mark as processed
    listener.mark_processed(reply_id)
    
    # Should not appear in subsequent calls
    remaining = listener.get_replies()
    assert len(remaining) == 0


def test_add_manual_reply():
    """Test adding a manual reply for testing."""
    clear_mock_email_storage()
    listener = MockEmailListener(auto_generate_replies=False)
    
    manual_reply = EmailReply(
        reply_id="TEST-REPLY-001",
        original_email_id="EMAIL-001",
        from_address="supplier@test.mock",
        to_address="procurement@company.mock",
        subject="Re: RFQ",
        body="Here is our quote: $10 per unit",
        received_at=datetime.now(),
    )
    
    listener.add_manual_reply(manual_reply)
    replies = listener.get_replies()
    
    assert len(replies) == 1
    assert replies[0].reply_id == "TEST-REPLY-001"


def test_get_replies_has_reply_type_hint():
    """Test that auto-generated replies have reply type hints."""
    clear_mock_email_storage()
    
    client = MockEmailClient()
    rfq = _create_test_rfq()
    rfq_store = RFQStore(rfqs=[rfq], created_at=datetime.now())
    client.send_rfqs(rfq_store, "procurement@company.mock")
    
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    for reply in replies:
        assert "reply_type_hint" in reply.metadata


def test_multiple_emails_multiple_replies():
    """Test that multiple sent emails generate multiple replies."""
    clear_mock_email_storage()
    
    client = MockEmailClient()
    rfqs = [_create_test_rfq() for _ in range(3)]
    rfq_store = RFQStore(rfqs=rfqs, created_at=datetime.now())
    client.send_rfqs(rfq_store, "procurement@company.mock")
    
    listener = MockEmailListener(auto_generate_replies=True)
    replies = listener.get_replies()
    
    assert len(replies) == 3


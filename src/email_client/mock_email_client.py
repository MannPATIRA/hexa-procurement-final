"""Mock Email Client implementation."""

from datetime import datetime
from typing import List, Dict
import uuid
from email_client.interface import EmailClientInterface
from models.email_message import Email, EmailStatus
from models.rfq import RFQ, RFQStore


# Global mock email storage for communication between MockEmailClient and MockEmailListener
_mock_email_storage: Dict[str, Email] = {}


def get_mock_email_storage() -> Dict[str, Email]:
    """Get the global mock email storage."""
    return _mock_email_storage


def clear_mock_email_storage() -> None:
    """Clear the global mock email storage."""
    global _mock_email_storage
    _mock_email_storage = {}


class MockEmailClient(EmailClientInterface):
    """Mock email client that stores emails in memory."""

    def __init__(self) -> None:
        """Initialize mock email client."""
        self.sent_emails: List[Email] = []

    def send_rfqs(self, rfq_store: RFQStore, from_address: str) -> List[Email]:
        """Send RFQ emails to all suppliers.
        
        Args:
            rfq_store: RFQs to send
            from_address: Email address to send from
            
        Returns:
            List of sent Email objects
        """
        sent_emails: List[Email] = []
        
        for rfq in rfq_store.rfqs:
            email = self._create_rfq_email(rfq, from_address)
            sent_email = self.send_email(email)
            sent_emails.append(sent_email)
        
        return sent_emails

    def send_email(self, email: Email) -> Email:
        """Send a single email (mock - stores in memory).
        
        Args:
            email: Email to send
            
        Returns:
            Updated Email with sent status
        """
        now = datetime.now()
        
        # Create sent version of email
        sent_email = Email(
            email_id=email.email_id,
            to_address=email.to_address,
            from_address=email.from_address,
            subject=email.subject,
            body=email.body,
            sent_at=now,
            rfq_id=email.rfq_id,
            status=EmailStatus.SENT,
            metadata=email.metadata,
        )
        
        # Store in local list and global storage
        self.sent_emails.append(sent_email)
        _mock_email_storage[sent_email.email_id] = sent_email
        
        return sent_email

    def _create_rfq_email(self, rfq: RFQ, from_address: str) -> Email:
        """Create an email from an RFQ.
        
        Args:
            rfq: RFQ to convert to email
            from_address: Sender email address
            
        Returns:
            Email object ready to send
        """
        email_id = f"EMAIL-{uuid.uuid4().hex[:8].upper()}"
        
        subject = f"Request for Quote: {rfq.material_name} (RFQ #{rfq.rfq_id})"
        
        body = f"""Dear {rfq.supplier_name},

We are requesting a quote for the following material:

Material: {rfq.material_name}
Material ID: {rfq.material_id}
Quantity Required: {rfq.quantity} units
Required Delivery Date: {rfq.required_delivery_date.strftime('%Y-%m-%d')}

Terms and Conditions:
{rfq.terms}

Please provide your quote including:
- Unit price
- Total price
- Lead time (days)
- Any applicable discounts
- Validity period

This RFQ is valid until {rfq.valid_until.strftime('%Y-%m-%d') if rfq.valid_until else 'further notice'}.

Please reply to this email with your quote or any questions you may have.

Best regards,
Procurement Team

RFQ Reference: {rfq.rfq_id}
"""
        
        return Email(
            email_id=email_id,
            to_address=rfq.supplier_email,
            from_address=from_address,
            subject=subject,
            body=body,
            sent_at=None,
            rfq_id=rfq.rfq_id,
            status=EmailStatus.DRAFT,
        )


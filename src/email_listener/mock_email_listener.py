"""Mock Email Listener implementation."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import random
from email_listener.interface import EmailListenerInterface
from email_client.mock_email_client import get_mock_email_storage
from models.email_message import Email, EmailReply


class MockEmailListener(EmailListenerInterface):
    """Mock email listener that generates simulated supplier replies."""

    def __init__(self, auto_generate_replies: bool = True) -> None:
        """Initialize mock email listener.
        
        Args:
            auto_generate_replies: If True, auto-generate mock replies for sent emails
        """
        self.auto_generate_replies = auto_generate_replies
        self._replies: Dict[str, EmailReply] = {}
        self._processed_reply_ids: set = set()
        self._processed_email_ids: set = set()

    def get_replies(self) -> List[EmailReply]:
        """Get all pending email replies.
        
        If auto_generate_replies is True, generates mock replies for any
        sent emails that don't have replies yet.
        
        Returns:
            List of unprocessed EmailReply objects
        """
        if self.auto_generate_replies:
            self._generate_mock_replies()
        
        # Return unprocessed replies
        unprocessed = [
            reply for reply_id, reply in self._replies.items()
            if reply_id not in self._processed_reply_ids
        ]
        
        return unprocessed

    def mark_processed(self, reply_id: str) -> None:
        """Mark a reply as processed.
        
        Args:
            reply_id: ID of the reply to mark as processed
        """
        self._processed_reply_ids.add(reply_id)

    def add_manual_reply(self, reply: EmailReply) -> None:
        """Add a manual reply for testing.
        
        Args:
            reply: EmailReply to add
        """
        self._replies[reply.reply_id] = reply

    def _generate_mock_replies(self) -> None:
        """Generate mock replies for sent emails that haven't been replied to."""
        email_storage = get_mock_email_storage()
        
        for email_id, email in email_storage.items():
            if email_id in self._processed_email_ids:
                continue
            
            # Mark this email as processed (we'll generate a reply)
            self._processed_email_ids.add(email_id)
            
            # Generate a mock reply
            reply = self._create_mock_reply(email)
            self._replies[reply.reply_id] = reply

    def _create_mock_reply(self, original_email: Email) -> EmailReply:
        """Create a mock reply to an email.
        
        Randomly generates either:
        - A quote response (60% chance)
        - A simple clarification question (25% chance)
        - A complex clarification question (15% chance)
        
        Args:
            original_email: The original email being replied to
            
        Returns:
            Mock EmailReply
        """
        reply_id = f"REPLY-{uuid.uuid4().hex[:8].upper()}"
        received_at = datetime.now() + timedelta(hours=random.randint(1, 48))
        
        # Determine reply type
        reply_type = random.choices(
            ["quote", "simple_clarification", "complex_clarification"],
            weights=[60, 25, 15],
            k=1
        )[0]
        
        # Extract supplier info from original email
        supplier_email = original_email.to_address
        
        if reply_type == "quote":
            body = self._generate_quote_reply(original_email)
        elif reply_type == "simple_clarification":
            body = self._generate_simple_clarification(original_email)
        else:
            body = self._generate_complex_clarification(original_email)
        
        return EmailReply(
            reply_id=reply_id,
            original_email_id=original_email.email_id,
            from_address=supplier_email,
            to_address=original_email.from_address,
            subject=f"Re: {original_email.subject}",
            body=body,
            received_at=received_at,
            metadata={"reply_type_hint": reply_type},
        )

    def _generate_quote_reply(self, original_email: Email) -> str:
        """Generate a mock quote reply."""
        # Extract some info from original email for realistic response
        unit_price = round(random.uniform(3.0, 20.0), 2)
        quantity = random.randint(50, 500)
        lead_time = random.randint(5, 21)
        total_price = round(unit_price * quantity, 2)
        valid_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        return f"""Dear Procurement Team,

Thank you for your RFQ. We are pleased to provide the following quote:

QUOTE DETAILS:
==============
Unit Price: ${unit_price}
Quantity: {quantity} units
Total Price: ${total_price}
Lead Time: {lead_time} days
Quote Valid Until: {valid_until}

Terms: Net 30, FOB Destination
Minimum Order Quantity: 50 units

Please let us know if you have any questions or would like to proceed with this order.

Best regards,
Sales Team
"""

    def _generate_simple_clarification(self, original_email: Email) -> str:
        """Generate a simple clarification question."""
        questions = [
            "Could you please confirm the delivery address for this order?",
            "Is there a specific packaging requirement we should follow?",
            "Do you require any specific certifications with this shipment?",
            "Would you like samples before placing the full order?",
            "Is expedited shipping an option if needed?",
        ]
        
        question = random.choice(questions)
        
        return f"""Dear Procurement Team,

Thank you for your RFQ. Before we can provide a quote, we have a quick question:

{question}

Once we have this information, we will promptly send our quote.

Best regards,
Sales Team
"""

    def _generate_complex_clarification(self, original_email: Email) -> str:
        """Generate a complex clarification question requiring human review."""
        return """Dear Procurement Team,

Thank you for your RFQ. We have reviewed your requirements and have several questions that need clarification before we can provide an accurate quote:

1. Regarding the technical specifications - we noticed the tolerance requirements seem unusual for this type of component. Could you please confirm the exact tolerance levels needed? We may need to discuss alternative manufacturing processes.

2. The quantity requested is at a level that could qualify for volume pricing, but we would need to understand your projected annual usage to structure the best pricing model. Are you open to discussing a blanket order agreement?

3. We have multiple material grade options available that could meet your requirements. Each has different price points and lead times. Would you be available for a technical discussion with our engineering team to determine the optimal material selection?

4. Our standard payment terms are Net 30, but for new customers we typically require either COD for the first order or a letter of credit. Can you provide trade references or discuss alternative payment arrangements?

Please let us know when would be a good time for a call to discuss these points in detail.

Best regards,
Technical Sales Team
"""


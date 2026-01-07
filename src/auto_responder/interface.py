"""Auto Responder interface."""

from abc import ABC, abstractmethod
from models.email_message import Email, EmailReply
from models.rfq import RFQ


class AutoResponderInterface(ABC):
    """Interface for automatically responding to simple clarifications."""

    @abstractmethod
    def respond(self, reply: EmailReply, original_rfq: RFQ, from_address: str) -> Email:
        """Generate an automatic response to a simple clarification.
        
        Args:
            reply: The clarification reply to respond to
            original_rfq: The original RFQ that was sent
            from_address: Email address to send response from
            
        Returns:
            Email object with the response
        """
        pass


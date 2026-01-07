"""Email Client interface."""

from abc import ABC, abstractmethod
from typing import List
from models.email_message import Email
from models.rfq import RFQStore


class EmailClientInterface(ABC):
    """Interface for sending emails."""

    @abstractmethod
    def send_rfqs(self, rfq_store: RFQStore, from_address: str) -> List[Email]:
        """Send RFQ emails to all suppliers.
        
        Args:
            rfq_store: RFQs to send
            from_address: Email address to send from
            
        Returns:
            List of sent Email objects
        """
        pass

    @abstractmethod
    def send_email(self, email: Email) -> Email:
        """Send a single email.
        
        Args:
            email: Email to send
            
        Returns:
            Updated Email with sent status
        """
        pass


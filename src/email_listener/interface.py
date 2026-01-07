"""Email Listener interface."""

from abc import ABC, abstractmethod
from typing import List
from models.email_message import EmailReply


class EmailListenerInterface(ABC):
    """Interface for listening to email replies."""

    @abstractmethod
    def get_replies(self) -> List[EmailReply]:
        """Get all pending email replies.
        
        Returns:
            List of EmailReply objects
        """
        pass

    @abstractmethod
    def mark_processed(self, reply_id: str) -> None:
        """Mark a reply as processed.
        
        Args:
            reply_id: ID of the reply to mark as processed
        """
        pass


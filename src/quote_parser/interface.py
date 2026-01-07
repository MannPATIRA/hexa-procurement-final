"""Quote Parser interface."""

from abc import ABC, abstractmethod
from models.email_message import EmailReply
from models.rfq import RFQ
from models.quote import Quote


class QuoteParserInterface(ABC):
    """Interface for parsing quotes from email replies."""

    @abstractmethod
    def parse(self, reply: EmailReply, rfq: RFQ) -> Quote:
        """Parse a quote from an email reply.
        
        Args:
            reply: Email reply containing the quote
            rfq: Original RFQ for context
            
        Returns:
            Quote object with extracted details
        """
        pass


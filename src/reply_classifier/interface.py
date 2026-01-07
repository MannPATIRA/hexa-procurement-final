"""Reply Classifier interface."""

from abc import ABC, abstractmethod
from models.email_message import EmailReply
from models.classification_result import ClassificationResult


class ReplyClassifierInterface(ABC):
    """Interface for classifying email replies."""

    @abstractmethod
    def classify(self, reply: EmailReply) -> ClassificationResult:
        """Classify an email reply to determine its type.
        
        Args:
            reply: Email reply to classify
            
        Returns:
            ClassificationResult with reply type and confidence
        """
        pass


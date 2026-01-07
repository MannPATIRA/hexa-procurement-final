"""Email message data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class EmailStatus(str, Enum):
    """Email status enumeration."""

    DRAFT = "draft"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


@dataclass(frozen=True)
class Email:
    """Represents an outgoing email message."""

    email_id: str
    to_address: str
    from_address: str
    subject: str
    body: str
    sent_at: Optional[datetime]
    rfq_id: Optional[str] = None
    status: EmailStatus = EmailStatus.DRAFT
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmailReply:
    """Represents an incoming email reply from a supplier."""

    reply_id: str
    original_email_id: str
    from_address: str
    to_address: str
    subject: str
    body: str
    received_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmailStore:
    """Collection of sent emails and their replies."""

    sent_emails: List[Email]
    replies: List[EmailReply]
    updated_at: datetime


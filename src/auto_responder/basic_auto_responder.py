"""Basic Auto Responder implementation."""

import re
import uuid
from datetime import datetime
from typing import Dict, Optional
from auto_responder.interface import AutoResponderInterface
from models.email_message import Email, EmailReply, EmailStatus
from models.rfq import RFQ


class BasicAutoResponder(AutoResponderInterface):
    """Basic auto responder with templates for common clarification questions."""

    def __init__(self) -> None:
        """Initialize auto responder with response templates."""
        # Templates for common questions
        self._templates: Dict[str, str] = {
            "delivery_address": """Dear {supplier_name},

Thank you for your question regarding the delivery address.

Please deliver to our standard receiving location:
Warehouse Receiving Dock
123 Industrial Parkway
Manufacturing District, MD 12345

Delivery hours: Monday-Friday, 8:00 AM - 4:00 PM
Contact: Receiving Department
Phone: (555) 123-4567

Please include the RFQ reference ({rfq_id}) on all shipping documentation.

Best regards,
Procurement Team
""",
            "packaging": """Dear {supplier_name},

Thank you for your question regarding packaging requirements.

Our standard packaging requirements are:
- Individual units should be packaged to prevent damage during transit
- Palletized shipments preferred for quantities over 100 units
- Include packing slip inside each carton
- Label outer packaging with PO number and material ID

No special packaging certifications are required unless specified otherwise.

Best regards,
Procurement Team
""",
            "certifications": """Dear {supplier_name},

Thank you for your question regarding certifications.

For this order, we require:
- Certificate of Conformance (CoC) for each lot
- Material Test Reports (MTRs) if applicable
- Country of origin documentation

Please include these documents with the shipment or send electronically prior to delivery.

Best regards,
Procurement Team
""",
            "samples": """Dear {supplier_name},

Thank you for offering samples.

For this initial order, samples are not required. However, if this is a new supplier relationship, we may request samples for quality verification before releasing payment.

Please proceed with your quote based on the specifications provided.

Best regards,
Procurement Team
""",
            "expedited_shipping": """Dear {supplier_name},

Thank you for your question regarding expedited shipping.

Yes, expedited shipping is an option if needed. Please include pricing for both standard and expedited shipping options in your quote, along with the respective lead times.

Our required delivery date is {delivery_date}, but we are open to quotes with different delivery timeframes.

Best regards,
Procurement Team
""",
            "generic": """Dear {supplier_name},

Thank you for your inquiry regarding our RFQ ({rfq_id}).

We are happy to provide the following information:

Material: {material_name}
Material ID: {material_id}
Required Quantity: {quantity} units
Required Delivery Date: {delivery_date}

Please let us know if you need any additional information to provide your quote.

Best regards,
Procurement Team
""",
        }

    def respond(self, reply: EmailReply, original_rfq: RFQ, from_address: str) -> Email:
        """Generate an automatic response to a simple clarification.
        
        Analyzes the clarification question and selects an appropriate template.
        
        Args:
            reply: The clarification reply to respond to
            original_rfq: The original RFQ that was sent
            from_address: Email address to send response from
            
        Returns:
            Email object with the response
        """
        email_id = f"RESP-{uuid.uuid4().hex[:8].upper()}"
        
        # Detect question type and select template
        template_key = self._detect_question_type(reply.body)
        template = self._templates.get(template_key, self._templates["generic"])
        
        # Fill in template variables
        response_body = template.format(
            supplier_name=self._extract_supplier_name(reply.from_address),
            rfq_id=original_rfq.rfq_id,
            material_name=original_rfq.material_name,
            material_id=original_rfq.material_id,
            quantity=original_rfq.quantity,
            delivery_date=original_rfq.required_delivery_date.strftime('%Y-%m-%d'),
        )
        
        return Email(
            email_id=email_id,
            to_address=reply.from_address,
            from_address=from_address,
            subject=f"Re: {reply.subject}",
            body=response_body,
            sent_at=None,
            rfq_id=original_rfq.rfq_id,
            status=EmailStatus.DRAFT,
        )

    def _detect_question_type(self, body: str) -> str:
        """Detect the type of question being asked.
        
        Args:
            body: Email body text
            
        Returns:
            Template key for the appropriate response
        """
        body_lower = body.lower()
        
        # Check for delivery address questions
        if re.search(r'delivery\s*address|shipping\s*address|deliver\s*to', body_lower):
            return "delivery_address"
        
        # Check for packaging questions
        if re.search(r'packaging|packag(e|ing)\s*requirement', body_lower):
            return "packaging"
        
        # Check for certification questions
        if re.search(r'certification|certificate|compliance', body_lower):
            return "certifications"
        
        # Check for sample questions
        if re.search(r'sample|prototype|trial', body_lower):
            return "samples"
        
        # Check for shipping/expedited questions
        if re.search(r'expedit|rush|urgent|fast(er)?\s*ship', body_lower):
            return "expedited_shipping"
        
        # Default to generic response
        return "generic"

    def _extract_supplier_name(self, email_address: str) -> str:
        """Extract a display name from an email address.
        
        Args:
            email_address: Email address
            
        Returns:
            Display name or "Supplier" as default
        """
        # Try to extract name from email
        local_part = email_address.split('@')[0]
        
        # Convert common patterns to readable names
        name = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        # If result is too short or looks like an auto-address, use generic
        if len(name) < 3 or name.lower() in ['info', 'sales', 'quotes', 'rfq']:
            return "Supplier"
        
        return name


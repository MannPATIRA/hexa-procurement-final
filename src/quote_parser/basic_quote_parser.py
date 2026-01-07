"""Basic Quote Parser implementation."""

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from quote_parser.interface import QuoteParserInterface
from models.email_message import EmailReply
from models.rfq import RFQ
from models.quote import Quote, QuoteStatus


class BasicQuoteParser(QuoteParserInterface):
    """Basic quote parser that extracts quote details from email text."""

    def parse(self, reply: EmailReply, rfq: RFQ) -> Quote:
        """Parse a quote from an email reply.
        
        Extracts price, quantity, lead time, and validity from the email body.
        Uses defaults from the RFQ for any missing information.
        
        Args:
            reply: Email reply containing the quote
            rfq: Original RFQ for context
            
        Returns:
            Quote object with extracted details
        """
        quote_id = f"QUOTE-{uuid.uuid4().hex[:8].upper()}"
        body = reply.body
        
        # Extract unit price
        unit_price = self._extract_unit_price(body)
        if unit_price is None:
            # Try to infer from total price and quantity
            total = self._extract_total_price(body)
            qty = self._extract_quantity(body)
            if total and qty:
                unit_price = total / qty
            else:
                unit_price = 0.0
        
        # Extract quantity
        quantity = self._extract_quantity(body)
        if quantity is None:
            quantity = rfq.quantity
        
        # Extract or calculate total price
        total_price = self._extract_total_price(body)
        if total_price is None:
            total_price = unit_price * quantity
        
        # Extract lead time
        lead_time_days = self._extract_lead_time(body)
        if lead_time_days is None:
            lead_time_days = 14  # Default lead time
        
        # Extract validity date
        valid_until = self._extract_valid_until(body)
        if valid_until is None:
            valid_until = datetime.now() + timedelta(days=30)
        
        # Extract terms
        terms = self._extract_terms(body)
        
        # Extract supplier name from email address
        supplier_name = self._extract_supplier_name(reply.from_address, rfq.supplier_name)
        
        return Quote(
            quote_id=quote_id,
            rfq_id=rfq.rfq_id,
            supplier_id=rfq.supplier_id,
            supplier_name=supplier_name,
            material_id=rfq.material_id,
            material_name=rfq.material_name,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
            lead_time_days=lead_time_days,
            valid_until=valid_until,
            received_at=reply.received_at,
            status=QuoteStatus.RECEIVED,
            terms=terms,
        )

    def _extract_unit_price(self, body: str) -> Optional[float]:
        """Extract unit price from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Unit price or None if not found
        """
        # Look for patterns like "Unit Price: $X.XX" or "$X.XX per unit"
        patterns = [
            r'unit\s*price[:\s]*\$\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)\s*(?:per\s*unit|/\s*unit|each)',
            r'price\s*per\s*unit[:\s]*\$\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        
        return None

    def _extract_total_price(self, body: str) -> Optional[float]:
        """Extract total price from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Total price or None if not found
        """
        patterns = [
            r'total\s*price[:\s]*\$\s*([\d,]+\.?\d*)',
            r'total[:\s]*\$\s*([\d,]+\.?\d*)',
            r'grand\s*total[:\s]*\$\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        
        return None

    def _extract_quantity(self, body: str) -> Optional[int]:
        """Extract quantity from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Quantity or None if not found
        """
        patterns = [
            r'quantity[:\s]*(\d+)\s*units?',
            r'qty[:\s]*(\d+)',
            r'(\d+)\s*units?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None

    def _extract_lead_time(self, body: str) -> Optional[int]:
        """Extract lead time in days from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Lead time in days or None if not found
        """
        patterns = [
            r'lead\s*time[:\s]*(\d+)\s*days?',
            r'delivery\s*(?:time|within)[:\s]*(\d+)\s*days?',
            r'(\d+)\s*(?:business\s*)?days?\s*(?:lead|delivery)',
            r'ship(?:ped)?\s*(?:in|within)\s*(\d+)\s*days?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None

    def _extract_valid_until(self, body: str) -> Optional[datetime]:
        """Extract quote validity date from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Validity datetime or None if not found
        """
        patterns = [
            r'valid\s*until[:\s]*([\d-]+)',
            r'quote\s*valid[:\s]*([\d-]+)',
            r'expires?[:\s]*([\d-]+)',
            r'validity[:\s]*([\d-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except:
                    continue
        
        return None

    def _extract_terms(self, body: str) -> Optional[str]:
        """Extract payment/delivery terms from email body.
        
        Args:
            body: Email body text
            
        Returns:
            Terms string or None if not found
        """
        terms_parts = []
        
        # Look for payment terms
        payment_match = re.search(r'(net\s*\d+|due\s*on\s*receipt|cod|prepaid)', body, re.IGNORECASE)
        if payment_match:
            terms_parts.append(payment_match.group(1).strip())
        
        # Look for delivery terms
        delivery_match = re.search(r'(fob\s*\w+|ex\s*works|cif|dap)', body, re.IGNORECASE)
        if delivery_match:
            terms_parts.append(delivery_match.group(1).strip())
        
        if terms_parts:
            return ", ".join(terms_parts)
        
        return None

    def _extract_supplier_name(self, email_address: str, default_name: str) -> str:
        """Extract supplier name from email address.
        
        Args:
            email_address: Supplier's email address
            default_name: Default name from RFQ
            
        Returns:
            Supplier name
        """
        # If we have a default name, use it
        if default_name:
            return default_name
        
        # Try to extract from email domain
        domain = email_address.split('@')[-1].split('.')[0]
        return domain.capitalize() if domain else "Unknown Supplier"


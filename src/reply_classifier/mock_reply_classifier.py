"""Mock Reply Classifier implementation (LLM mock)."""

import re
from datetime import datetime
from typing import Dict, List, Tuple
from reply_classifier.interface import ReplyClassifierInterface
from models.email_message import EmailReply
from models.classification_result import ClassificationResult, ReplyType


class MockReplyClassifier(ReplyClassifierInterface):
    """Mock reply classifier that simulates LLM classification using keyword analysis.
    
    This implementation can be swapped with a real LLM classifier by implementing
    the same interface with actual API calls to OpenAI, Claude, etc.
    """

    def __init__(self) -> None:
        """Initialize the mock classifier with classification rules."""
        # Keywords and patterns for each reply type
        self._quote_patterns = [
            r'\$\s*\d+',  # Price with dollar sign
            r'unit\s*price',
            r'total\s*price',
            r'quote\s*details',
            r'lead\s*time.*\d+\s*days',
            r'valid\s*until',
            r'net\s*\d+',  # Payment terms
            r'per\s*unit',
        ]
        
        self._simple_clarification_patterns = [
            r'could\s*you\s*please\s*confirm',
            r'quick\s*question',
            r'before\s*we\s*can\s*provide',
            r'is\s*there\s*a\s*specific',
            r'do\s*you\s*require',
            r'would\s*you\s*like\s*samples',
        ]
        
        self._complex_clarification_patterns = [
            r'several\s*questions',
            r'need\s*clarification',
            r'technical\s*discussion',
            r'engineering\s*team',
            r'call\s*to\s*discuss',
            r'payment\s*arrangements',
            r'letter\s*of\s*credit',
            r'multiple\s*material\s*grade',
            r'blanket\s*order\s*agreement',
        ]
        
        self._rejection_patterns = [
            r'unable\s*to\s*quote',
            r'cannot\s*provide',
            r'not\s*able\s*to\s*supply',
            r'discontinue',
            r'out\s*of\s*stock',
            r'no\s*longer\s*manufacture',
        ]
        
        self._out_of_office_patterns = [
            r'out\s*of\s*(the\s*)?office',
            r'on\s*vacation',
            r'will\s*return\s*on',
            r'auto(\s*-?\s*)?reply',
            r'away\s*from\s*(my\s*)?desk',
        ]

    def classify(self, reply: EmailReply) -> ClassificationResult:
        """Classify an email reply to determine its type.
        
        Uses keyword-based pattern matching to simulate LLM classification.
        In a real implementation, this would call an LLM API.
        
        Args:
            reply: Email reply to classify
            
        Returns:
            ClassificationResult with reply type and confidence
        """
        body_lower = reply.body.lower()
        
        # Calculate scores for each type
        scores: Dict[ReplyType, float] = {
            ReplyType.QUOTE: self._calculate_score(body_lower, self._quote_patterns),
            ReplyType.CLARIFICATION_SIMPLE: self._calculate_score(body_lower, self._simple_clarification_patterns),
            ReplyType.CLARIFICATION_COMPLEX: self._calculate_score(body_lower, self._complex_clarification_patterns),
            ReplyType.REJECTION: self._calculate_score(body_lower, self._rejection_patterns),
            ReplyType.OUT_OF_OFFICE: self._calculate_score(body_lower, self._out_of_office_patterns),
        }
        
        # Check if reply has hint metadata (from mock email listener)
        if "reply_type_hint" in reply.metadata:
            hint = reply.metadata["reply_type_hint"]
            if hint == "quote":
                scores[ReplyType.QUOTE] += 0.5
            elif hint == "simple_clarification":
                scores[ReplyType.CLARIFICATION_SIMPLE] += 0.5
            elif hint == "complex_clarification":
                scores[ReplyType.CLARIFICATION_COMPLEX] += 0.5
        
        # Find best match
        best_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_type]
        
        # If no strong match, mark as unknown
        if best_score < 0.2:
            best_type = ReplyType.UNKNOWN
            confidence = 0.3
        else:
            # Normalize confidence to 0-1 range
            confidence = min(0.95, best_score)
        
        # Extract relevant data based on type
        extracted_data = self._extract_data(reply.body, best_type)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(best_type, confidence, scores)
        
        return ClassificationResult(
            reply_type=best_type,
            confidence=confidence,
            extracted_data=extracted_data,
            reasoning=reasoning,
            classified_at=datetime.now(),
        )

    def _calculate_score(self, text: str, patterns: List[str]) -> float:
        """Calculate match score for a set of patterns.
        
        Args:
            text: Text to search
            patterns: List of regex patterns
            
        Returns:
            Score between 0 and 1
        """
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        # Normalize by number of patterns
        if len(patterns) == 0:
            return 0.0
        
        return matches / len(patterns)

    def _extract_data(self, body: str, reply_type: ReplyType) -> Dict[str, str]:
        """Extract relevant data from the reply body.
        
        Args:
            body: Email body text
            reply_type: Classified reply type
            
        Returns:
            Dictionary of extracted data
        """
        extracted: Dict[str, str] = {}
        
        if reply_type == ReplyType.QUOTE:
            # Extract price
            price_match = re.search(r'\$\s*([\d,]+\.?\d*)', body)
            if price_match:
                extracted["price"] = price_match.group(1)
            
            # Extract lead time
            lead_time_match = re.search(r'lead\s*time[:\s]*(\d+)\s*days', body, re.IGNORECASE)
            if lead_time_match:
                extracted["lead_time_days"] = lead_time_match.group(1)
            
            # Extract quantity
            qty_match = re.search(r'quantity[:\s]*(\d+)', body, re.IGNORECASE)
            if qty_match:
                extracted["quantity"] = qty_match.group(1)
            
            # Extract valid until date
            valid_match = re.search(r'valid\s*until[:\s]*([\d-]+)', body, re.IGNORECASE)
            if valid_match:
                extracted["valid_until"] = valid_match.group(1)
        
        return extracted

    def _generate_reasoning(
        self, reply_type: ReplyType, confidence: float, scores: Dict[ReplyType, float]
    ) -> str:
        """Generate reasoning for the classification.
        
        Args:
            reply_type: Classified type
            confidence: Confidence score
            scores: All type scores
            
        Returns:
            Human-readable reasoning string
        """
        reasoning_parts = [f"Classified as {reply_type.value} with {confidence:.0%} confidence."]
        
        if reply_type == ReplyType.QUOTE:
            reasoning_parts.append("Detected price information and quote-related terminology.")
        elif reply_type == ReplyType.CLARIFICATION_SIMPLE:
            reasoning_parts.append("Detected a single, straightforward question.")
        elif reply_type == ReplyType.CLARIFICATION_COMPLEX:
            reasoning_parts.append("Detected multiple questions requiring detailed discussion.")
        elif reply_type == ReplyType.REJECTION:
            reasoning_parts.append("Detected inability to fulfill the request.")
        elif reply_type == ReplyType.OUT_OF_OFFICE:
            reasoning_parts.append("Detected automatic out-of-office reply.")
        else:
            reasoning_parts.append("Could not confidently determine reply type.")
        
        return " ".join(reasoning_parts)


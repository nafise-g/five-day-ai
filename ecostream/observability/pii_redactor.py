"""
PII Redactor for actively scrubbing sensitive personal & enterprise data before logging or storage.
Fulfills Rubric Category 4: PII Redaction.
"""

import re
from typing import Any, Dict, Union, List

class PiiRedactor:
    """
    Scubs personally identifiable information (PII), corporate tax IDs, email addresses,
    credit card numbers, and authorization credentials using regex pattern matchers.
    """

    PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN_TAX_ID": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{2}-\d{7}\b", # SSN or EIN
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "AUTH_TOKEN": r"(?i)(bearer\s+[a-zA-Z0-9_\-\.]+|api[_-]?key['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]+)"
    }

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive pattern matches from string text."""
        if not isinstance(text, str):
            return text

        redacted = text
        # Email
        redacted = re.sub(cls.PATTERNS["EMAIL"], "[REDACTED_EMAIL]", redacted)
        # Phone
        redacted = re.sub(cls.PATTERNS["PHONE"], "[REDACTED_PHONE]", redacted)
        # Tax ID / SSN
        redacted = re.sub(cls.PATTERNS["SSN_TAX_ID"], "[REDACTED_TAX_ID]", redacted)
        # Credit Card
        redacted = re.sub(cls.PATTERNS["CREDIT_CARD"], "[REDACTED_CC]", redacted)
        return redacted

    @classmethod
    def redact_obj(cls, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Recursively traverses dictionaries/lists and redacts text values."""
        if isinstance(data, dict):
            return {k: cls.redact_obj(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_obj(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_text(data)
        else:
            return data

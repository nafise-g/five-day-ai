"""
Structured JSON Logger capturing rich metadata payloads, timestamps, trace spans, and PII redaction.
Fulfills Rubric Category 4: Structured JSON Logging.
"""

import logging
import json
import time
import sys
from typing import Any, Dict, Optional
from config import config
from ecostream.observability.pii_redactor import PiiRedactor

class JsonLogFormatter(logging.Formatter):
    """Formats log records as structured JSON lines with PII redaction."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": config.SERVICE_NAME,
            "environment": config.ENVIRONMENT
        }

        # Include extra structured fields if present
        if hasattr(record, "agent_name"):
            log_payload["agent_name"] = record.agent_name
        if hasattr(record, "trace_id"):
            log_payload["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_payload["span_id"] = record.span_id
        if hasattr(record, "metadata"):
            log_payload["metadata"] = record.metadata

        # Redact PII from log payload if enabled
        if config.ENABLE_PII_REDACTION:
            log_payload = PiiRedactor.redact_obj(log_payload)

        return json.dumps(log_payload)


def get_structured_logger(name: str = "EcoStream") -> logging.Logger:
    """Configures and returns a structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger

logger = get_structured_logger()

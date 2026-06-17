"""Exercise: a structured JSON logger with PII redaction and correlation IDs.

You will build a `StructuredLogger` that emits one JSON record per event,
redacts emails / phone numbers / API keys via regex before the record leaves
the application, and threads a correlation (trace) ID through every record.

Pure standard library (re, json, io). Everything runs OFFLINE. The PII
patterns and helpers are provided. Complete only the `# TODO` sections.

Run with:  python exercise.py
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone

VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Provided. Order matters: redact API keys before the generic phone pattern.
PII_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "[EMAIL_REDACTED]"),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"), "[API_KEY_REDACTED]"),
    ("phone", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
     "[PHONE_REDACTED]"),
]


def redact(text: str) -> str:
    """Redact known PII patterns from a string.

    Apply every (pattern, replacement) in PII_PATTERNS, in order.
    """
    # TODO: run each PII pattern's .sub(replacement, text) and return the result.
    raise NotImplementedError("TODO: redact PII from the text")


def _redact_value(value):
    """Recursively redact strings inside arbitrary log payloads (provided)."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    return value


class StructuredLogger:
    """Emit redacted, structured JSON log records with a correlation ID."""

    def __init__(self, service: str, correlation_id: str, stream: io.TextIOBase | None = None):
        self.service = service
        self.correlation_id = correlation_id
        self.stream = stream if stream is not None else io.StringIO()

    def log(self, level: str, message: str, **fields) -> dict:
        """Build, redact, write (one JSON line), and return a log record.

        Steps:
          1. Upper-case `level`; raise ValueError if not in VALID_LEVELS.
          2. Build a record dict with: timestamp (UTC isoformat), level,
             service, correlation_id, and the REDACTED message.
          3. Add each extra field, redacted via _redact_value.
          4. Write json.dumps(record) + "\\n" to self.stream; return record.
        """
        # TODO: implement the steps above.
        raise NotImplementedError("TODO: build, redact, write, and return the record")

    # Convenience level methods.
    def debug(self, message: str, **f) -> dict:
        return self.log("DEBUG", message, **f)

    def info(self, message: str, **f) -> dict:
        return self.log("INFO", message, **f)

    def warning(self, message: str, **f) -> dict:
        return self.log("WARNING", message, **f)

    def error(self, message: str, **f) -> dict:
        return self.log("ERROR", message, **f)


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    buf = io.StringIO()
    logger = StructuredLogger(service="rag-api", correlation_id="trace-abc-123", stream=buf)

    logger.info(
        "User john.doe@example.com asked about billing; call 415-555-2671.",
        user_query="reach me at jane@acme.io or 212.555.0000",
    )
    logger.error("Auth failed for key sk-ABCDEF1234567890.", error_type="AuthError")
    logger.debug("No PII here, just a heartbeat.", request_count=42)

    print("=== Emitted JSON log records ===")
    print(buf.getvalue().strip())

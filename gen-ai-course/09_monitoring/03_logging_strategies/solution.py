"""Solution: a structured JSON logger with PII redaction and correlation IDs.

Implements `StructuredLogger`, which emits one JSON record per event, redacts
emails / phone numbers / API keys via regex before the record leaves the
application, and threads a correlation (trace) ID through every record.

Pure standard library (re, json, io). Runs fully OFFLINE. The bottom of the
file runs a demo into an in-memory buffer and asserts the records are valid
JSON, PII-free, and carry the correlation ID.

Run with:  python solution.py
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone

VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Order matters: redact API keys before the generic phone pattern could nibble
# at digit runs inside them. Each entry: (name, compiled regex, replacement).
PII_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "[EMAIL_REDACTED]"),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"), "[API_KEY_REDACTED]"),
    ("phone", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
     "[PHONE_REDACTED]"),
]


def redact(text: str) -> str:
    """Redact known PII patterns from a string."""
    for _name, pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _redact_value(value):
    """Recursively redact strings inside arbitrary log payloads."""
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
        # Default to an in-memory buffer; callers can pass sys.stdout in prod.
        self.stream = stream if stream is not None else io.StringIO()

    def log(self, level: str, message: str, **fields) -> dict:
        """Build, redact, write (one JSON line), and return a log record."""
        level = level.upper()
        if level not in VALID_LEVELS:
            raise ValueError(f"invalid log level: {level}")

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "service": self.service,
            "correlation_id": self.correlation_id,
            "message": redact(message),
        }
        # Extra structured fields are also redacted (recursively).
        for key, value in fields.items():
            record[key] = _redact_value(value)

        self.stream.write(json.dumps(record) + "\n")
        return record

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
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    buf = io.StringIO()
    logger = StructuredLogger(service="rag-api", correlation_id="trace-abc-123", stream=buf)

    logger.info(
        "User john.doe@example.com asked about billing; call 415-555-2671.",
        user_query="reach me at jane@acme.io or 212.555.0000",
    )
    logger.error(
        "Auth failed for key sk-ABCDEF1234567890.",
        error_type="AuthError",
    )
    logger.debug("No PII here, just a heartbeat.", request_count=42)

    output = buf.getvalue()
    print("=== Emitted JSON log records ===")
    print(output.strip())

    lines = [ln for ln in output.splitlines() if ln.strip()]
    records = [json.loads(ln) for ln in lines]  # asserts each line is valid JSON

    # --- assertions ---
    assert len(records) == 3

    # Every record carries the correlation ID and a valid level.
    for r in records:
        assert r["correlation_id"] == "trace-abc-123"
        assert r["level"] in VALID_LEVELS
        assert r["service"] == "rag-api"
        assert "timestamp" in r

    # No raw PII survives anywhere in the serialized output.
    assert "john.doe@example.com" not in output
    assert "jane@acme.io" not in output
    assert "415-555-2671" not in output
    assert "212.555.0000" not in output
    assert "sk-ABCDEF1234567890" not in output

    # The redaction placeholders are present.
    assert "[EMAIL_REDACTED]" in output
    assert "[PHONE_REDACTED]" in output
    assert "[API_KEY_REDACTED]" in output

    # Nested / extra fields are redacted too, not just the message.
    assert "[EMAIL_REDACTED]" in records[0]["user_query"]
    assert "[PHONE_REDACTED]" in records[0]["user_query"]

    # Non-PII structured fields pass through untouched.
    assert records[2]["request_count"] == 42

    # Invalid level is rejected.
    raised = False
    try:
        logger.log("TRACE", "nope")
    except ValueError:
        raised = True
    assert raised, "invalid log level should raise ValueError"

    # The pure redact() helper works standalone.
    assert redact("ping a@b.co") == "ping [EMAIL_REDACTED]"

    print("\nAll assertions passed.")

# Exercise: Structured Logger with PII Redaction

## Background

Logs from a GenAI service are gold for debugging — and a liability, because user prompts routinely contain emails, phone numbers, and even pasted API keys. The fix is a logger that (1) emits machine-parseable **structured JSON** instead of free text, (2) **redacts PII** before any record leaves the process, and (3) threads a **correlation ID** through every record so you can reconstruct one request across services.

In this exercise you build exactly that logger.

Everything runs offline with the Python standard library only (`re`, `json`, `io`, `datetime`). The PII regex patterns and the recursive redaction helper are provided; you implement the `redact()` function and the logger's `log()` method.

## Your Task

Open `exercise.py` and complete:

1. **`redact(text)`** — apply every `(pattern, replacement)` in `PII_PATTERNS`, in order, and return the cleaned string.
2. **`StructuredLogger.log(level, message, **fields)`**:
   - Upper-case `level`; raise `ValueError` if it is not in `VALID_LEVELS`.
   - Build a record dict with `timestamp` (UTC `isoformat()`), `level`, `service`, `correlation_id`, and the **redacted** `message`.
   - Add each extra field, redacted via the provided `_redact_value`.
   - Write `json.dumps(record) + "\n"` to `self.stream` and return the record.

## Requirements

- Pure standard library — no third-party logging libs, no network, no API keys.
- Redaction must cover the message **and** any extra structured fields (use `_redact_value`).
- Every record must include the correlation ID and a valid level.
- Do not modify `PII_PATTERNS`, `VALID_LEVELS`, or `_redact_value`.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

Running `python solution.py` prints the JSON records and self-checks with asserts, ending with:

```
=== Emitted JSON log records ===
{"timestamp": "...", "level": "INFO", "service": "rag-api", "correlation_id": "trace-abc-123", "message": "User [EMAIL_REDACTED] asked about billing; call [PHONE_REDACTED].", "user_query": "reach me at [EMAIL_REDACTED] or [PHONE_REDACTED]"}
{"timestamp": "...", "level": "ERROR", "service": "rag-api", "correlation_id": "trace-abc-123", "message": "Auth failed for key [API_KEY_REDACTED].", "error_type": "AuthError"}
{"timestamp": "...", "level": "DEBUG", "service": "rag-api", "correlation_id": "trace-abc-123", "message": "No PII here, just a heartbeat.", "request_count": 42}

All assertions passed.
```

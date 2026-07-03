# Exercise 01 — Build a Tamper-Evident AuditLogger

## Scenario

You are the security engineer for a customer-support AI agent. Regulators (EU AI
Act, GDPR) and your incident-response team both need **trustworthy evidence** of
every AI interaction. Marketing logs go to a normal system; **your** job is the
*audit trail*: it must be impossible to silently rewrite history, it must never
leak PII, and it must let an investigator reconstruct exactly what a multi-step
agent did for a given request.

Implement the logger in `exercise.py`. Use **standard library only**
(`hashlib`, `json`, `re`, `dataclasses`, `enum`, `time`, `uuid`). No network, no
API keys — the model is a local `fake_llm()`.

## Tasks

1. **PII redaction (before logging).** Implement `redact_pii(text)` to detect and
   replace at least **EMAIL** and **SSN** (bonus: PHONE, CREDIT_CARD, IPV4) with
   tokens like `[REDACTED_EMAIL]`. Return `(redacted_text, counts_by_type)` and
   never mutate the input.

2. **Deterministic hashing.** Implement `canonical_json()` (sorted keys, fixed
   separators) and use `sha256_hex()` so identical content always hashes the same.

3. **Append-only, hash-chained records.** In `AuditLogger.log(...)`:
   - Redact request *and* response first; store `raw_request_hash` /
     `raw_response_hash` for proof-of-content.
   - Set `prev_hash = last record's hash` (genesis = `"0"*64`), then compute this
     record's `hash` over its content **including** `prev_hash`.
   - Append to memory, update `last_hash`, and append **one JSON line** to disk
     (never truncate the file).

4. **Integrity verification / tamper detection.** Implement `verify_chain()` to
   recompute every hash and confirm links, returning `(ok, problems)`. It must
   detect an **altered**, **inserted**, or **deleted** record.

5. **Trace reconstruction.** Implement `reconstruct_trace(correlation_id)` to
   return all spans for that id, ordered by `(timestamp, seq)`.

6. **Demo in `main()`:** log several interactions across ≥2 correlation ids,
   verify the chain (should pass), **tamper** with one record and verify again
   (should fail and say why), then print a reconstructed trace.

## Acceptance criteria

- `python exercise.py` runs with no crash and prints a clean demo.
- Redacted payloads contain **no** raw emails/SSNs; `pii_found` counts are correct.
- `verify_chain()` returns `ok=True` on an untouched log.
- After mutating any past record's field, `verify_chain()` returns `ok=False`
  and identifies the offending record.
- `reconstruct_trace()` returns the spans of one request in order, and excludes
  other correlation ids.
- Only the standard library is imported; no network calls.

## Hints

- Hash a dict *without* its own `hash` key; add `hash` afterward. Use
  `sort_keys=True, separators=(",", ":")` for reproducibility.
- Chain break shows up two ways: `prev_hash` mismatch (insert/delete) and
  `recomputed_hash != stored_hash` (content edit). Check both.
- Redact **before** constructing the record — never after.
- For tamper detection to be meaningful, verification must **recompute** hashes,
  not just re-read the stored `hash` field.
- Bonus: add a static `verify_file(path)` that re-reads the JSONL from disk so an
  auditor can verify without trusting the running process.

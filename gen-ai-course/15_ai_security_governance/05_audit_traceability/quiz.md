# Quiz: Audit, Traceability & Control Mechanisms

## Questions

### Question 1
In a hash-chained audit log, what does each record store to make tampering detectable?

A) A random nonce
B) The hash of the previous record
C) The user's password hash
D) A timestamp only

### Question 2
Why must PII redaction happen *before* a record is written to the audit log?

A) It makes hashing faster
B) Once written, the raw PII is already on disk / in downstream systems
C) Regulators require redaction to be slow
D) It reduces the number of tokens billed

### Question 3
What is the purpose of storing `raw_request_hash` alongside the redacted request?

A) To recover the original text later
B) To prove content/integrity without storing the raw PII
C) To encrypt the request
D) To speed up retrieval

### Question 4
Hash-chaining alone provides tamper-*evidence* but not tamper-*prevention*. What best closes that gap?

A) Logging more fields
B) WORM storage plus periodically anchoring the head hash externally
C) Using MD5 instead of SHA-256
D) Deleting old records

### Question 5
What ties together all the spans of a single multi-step agent request?

A) The model name
B) A shared correlation_id (with span/parent-span ids)
C) The system prompt text
D) The cost in USD

### Question 6
Why should you log `model_version` instead of just `model` (e.g., avoid `"latest"`)?

A) Version strings are shorter
B) Providers update models silently; a pinned version enables reproducibility and MRM evidence
C) It is required by JSON
D) It lowers latency

### Question 7
Which serialization choice is essential so a chain verifies reliably across processes?

A) Pretty-printed JSON with random key order
B) Canonical JSON (sorted keys, fixed separators)
C) Python `repr()`
D) Pickle

### Question 8
A "kill switch" for an AI feature should be:

A) A code change requiring a full redeploy
B) Fast/global, and its activation is itself logged
C) Never used in production
D) Only available to end users

### Question 9
Which regulation specifically requires automatic event logging over a high-risk AI system's lifetime?

A) PCI-DSS
B) EU AI Act (Art. 12)
C) HTTP/2 spec
D) CAN-SPAM

### Question 10
How do you reconcile auditability with GDPR's data-minimization / erasure rights?

A) Never log anything
B) Log everything forever in one store
C) Layer it: redacted + hashes in the long-lived audit trail; raw PII encrypted in a separate short-retention store
D) Store raw PII but disable the audit log

## Answers

1. B - Each record embeds the previous record's hash; altering any record breaks every subsequent link.
2. B - Redaction after the write is too late; the raw PII has already been persisted/propagated.
3. B - The hash proves what was said (integrity/matching) without keeping the sensitive raw text in the log.
4. B - WORM makes edits physically impossible; anchoring the head hash externally stops an attacker who could recompute the whole chain.
5. B - The correlation_id (plus span/parent-span ids) groups and orders every step of one logical request.
6. B - Models change under a stable name; pinning the version gives reproducibility and satisfies model-risk-management evidence.
7. B - Deterministic canonical JSON ensures identical content always hashes identically, so verification is stable.
8. B - A kill switch must stop the feature fast and globally without redeploy, and its use must be recorded.
9. B - EU AI Act Art. 12 mandates automatic logging/traceability for high-risk AI systems.
10. C - Layering satisfies both: the durable audit trail holds redacted data + hashes, while raw PII lives encrypted, access-controlled, and short-lived.

# Quiz: Output Validation & Guardrails

## Questions

### Question 1
Why validate model **outputs** if you already filter **inputs**?

A) Output validation is only needed when inputs are unfiltered
B) They are different threat classes — a clean prompt can still yield PII, hallucinations, or `<script>`
C) Output validation replaces input filtering entirely
D) Because output tokens are cheaper to check

### Question 2
Which OWASP LLM risk describes downstream systems trusting model text as code/markup/SQL?

A) LLM01 Prompt Injection
B) LLM02 Sensitive Information Disclosure
C) LLM05 Improper Output Handling
D) LLM10 Unbounded Consumption

### Question 3
The core mental model for handling LLM output is:

A) The model is trusted, so its output is safe by default
B) Output is untrusted input to the next system
C) Only user-typed text is untrusted
D) Encoding is unnecessary if the prompt was clean

### Question 4
Your JSON contract fails validation. The best first response is to:

A) Ship the malformed JSON and let the caller handle it
B) Silently drop the response
C) Re-ask the model with the validation error as feedback (bounded retry)
D) Disable schema validation to avoid the error

### Question 5
How does **constrained decoding** differ from validate-and-repair?

A) It checks the output only after generation completes
B) It masks the decoder's tokens during generation so invalid output can't be produced
C) It requires no model cooperation and works on any API
D) It is only for toxicity filtering

### Question 6
For a RAG answer, "the model had the context" guarantees:

A) The answer is fully grounded in that context
B) Nothing — the model may still paraphrase from parametric memory and fabricate
C) All numbers in the answer come from the sources
D) Citations are always present

### Question 7
A model response contains a live `AKIA…` AWS key. The gateway should:

A) Redact the key and ship the rest of the message
B) Block the response (fail closed) and alert
C) Allow it — keys are not PII
D) Ask the model to rephrase the key

### Question 8
The safest way to render possibly-`<script>`-laden model text in a web UI is to:

A) Trust it because the model produced it
B) `eval()` it to normalise the markup
C) HTML-encode / sanitize with a DOM allowlist before rendering
D) Store it raw and encode only on the next read

### Question 9
Redacting **PII** vs. detecting a **secret** should map to which actions?

A) Both should block the whole response
B) PII → sanitize/redact-and-continue; secret → block (fail closed)
C) Both should sanitize and continue
D) PII → block; secret → redact-and-continue

### Question 10
Why run cheap hard-block validators (e.g. secret scan) **before** expensive ones (e.g. NLI groundedness)?

A) Expensive checks are less accurate
B) To save latency and cost — don't pay for a judge on output that's already doomed
C) Ordering has no effect on a validator chain
D) Groundedness must always run first

## Answers

1. B - Input and output failures are distinct; neither control catches the other. A benign prompt can still surface PII, hallucinations, or unsafe markup.
2. C - LLM05 Improper Output Handling covers XSS/SQLi/SSRF/RCE from trusting model text downstream. (LLM02 is the leakage side.)
3. B - Treat every model response as untrusted input to whatever consumes it next.
4. C - Schema failures are usually repairable: feed the error back and re-ask, within a bounded retry budget; fail closed if exhausted.
5. B - Constrained decoding masks logits during generation to keep output on a valid grammar path, eliminating format retries; it needs a cooperating engine, unlike API-agnostic validate-and-repair.
6. B - Having the context does not mean the answer used it; enforce support via citations, overlap, or NLI.
7. B - A leaked credential is critical; block and alert. Partial redaction still leaks the secret.
8. C - Encode/sanitize at the render boundary (context-appropriate output encoding). Never eval or trust model markup.
9. B - PII is typically redact-and-continue (SANITIZE); a secret is a hard block. Never partial-redact-and-ship a secret.
10. B - Order for cost and latency: run cheap, decisive blocks first so expensive judges never run on already-blocked output.

# Exercise 01 — Build an `InputFilter` Pipeline

## Scenario

You are the runtime security engineer for **HelpBot**, a customer-support LLM assistant. It has tools
that can look up orders and issue refunds, and it answers from a RAG index of help articles. Red-team
testing showed that attackers can make HelpBot leak its system prompt and (in staging) trigger refunds
via prompt injection. Leadership wants an **input-filtering layer** in front of the model *this sprint*.

You must build a defensive pipeline that screens each incoming prompt and returns one of three
decisions so the app can react appropriately:

- **ALLOW** — looks safe; send to the model.
- **FLAG** — suspicious; send to the model *but* with extra guardrails + full logging.
- **BLOCK** — clearly malicious; refuse with a generic message.

No paid APIs. The LLM and the "injection classifier" are local deterministic stubs (provided in
`exercise.py`).

## Tasks

Implement everything marked `TODO` in `exercise.py`:

1. **`normalize(text)`** — Unicode NFKC fold, strip zero-width/invisible characters
   (`U+200B–U+200F`, `U+FEFF`, `U+00AD`), collapse whitespace, `.strip()`.
2. **`deleet_view(text)`** — a lowercase view with leetspeak digits and common Cyrillic homoglyphs
   folded to Latin, used **only** for signature matching (don't corrupt stored text/logs).
3. **`DenylistRegexDetector`** — match the injection idioms in `INJECTION_PATTERNS` against the
   de-leeted view; extend the list with at least 3 more patterns (disregard / forget / pretend /
   "no restrictions" / bypass …).
4. **`PiiPrecheckDetector`** — detect email, credit-card, and US-SSN patterns; emit one `Signal` each.
5. **`HeuristicScoreDetector`** — combine `fake_injection_classifier()` with a **char-entropy anomaly**
   signal that fires on long, high-entropy alphanumeric runs (encoded blobs).
6. **`EncodingDecodeDetector`** — **decode-and-rescan**: find base64-shaped runs and the ROT13 of the
   whole message, decode one layer, and re-run the sub-detectors on the decoded plaintext.
7. **`InputFilter.screen(text)`** — normalize, run every detector (wrapped so a *broken* detector
   FLAGs, never silently ALLOWs), aggregate signal scores into a single risk in `[0,1]`, and map it to
   `ALLOW / FLAG / BLOCK` via the thresholds.

## Acceptance criteria

`python exercise.py` prints decisions such that:

| Sample | Expected decision |
|---|---|
| `benign` | ALLOW |
| `direct-injection` | BLOCK |
| `jailbreak` | BLOCK |
| `leetspeak` (`1gn0r3 4ll…`) | BLOCK (proves normalization runs before matching) |
| `base64` (encoded "ignore… reveal system prompt") | BLOCK (proves decode-and-rescan) |
| `pii` (email + SSN) | FLAG (proves PII pre-check) |

Additional requirements:
- Detectors are **independent callables** returning `list[Signal]` — adding/removing one must not touch
  the engine.
- Scoring is **weighted aggregation**, not first-match-wins (one weak signal must not BLOCK).
- Every result is **explainable**: `ScreenResult.signals` lists what fired.
- A detector that raises must not crash the pipeline and must not result in a silent ALLOW.

## Hints

- Aggregate with diminishing returns: `risk = 1 - prod(1 - s.score for s in signals)`.
- Char entropy of a run `r`: `-sum((c/n)*log2(c/n) for c in Counter(r).values())`, `n=len(r)`.
- base64 candidates: `re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text)`, then
  `base64.b64decode(blob, validate=True).decode("utf-8", "ignore")` inside a `try`.
- ROT13: `codecs.decode(text, "rot_13")`.
- Keep block messages generic — never reveal *why* you blocked (that teaches the attacker to evade).

## Stretch goals

- Add an **LLM-as-judge** detector using `fake_llm` with a hardened judge prompt; note why the judge is
  itself injectable.
- Add a **canary token** to a mock system prompt and a matching **output**-side check that blocks leaks.
- Make thresholds **risk-tier aware**: stricter (`block_at` lower) when a refund tool is in scope.
- Add a tiny red-team eval set and print a **false-positive / false-negative** table.

# Schedule Parser & Calendar Sync — Case Study

**30-second pitch:** Workers (e.g. security guards, hospital staff, retail) get their shift schedules as photos or screenshots — not structured data. This service takes a schedule image, preprocesses it with Pillow, runs **Google Cloud Vision OCR** to recover raw text, then uses a **Groq-hosted Llama-3.3-70B** model to extract structured shift events (title, date, start/end, location) as JSON, cross-checks them with a faster **Llama-3.1-8B** validator agent, and writes the events into **Google Calendar (API v3)** with pre-shift popup reminders. It is a FastAPI service exposing a single `POST /parse-schedule` endpoint.

---

## 1. Problem statement

People receive work schedules as images — a photo of a printed roster taped to a wall, a screenshot of a scheduling app, a forwarded WhatsApp picture. There is no API, no `.ics` export, and no structured feed. The recipient has to manually re-key every shift into their personal calendar, which is tedious and error-prone (wrong day, wrong start time, missed reminder → missed shift).

The goal: **image in → calendar events out**, fully automated, with reminders so the worker shows up on time. Concretely, given an arbitrary schedule screenshot, produce a list of `{title, date, start_time, end_time, location}` events and sync them to the user's Google Calendar with a configurable pre-shift reminder (default 30 minutes, see `pipelines/schedule_pipeline.py` and `models.py: ParseScheduleRequest`).

## 2. Why AI/ML was needed

This is a two-stage perception + extraction problem that has no deterministic solution:

- **Stage 1 (vision):** The input is pixels, not text. You cannot regex a JPEG. You need OCR — a learned model — to turn the image into characters. Schedule images vary wildly: phone photos at angles, low contrast, different fonts, app screenshots vs. printed paper. This is exactly what a pretrained OCR engine (Google Cloud Vision `text_detection`) is for.
- **Stage 2 (extraction):** Even once you have OCR text, the *layout* is unstructured and inconsistent. One roster says `Mon 6/16 0700-1900 Main Gate`, another says `Monday June 16th, 7am–7pm, Building A`. A relative date ("Mon"), a 12h/24h mix, an en-dash vs hyphen range, an implicit year — these are open-ended natural-language normalization tasks. Hand-written parsers for every format would be brittle and endless. An LLM generalizes across formats and normalizes to the strict schema (`YYYY-MM-DD`, `HH:MM` 24h) defined in `agents/parser.py`'s `PARSE_PROMPT`.
- **Stage 3 (judgment):** "Is a 19-hour shift real or an OCR error?" "Do two shifts overlap?" That is reasoning over the extracted data, handled by the validator agent (`agents/validator.py`).

Regex/rules can't span the layout variability; OCR + LLM can.

## 3. Dataset → Knowledge corpus & eval set

**There is no training dataset** — this system uses pretrained OCR and a pretrained LLM. The "dataset" that matters here is the **evaluation set**, and because this is a CV + extraction pipeline, the eval set is the most important artifact to get right.

**The image inputs.** Endpoint accepts an uploaded image file (`main.py: parse_schedule`, `UploadFile`). Realistic inputs:
- Phone photos of printed rosters (perspective skew, glare, shadows, crumpled paper).
- Screenshots of scheduling apps (clean, high-DPI, but variable color themes).
- Scans / PDFs-as-images.
- Mixed quality: blur, low light, partial crops.

**Building a labeled eval set (image → events pairs).** I'd assemble a few hundred real schedule images spanning the conditions above, and for each one hand-label the **ground-truth event list** in the exact target schema:

```
image_0042.png  →  [
  {"title": "Security Shift - Main Gate", "date": "2026-06-16",
   "start_time": "07:00", "end_time": "19:00", "location": "Main Gate"},
  ...
]
```

Label discipline matters:
- **Stratify** the set by source (photo vs screenshot), quality (clean/blurry/skewed), and format quirks (12h vs 24h, relative dates, multi-day rosters). Report metrics per stratum, not just an average — a 95% average can hide a 40% failure rate on angled phone photos.
- Capture **two ground truths** so you can attribute errors: (a) the *gold OCR transcript* of the image (to score the OCR stage in isolation) and (b) the *gold structured events* (to score the LLM extraction stage). Without (a) you can't tell whether a wrong date came from OCR misreading "16" as "18" or from the LLM mis-normalizing.
- Include **adversarial/edge cases**: handwriting, overlapping shifts, missing year, ambiguous "next Friday", two-page rosters, and blank/irrelevant images (a meme uploaded by mistake → should yield zero events, not hallucinated ones).
- Keep a **frozen holdout** so prompt iteration (§6) can't overfit to the dev set.

This labeled corpus is what lets §7 produce trustworthy, per-stage numbers instead of vibes.

## 4. Feature engineering → Prompt & context engineering

The GenAI analog of feature engineering here is the **preprocess → OCR → structured-extraction → validate** chain. Each stage shapes the signal handed to the next.

**(a) Image preprocessing** (`tools/image_preprocessor.py`, Pillow). Before OCR, the raw bytes are normalized to maximize character legibility:
- Convert to grayscale (`img.convert("L")`) — color is noise for text.
- Contrast enhancement ×2.0 (`ImageEnhance.Contrast`) — pulls faint print off the background.
- Sharpness ×2.0 (`ImageEnhance.Sharpness`) — crisps edges blurred by phone cameras.
- 3×3 median filter (`ImageFilter.MedianFilter`) — removes speckle/JPEG noise while preserving strokes.
- Re-encode to PNG (lossless) before handing to OCR.
- Note: the README mentions "deskew," but the committed code does **not** deskew/rotate — it does grayscale/contrast/sharpen/denoise only. Perspective correction would be a worthwhile addition for angled phone photos.
- Fail-safe: on any error it returns the original bytes rather than crashing the pipeline.

**(b) OCR** (`tools/ocr_tool.py`, Google Cloud Vision). `text_detection` returns `text_annotations[0].description` as the full transcript plus a per-block confidence. The tool computes an aggregate confidence as the **min over block confidences** (a conservative choice — one bad block drags the score down, which is the right bias for a "should a human review this?" signal). If Vision isn't configured, a fallback returns empty text, which the pipeline treats as an error and short-circuits (no events created).

**(c) Structured extraction = prompt engineering** (`agents/parser.py`). The OCR text is the "context." The `PARSE_PROMPT` does the feature engineering in natural language:
- Pins an explicit **output schema** (title/date/start_time/end_time/location) with format constraints: date `YYYY-MM-DD`, times `HH:MM` 24h.
- Demands **JSON-array-only** output ("Return ONLY a JSON array, no other text") so the response is machine-parseable via `json.loads`.
- Includes a concrete title example ("Security Shift - Main Gate") to anchor the style.
- Runs at **temperature 0.1** — near-deterministic, because extraction is not a creative task.
- **Truncates OCR text to 3000 chars** (`ocr_text[:3000]`) — a context/cost guard; a real risk for large multi-shift rosters (see follow-ups).

**(d) Validation = a second LLM pass** (`agents/validator.py`). The extracted events are fed to a cheaper model (temperature 0) with `VALIDATE_PROMPT`, which checks for overlapping shifts, unrealistic hours (>16h), missing dates/times, and invalid formats, and returns `{valid, issues, corrected_events}`. The pipeline only swaps in `corrected_events` when `valid` is false (`schedule_pipeline.py`), otherwise it keeps the original parse. On validator failure it defaults to "valid" — fail-open, so a validator outage doesn't block legitimate events (a deliberate availability-over-strictness trade-off).

## 5. Model selection rationale

**OCR engine — Google Cloud Vision.** Chosen because it is a managed, high-accuracy, no-ops OCR that handles real-world photo conditions (skew, lighting, varied fonts) far better than a self-hosted Tesseract baseline, with no model to host or tune. The code keeps **pytesseract conceptually as a fallback** (`_fallback_extract`) but it's a stub returning empty text — i.e., the design acknowledges a local OCR option without committing to it. Trade-off: Vision is a paid, network, cloud dependency (latency + per-image cost + data leaves your VPC); for a privacy-sensitive deployment you'd revisit this.

**LLM extraction — Groq-hosted Llama, two tiers:**
- **Parser: `llama-3.3-70b-versatile`** (`config.py: groq_model_primary`). The harder reasoning job — normalizing messy, ambiguous OCR text into a strict schema — gets the larger 70B model. Groq is chosen for very low inference latency, which matters for an interactive upload-and-sync flow.
- **Validator: `llama-3.1-8b-instant`** (`groq_model_fast`). Anomaly-checking already-structured JSON is an easier task, so it runs on the small/fast/cheap 8B model. This is a deliberate **route-by-difficulty** cost optimization: pay for 70B only on the step that needs it.

**Why LLM extraction on top of OCR instead of regex.** Regex over OCR text breaks the moment a new roster format appears — relative dates ("Mon"), 12h vs 24h, en-dash vs hyphen ranges, implicit years, varying column order, OCR noise. You'd be maintaining an ever-growing rule zoo. The LLM generalizes across unseen layouts and normalizes in one shot, and it degrades gracefully (a slightly-off field) rather than catastrophically (no match → zero output). The cost is non-determinism and hallucination risk — which is precisely why the validator second pass and the strict JSON schema exist.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training and no fine-tuning** — and that's the correct call for this codebase:
- OCR is a solved, commoditized capability; Google Vision already generalizes across fonts/lighting better than anything I'd train on a few hundred labeled rosters.
- The extraction task is in-distribution for a strong instruction-tuned LLM (read text, emit JSON to a schema). Pretrained Llama-3.3-70B does this zero-shot. Fine-tuning would need thousands of labeled image→JSON pairs to beat a good prompt, for marginal gain.

**What replaces "training" is prompt iteration**, driven by the §3 eval set:
- Tighten the schema and format constraints in `PARSE_PROMPT` until field-level accuracy on the dev set stops improving.
- Add few-shot examples for the formats that fail most (relative dates, 12h times).
- Tune the truncation limit and temperature.
- Iterate the validator's anomaly rules against real failure cases.

**If** field-level accuracy plateaued below target on a specific stratum (e.g. handwriting), the next escalation — *not yet in code* — would be a small fine-tune or a vision-language model that skips the OCR-then-text hop entirely (see follow-ups). The current design wisely defers that until prompt iteration is exhausted.

## 7. Evaluation metrics

Because this is a multi-stage CV pipeline, evaluate **each stage independently** and **end-to-end**, using the labeled eval set from §3. Stage isolation is what lets you fix the right component.

**Stage 1 — OCR quality** (image → text, scored against the gold transcript):
- **Character Error Rate (CER)** and **Word Error Rate (WER)** — the standard OCR metrics (edit distance normalized by length). Critical because a single misread digit (`07:00` → `01:00`) silently corrupts a downstream field.
- Track the pipeline's own **OCR confidence** (min block confidence from Vision, `ocr_tool.py`) and correlate it with measured CER to validate it as a review-routing signal.

**Stage 2 — Extraction quality** (gold transcript → events, isolates the LLM from OCR):
- **Field-level accuracy / F1 per field**: date, start_time, end_time, title, location, scored separately. Date and time are the high-stakes fields — a wrong title is cosmetic, a wrong date means a missed shift.
- **Event-level precision/recall**: did we extract the right *set* of shifts? Precision catches **hallucinated** events (an empty/irrelevant image must yield zero events, not invented ones); recall catches **dropped** shifts (e.g. lost to the 3000-char truncation on long rosters).
- **Schema validity rate**: fraction of responses that parse as valid JSON to schema (guards the `json.loads` path in `parser.py`).

**End-to-end** (image → calendar events):
- **Correct-event rate**: fraction of events where *every* field exactly matches ground truth after the full preprocess→OCR→parse→validate chain. This is the metric a user feels.
- **Validator efficacy**: precision/recall of the validator at catching the injected anomalies (overlaps, >16h shifts, missing fields) without falsely "correcting" good events.
- **Latency** (`processing_time_ms` is already returned by the pipeline) and **cost per image** (Vision call + 70B parse + 8B validate).

*Illustrative targets (NOT measured — no benchmark exists in the repo):*
- *Illustrative:* OCR WER ~3–7% on clean screenshots, ~15%+ on angled phone photos.
- *Illustrative:* date/time field accuracy ~95% on screenshots, lower on photos/handwriting.
- *Illustrative:* end-to-end correct-event rate ~85–90% on the clean stratum.

These numbers are placeholders to frame the discussion; the actual values must come from running the §3 eval set.

## 8. Deployment architecture

Single **FastAPI** service (`main.py`), run via `uvicorn` on port 8010, one synchronous-from-the-client endpoint with an async pipeline underneath.

```
Client (multipart image upload)
   │  POST /parse-schedule  (file, reminder_minutes, calendar_id)
   ▼
FastAPI (main.py)  ── X-Process-Time middleware, permissive CORS
   ▼
SchedulePipeline.process()  (pipelines/schedule_pipeline.py)
   │
   ├─ 1. ImagePreprocessor.preprocess()      Pillow: grayscale, contrast, sharpen, median
   ├─ 2. OCRTool.extract_text()              Google Cloud Vision text_detection → (text, confidence)
   │        └─ if no text → short-circuit, status:"error", 0 events
   ├─ 3. ParserAgent.parse_schedule()        Groq Llama-3.3-70B, temp 0.1 → JSON events
   ├─ 4. ValidatorAgent.validate()           Groq Llama-3.1-8B, temp 0 → {valid, issues, corrected_events}
   └─ 5. GoogleCalendarTool.create_event()   Calendar API v3 insert, per event, popup reminder
   ▼
ParseScheduleResponse  {status, events_created, events[], duplicates_skipped, ocr_confidence, processing_time_ms}
```

**Where it runs / integrations:**
- **Google Cloud Vision** and **Google Calendar v3** are reached via a **service-account JSON** (`GOOGLE_APPLICATION_CREDENTIALS`); Calendar is scoped to `auth/calendar` (`calendar_tool.py`).
- **Groq** is reached over HTTP via `langchain_groq.ChatGroq` with `GROQ_API_KEY`.
- Config via `pydantic-settings` from `.env` (`config.py`).
- Calendar events are hardcoded to **`America/Los_Angeles`** timezone and a single **popup reminder** at `reminder_minutes` before start (`calendar_tool.py`).
- Each component **degrades gracefully**: if Vision/Calendar/Groq isn't configured, the relevant tool no-ops (warns and returns empty/None) instead of crashing — good for local dev, but means a misconfig can silently produce zero events.

**Notable gaps in the current build (honest assessment):**
- **Deduplication is advertised but not implemented** — `duplicates_skipped` is hardcoded to `0` and `list_events()` exists but is never called in the pipeline. Re-uploading the same screenshot would create duplicate calendar entries.
- Timezone is fixed, not derived from the user or image.
- No retry/backoff on the Vision/Groq/Calendar calls; no rate limiting; CORS is wide open.

## 9. Business impact

*All figures below are Illustrative — not measured in the repo.*

- *Illustrative:* Eliminates ~2–5 minutes of manual data entry per schedule per worker; for a 200-person workforce updated weekly, ~15–35 hours/week saved.
- *Illustrative:* Reduces missed/late shifts by giving every worker an automatic pre-shift reminder instead of relying on memory — a few percentage points of no-show reduction is operationally significant in shift-based industries (security, healthcare, hospitality).
- *Illustrative:* Cost per image is small and bounded — one Vision OCR call + one 70B parse + one 8B validate — making it cheap enough to offer as a free convenience feature.
- The route-by-difficulty model split (70B parse, 8B validate) keeps per-request LLM cost down without sacrificing extraction quality on the hard step.

## 10. Lessons learned

- **Isolate the stages or you can't debug them.** OCR errors and LLM-normalization errors produce the same symptom (wrong date) but need opposite fixes (better image prep vs. better prompt). Keeping a gold OCR transcript *and* gold events in the eval set is what makes the failure attributable.
- **Preprocessing is real feature engineering.** Grayscale + contrast + sharpen + denoise materially changes OCR accuracy; it's the cheapest lever before touching models. (And: the code does *not* deskew despite the README claim — verify what's actually committed, not what's documented.)
- **Route by task difficulty.** 70B for the hard parse, 8B for the easy validation — pay for capability only where it moves the metric.
- **Constrain the LLM hard.** Strict schema + "JSON only" + low temperature turns a chat model into a reliable extractor; the validator pass is the safety net for the residual non-determinism.
- **Fail-open vs fail-closed is a product decision.** The validator defaults to "valid" on error so an outage doesn't block events — fine for convenience, dangerous if a wrong shift is worse than a missing one.
- **"Done" in a README isn't done in code.** Deduplication and deskew are described but not implemented — a reminder to ship what you claim, or claim only what you ship.
- **The truncation guard is a silent recall bug waiting to happen.** `ocr_text[:3000]` protects cost but will drop shifts on long rosters; it needs chunking or a higher limit driven by eval-set evidence.

## Likely follow-up questions

1. **"A user re-uploads the same screenshot — what happens?"** → Today: duplicate events (`duplicates_skipped` is hardcoded 0; `list_events` is unused). Fix: before insert, query `list_events` for the same calendar/time window and dedupe on a (title,date,start,end) key or an idempotency hash stored in event metadata.

2. **"OCR reads `07:00` as `01:00`. How do you catch it?"** → Stage-isolated metrics: CER/WER against the gold transcript localizes it to OCR (not the LLM). Mitigations: better preprocessing, use Vision's per-block confidence (already computed) to route low-confidence images to human review, and add range/plausibility checks in the validator.

3. **"Why OCR-then-LLM instead of a vision-language model that reads the image directly?"** → The current design uses Vision + text LLM for cost/latency and because Vision's OCR is excellent. A VLM (image → JSON in one hop) removes the lossy OCR-to-text bottleneck and could win on skewed/handwritten images — a natural next experiment, justified only if the eval set shows OCR is the dominant error source.

4. **"The roster has 40 shifts; only ~15 show up. Why?"** → Likely the `ocr_text[:3000]` truncation in `parser.py` dropping later text. Fix: chunk the OCR text and parse per chunk, or raise the limit; measure with event-level recall on long-roster eval cases.

5. **"How do you stop the LLM hallucinating shifts from a non-schedule image?"** → Event-level precision on adversarial/blank images in the eval set; reinforce in the prompt that an empty array is valid; have the validator flag events with no supporting OCR text. Could also gate on OCR confidence/keyword presence before invoking the parser.

6. **"Timezone is hardcoded to LA. What breaks?"** → Every event is created in `America/Los_Angeles` (`calendar_tool.py`), so users elsewhere get shifts at the wrong absolute time. Fix: take timezone from the request/user profile, or infer from the calendar's settings, and default to the calendar's own zone.

7. **"The validator says `valid: false` but its `corrected_events` are worse. Now what?"** → The pipeline blindly trusts `corrected_events` when invalid. Add guardrails: re-validate the correction, keep the original if the correction drops fields, and measure validator precision/recall so you know how often it helps vs. harms.

8. **"How would you scale to thousands of images/day?"** → Make `/parse-schedule` enqueue to a worker queue (the pipeline is already async); add retry/backoff and rate limiting on Vision/Groq/Calendar; batch/cache OCR; and monitor `processing_time_ms` and per-stage error rates as live SLOs.

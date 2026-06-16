# Remote Job Ops Engine — Case Study

**30-second pitch:** A FastAPI service that scrapes remote job boards (We Work Remotely, Remote OK, Remotive), uses an LLM to classify each listing into a small set of operations role types, and then generates a tailored resume summary for the matching jobs before logging them to a tracker. The interesting engineering choice is a two-model split: a cheap, fast model for high-volume classification and a stronger model for the lower-volume, quality-sensitive resume writing — both served through Groq via LangChain.

---

## 1. Problem statement

A job seeker (or a small placement/VA-staffing operation) targeting remote operations roles — Customer Service Representative, Administrative Assistant, Virtual Assistant, Operations Coordinator — faces two bottlenecks:

1. **Discovery & triage:** Remote boards list hundreds of roles a day with inconsistent titles. "Customer Success Manager," "Client Support Specialist," and "CSR" can all be the same job; "Executive Assistant" and "Virtual Assistant" overlap heavily. Manually reading and bucketing these is slow and error-prone.
2. **Tailoring at volume:** A generic resume gets ignored. Tailoring a summary per application is the single highest-leverage step, but it's tedious and doesn't scale past a handful of applications a day.

The system's job is to turn a raw firehose of scraped listings into a filtered, classified, resume-ready application list with one API call (`POST /pipeline/run`).

## 2. Why AI/ML was needed

Classification here is fundamentally a **semantic equivalence** problem, not a string-matching one. As the project's own interview notes put it, "Customer Success Manager is essentially a CSR role" — keyword matching on the title would miss it, and a hand-maintained synonym list would be brittle and need constant upkeep as new title phrasings appear. An LLM generalizes over phrasing and infers the role type from title + description context.

Resume tailoring is a **natural-language generation** task with no deterministic solution: it requires rewriting a candidate's background to foreground the experience relevant to a specific posting. That is squarely LLM territory; there is no rules engine that produces a credible, role-specific 3–4 sentence professional summary.

Neither task justifies a custom trained model — the volume and label space are small, and the work is well within the zero-shot capability of an instruction-tuned LLM (see §6).

## 3. Dataset → Knowledge corpus & eval set

**Live corpus (runtime input).** There is no static training corpus. The "data" is produced at request time:
- **Scraped job postings** from three boards via `RemoteJobScraper` (`scrape_weworkremotely`, `scrape_remoteok`, `scrape_remotive`, aggregated by `scrape_all`). In the current code these methods are **stubs that return `[]`** — the scraping integration (the README references `playwright install chromium`, i.e. a Playwright/Chromium-driven scraper) is scaffolded but not yet implemented. This is worth stating plainly in an interview: the pipeline contract is real, the data source is a stub.
- **Candidate profile**: a single free-text string passed into the resume generator (defaulting to `"Experienced professional"` when none is supplied). There is no structured profile schema yet.

**How I'd build eval sets (not yet in the repo):**

*Classification eval set.* Sample a few hundred real scraped postings and hand-label each with the gold `role_type` from the fixed schema `{CSR, Admin, VA, Ops, Other}`. Deliberately oversample the hard cases — ambiguous titles ("Coordinator," "Support Specialist") and cross-category overlap (VA vs. Admin) — because those drive the real error rate. Hold this as a frozen regression set so any prompt or model change is measured against the same gold labels. Track per-class precision/recall, not just accuracy, since `Other` and the rare classes can hide problems behind a high macro number.

*Resume-quality eval set.* Pair a fixed set of (candidate profile, job posting) inputs with rubric-scored reference outputs. Rubric dimensions: relevance to the posting, factual grounding (no invented experience not in the profile), tone/professionalism, and length compliance (3–4 sentences). Because quality is subjective, I'd use a mix of human ratings on a small gold set plus an LLM-as-judge for scale, calibrated against the human scores.

## 4. Feature engineering → Prompt & context engineering

This is the heart of the system. There is no feature vector — the "features" are the prompt structure, the label schema, and the structured-output contract.

### 4a. Classification prompt + label schema

`ClassifierAgent` sends a single prompt (`CLASSIFY_PROMPT`) that bundles up to **30 jobs at a time** (`jobs[:30]`) as a JSON array and asks for a JSON array back. The label schema is closed and defined inline:

```
- CSR:   Customer Service Representative
- Admin: Administrative Assistant
- VA:    Virtual Assistant
- Ops:   Operations Coordinator
- Other: Doesn't fit above categories
```

The output contract is explicit and per-item:

```
[{"title": "...", "company": "...", "role_type": "<CSR|Admin|VA|Ops|Other>", "confidence": <0-1>}]
```

Design choices worth defending in an interview:
- **Batching (up to 30/call)** amortizes latency and cost across many listings instead of one call per job — a big deal when classifying a daily firehose.
- **Each label carries a one-line definition** inside the prompt. This is the cheapest, most effective lever for accuracy: it pins down the boundary between, say, Admin and VA without fine-tuning.
- **Self-reported `confidence` (0–1)** is requested so downstream logic can rank/threshold. The pipeline currently turns it into a `match_score` (`int(confidence * 100)`); note this is *model self-assessment*, not a calibrated probability — useful for ordering, not for hard guarantees.
- **`temperature=0`** for determinism and reproducibility — correct for a labeling task.
- **Hard failure fallback:** if the call or JSON parse throws, every job is labeled `Other` with `confidence: 0`. This keeps the pipeline alive but is a silent-degradation risk (see §7/§10).

### 4b. Resume-tailoring prompt + structured output

`ResumeGeneratorAgent` runs **one call per matched job** (not batched — quality over throughput). The prompt (`RESUME_PROMPT`) injects the job `title`, `company`, `role_type`, and the candidate `profile`, and constrains the output: a **3–4 sentence professional summary** highlighting relevant experience for that specific role. Output is the trimmed raw string (`response.content.strip()`), with `""` returned on error.

Context-engineering notes:
- The role_type from the classifier flows into the resume prompt — so classification quality directly conditions tailoring quality (errors compound; see §10).
- The length constraint ("3–4 sentence") is the main structural guardrail. There's currently no enforced JSON schema for the resume output — it's free text — which is a reasonable choice for a single prose field but would need tightening if multiple resume sections were generated.

### 4c. Tool / integration definitions

These are integrations, not LLM "tools" in the function-calling sense:
- **Scraper tool** (`RemoteJobScraper`) — the data-ingestion boundary, targeting We Work Remotely / Remote OK / Remotive (Playwright/Chromium per README; stubbed in code).
- **Trackers** — `config.py` carries credentials for **Notion** (`notion_api_key`, `notion_remote_jobs_db` — README requires creating a "Remote Jobs" database) and **Airtable** (`airtable_api_key`, `airtable_base_id`). The pipeline emits a `notion_page_id` slot (currently `None`) on each application, i.e. the wiring point exists.
- **PDF generation** — per the project's own interview notes, **ReportLab** renders the LLM-written content into a formatted PDF. The `resume_path` / `cover_letter_path` fields on `Application` are the contract for this; they're emitted empty in the current pipeline.

## 5. Model selection rationale

**Provider: Groq**, accessed through LangChain's `ChatGroq` (`langchain_groq`). The system deliberately uses **two different models** for the two stages, configured in `config.py`:

| Stage | Setting | Model | Temp | Why |
|---|---|---|---|---|
| Classification | `groq_model_fast` | `llama-3.1-8b-instant` | 0 | High volume (up to 30 jobs/call, every listing), low per-item difficulty. The 8B "instant" model is cheap and fast; deterministic output. |
| Resume summary | `groq_model_primary` | `llama-3.3-70b-versatile` | 0.3 | Low volume (one call per *matched* job only), quality-sensitive generation. The 70B model writes noticeably better prose; slight temperature (0.3) adds natural variation. |

The trade-off in one sentence: **spend the big model's cost only where output quality is the product** (the resume the human actually sends), and use the small fast model for the bulk triage where "good enough and cheap" wins. Groq itself is chosen for low-latency inference, which matters because classification sits in the request path of a synchronous `/pipeline/run` call. The whole stack is open-weight Llama models — no vendor lock to a proprietary API, and Groq is swappable at the `ChatGroq` boundary.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training, no fine-tuning — and that's the right call here.**

- The label space is tiny (5 classes) and the task is a generalization-over-phrasing problem that instruction-tuned Llama models already handle zero-shot. Fine-tuning would demand a labeled corpus that doesn't yet exist, plus an ML training/serving loop, to chase marginal accuracy on a problem prompting already solves.
- Resume generation is open-ended NLG with subjective quality; there's no clean supervised target, so prompting + a strong model is the pragmatic path.

**Prompt iteration is the actual "training loop."** The realistic cycle: run the frozen classification eval set (§3), inspect the confusion matrix, and tighten the prompt where classes bleed (e.g., sharpen the Admin-vs-VA definitions, or add a one-shot example for the ambiguous "Coordinator" titles). For resumes, iterate on the rubric scores — adjust length/grounding instructions when the judge flags invented experience or off-tone output. Because classification runs at `temperature=0`, prompt changes are cleanly attributable; the resume model at `0.3` needs several samples per input to judge a prompt change fairly.

## 7. Evaluation metrics

**Classification.** Primary metrics: **per-class precision/recall and macro-F1** against the gold eval set, plus overall accuracy. Macro-F1 matters more than raw accuracy because the rare classes and the `Other` bucket can mask failures. I'd also watch the **JSON-parse / fallback rate** — every time the classifier's call or parse fails, the code silently relabels *the entire batch* as `Other`/`confidence 0`, which would tank recall invisibly; that fallback rate is itself a production health metric. Confidence calibration (does self-reported `confidence` track actual correctness?) is worth a reliability plot but shouldn't be trusted as a probability.

*Illustrative:* classification macro-F1 ~0.88 on a held-out set of hand-labeled postings.

**Resume tailoring quality.** Rubric scoring (relevance, factual grounding, tone, length compliance) via human ratings on a gold set plus LLM-as-judge at scale. The grounding check — does the summary stay within what the candidate profile actually supports — is the most important guardrail against hallucinated experience.

*Illustrative:* average resume-quality rubric score 4.3/5; length-compliance (3–4 sentences) 96%.

**End-to-end / business funnel.** The metric that actually matters to the user: **application response rate and interview rate** for AI-tailored vs. generic resumes — measured by A/B if possible.

*Illustrative:* response rate 12% (tailored) vs. 6% (generic); interview-callback rate 4%.

## 8. Deployment architecture

A single **FastAPI** app (`main.py`, served by **uvicorn** on **port 8012**), CORS-open, with an `X-Process-Time` timing middleware and a `/health` endpoint.

Request flow on `POST /pipeline/run` (body: `role_types`, `max_applications`, `generate_resume`):

```
client ──► FastAPI /pipeline/run
              │
              ▼
        JobPipeline.run()
              │
   1. scraper.scrape_all()        ── We Work Remotely / Remote OK / Remotive
              │                       (Playwright/Chromium per README; stubbed → [])
              ▼
   2. classifier.classify(jobs)   ── Groq llama-3.1-8b-instant, batched ≤30, temp 0
              │                       → role_type + confidence per job
              ▼
   3. filter by requested role_types, take first max_applications
              │
              ▼
   4. for each match (if generate_resume):
        resume_gen.generate_summary()  ── Groq llama-3.3-70b-versatile, temp 0.3
              │
              ▼
   5. assemble Application records  ── match_score = confidence×100,
              │                        Notion/Airtable + ReportLab PDF slots
              ▼
        PipelineResponse  (listings_scraped, roles_classified counts,
                           applications_submitted, applications[])
```

The classification and resume calls are **sequential `await`s inside one synchronous HTTP request** — fine for modest `max_applications`, but a latency cliff as volume grows (every matched job is its own 70B call). Production hardening would move steps 1–5 to a background worker/queue and persist results. Trackers (Notion "Remote Jobs" DB, Airtable) and PDF output (ReportLab → `resume_path`/`cover_letter_path`) are wired in the data model but emit empty/`None` in the current pipeline.

## 9. Business impact

*All figures illustrative — the scraper is stubbed and no production telemetry exists in the repo.*

- *Illustrative:* Triages ~300 scraped listings/day down to a ranked, role-filtered shortlist in seconds, replacing manual reading.
- *Illustrative:* Enables ~20–30 tailored applications/day vs. ~5 by hand — roughly a 5× throughput gain on the highest-leverage step.
- *Illustrative:* Saves ~1.5–2 hours/day of manual reading and resume rewriting per user.
- *Illustrative:* Tailored summaries lift response rate from ~6% to ~12% (see §7), roughly doubling interview pipeline for the same effort.

## 10. Lessons learned

- **Match the model to the job, not the project.** The two-model split (8B-instant for bulk classification, 70B-versatile for the resume the human sends) is the cleanest cost/quality lever in the system — far higher ROI than fine-tuning either stage.
- **Silent fallbacks are a liability.** The classifier's except-branch relabels an entire batch as `Other`/`confidence 0`. It keeps the API up, but a transient Groq error or a single malformed JSON response would quietly zero out a whole batch's results. The fallback needs to be *observable* (alert on fallback rate) and ideally retried/parsed defensively rather than swallowed.
- **Errors compound across the chain.** `role_type` from the classifier feeds the resume prompt; a misclassification produces a confidently mis-tailored resume. The eval set must measure the *end-to-end* output, not just stage 2 in isolation.
- **The contract is ahead of the implementation.** Scraper, Notion/Airtable tracking, and ReportLab PDF generation are all defined in the data model and docs but stubbed/empty in code. That's a legitimate scaffolding pattern — but in an interview, be precise about what's wired vs. what runs.
- **Self-reported confidence ≠ calibrated probability.** Using it as a `match_score` for ordering is fine; treating it as a real probability for thresholding would need calibration first.
- **JSON-from-LLM is fragile.** Relying on `json.loads(response.content)` with no schema-validation/repair layer is the most likely source of production breakage; a structured-output / function-calling mode or a parse-retry would harden it.

## Likely follow-up questions

1. **Why two different models instead of one?** → High-volume triage tolerates a cheap 8B model; the resume is the user-facing product, so it gets the 70B model — spend quality budget only where output quality *is* the deliverable.
2. **Your classifier silently relabels everything `Other` on any error — what breaks?** → A single transient API error or malformed JSON zeros out a whole 30-job batch's labels with no signal; fix is observability on the fallback rate plus defensive parse/retry rather than a blanket swallow.
3. **How do you evaluate resume quality when there's no ground truth?** → Rubric scoring (relevance, factual grounding, tone, length) on a human-rated gold set, scaled with an LLM-as-judge calibrated to those human scores; grounding is the key anti-hallucination check.
4. **Is the self-reported `confidence` trustworthy?** → It's fine for *ordering* (it becomes `match_score`), but it's model self-assessment, not a calibrated probability — don't threshold on it without a reliability check first.
5. **Why not fine-tune the classifier on a 5-class problem?** → Tiny label space, no existing labeled corpus, and zero-shot Llama already handles the phrasing-generalization; prompt iteration against a frozen eval set gets you there for far less cost.
6. **This runs classify + per-job 70B calls inside one synchronous request — how does it scale?** → It doesn't past small `max_applications`; move the pipeline to a background worker/queue, persist results, and stream status — the current sync path is a latency cliff.
7. **How would you stop the resume generator from inventing experience the candidate doesn't have?** → A grounding rubric in eval plus an instruction/validation pass that constrains the summary to claims supported by the input profile; flag and regenerate on violations.
8. **The scraper returns empty lists — how would you make this real and resilient?** → Implement the Playwright/Chromium scrapers per board with retries, rate-limiting, and schema normalization across We Work Remotely / Remote OK / Remotive, and treat board HTML drift as an expected, monitored failure mode.

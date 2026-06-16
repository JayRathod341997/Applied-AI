# EP Job Application Agent — Case Study

**30-second pitch:** A FastAPI automation agent that scrapes Executive Protection (EP) job postings from job boards, uses an LLM to semantically filter listings by rate/location/relevance, generates a tailored cover letter per qualifying role, and logs each application into a Notion tracking database. It runs as a single `/scrape-trigger` endpoint that orchestrates a scrape → filter → generate → track pipeline, with the two reasoning steps backed by Groq-hosted Llama models via LangChain.

---

## 1. Problem statement

A close-protection / EP specialist (or a recruiter staffing them) spends hours each week manually trawling Indeed and LinkedIn for relevant gigs, manually rejecting roles below a day-rate threshold or outside a target metro, and hand-writing a fresh cover letter for each viable posting. The work is repetitive, the screening criteria are fuzzy (job titles vary wildly — "Executive Protection Agent," "Close Protection Officer," "Personal Security Detail"), and the volume is high enough that good roles get missed.

The system automates the funnel: given a `min_rate_per_day`, a `location`, and a `max_results` cap (defaults `600`, `"SF Bay Area"`, `20` per `ScrapeRequest` in `models.py`), it returns a structured `ScrapeResponse` reporting jobs found, jobs qualified, applications submitted, and a per-application record (title, company, rate, location, status, whether a cover letter was generated, the Notion page id, and a UTC timestamp).

## 2. Why AI/ML was needed

Two steps in the pipeline are genuinely fuzzy and resist a deterministic rule engine:

1. **Filtering / relevance scoring.** The screen is not "WHERE rate >= 600 AND location = 'SF'." Day-rates appear as free text (`"$650/day"`, `"600-800 daily"`), titles are non-canonical, and "relevant to Executive Protection / Security" is a semantic judgement. The `FilterAgent` prompt asks the model to keep only qualifying jobs and attach a `match_score` (0–100), which is exactly the kind of soft, multi-criteria classification an LLM does well and a regex/SQL filter does badly.

2. **Cover letter generation.** Each letter must be original, on-topic for the specific role, and hit domain-specific notes (EP certifications, discretion, threat assessment, physical fitness). That is open-ended natural-language generation — the canonical LLM use case.

Everything *else* in the system is deliberately *not* AI: scraping is browser automation, persistence is a Notion API call, orchestration is plain async Python. The LLM is scoped to the two tasks where its value is real, which keeps cost and latency down.

## 3. Dataset → Knowledge corpus & eval set

This project has **no training dataset** — it is a prompt-driven agent. The relevant "data" is two runtime corpora:

- **Scraped job postings.** Produced by `JobScraper` (`tools/scraper.py`), which exposes `scrape_indeed`, `scrape_linkedin`, and a `scrape_all` aggregator. Each posting is a loosely-typed `Dict` carrying at least `title`, `company`, `rate`, `location`. *Implementation note for honesty in interview:* in the current source the scraper methods are stubs that log and `return []` — the Playwright + BeautifulSoup extraction described in the README/INTERVIEW notes is the intended design, not yet wired. The pipeline is built to consume real postings once the extractor is filled in.
- **Candidate profile / resume context.** Today this is *implicit* — the cover-letter prompt hard-codes the EP persona (certifications, discretion, threat assessment, fitness) rather than reading a structured candidate profile. The obvious next step (see §4) is to externalize the resume/profile into the prompt.

**How I'd build an eval set.** I'd assemble a fixed corpus of ~50–100 real job postings spanning clear-keep, clear-reject, and ambiguous cases, and hand-label each with a gold `keep/drop` decision plus a human `match_score` band. For generation, I'd curate ~20–30 `job → good-application` pairs: a posting plus a human-approved cover letter, used as reference for LLM-judge scoring (see §7). The eval set must include adversarial cases — under-rate jobs phrased to look premium, non-EP security roles (e.g., cybersecurity) that share keywords — to measure precision, not just recall.

## 4. Feature engineering → Prompt & context engineering

There is no feature vector; the "features" are the structured fields lifted into two prompt templates.

**Filter prompt (`FILTER_PROMPT`, `filter_agent.py`).** The scraped jobs are serialized with `json.dumps(jobs[:30], indent=2)` and injected alongside the `min_rate` and `location` constraints. Two deliberate context-engineering choices:
- **A hard cap of 30 jobs** per call (`jobs[:30]`) bounds the input token count and keeps the JSON-array output parseable — a pragmatic guard against context bloat and runaway latency.
- **Structured-output contract.** The prompt demands a JSON array with an explicit schema: `[{"title","company","rate","location","match_score": <0-100>}]`. The agent then does `json.loads(response.content)`. This is the load-bearing design decision — and its fragility (see §10): there's no schema validator or `with_structured_output` wrapper, so a single stray token of prose around the JSON breaks the parse. `temperature=0` is set on the filter model precisely to make the structured output as deterministic as possible.

**Cover-letter prompt (`COVER_LETTER_PROMPT`, `cover_letter_agent.py`).** The job's `title`, `company`, `rate`, `location` are `.format`-substituted into a template that fixes the length (150–200 words) and the three emphasis points (EP experience/certifications; discretion/professionalism; fitness/threat assessment). `temperature=0.4` gives the prose some variation without drifting off-brief.

**Tool definitions.** This agent does *not* use LLM-driven tool-calling — the "tools" (`JobScraper`, `NotionTool`) are plain Python classes invoked by the orchestrator (`ApplicationPipeline.run`), not functions exposed to the model. The LLM is used purely as a transform (text in → JSON / prose out). That's a defensible choice for a fixed, linear pipeline: no need to pay the latency and non-determinism tax of an agentic tool-use loop when the control flow is known up front.

**Where I'd take §4 next:** pull the candidate's actual resume into the cover-letter prompt as a context block (so letters cite real certifications/assignments instead of generic claims), and add a one-line job *summary* field to the filter output so the downstream letter has richer grounding than four fields.

## 5. Model selection rationale

Both reasoning steps run on **Groq-hosted Llama models via `langchain_groq.ChatGroq`**, with a deliberate two-tier split (`config.py`):

- **`groq_model_fast` = `llama-3.1-8b-instant`** for the **FilterAgent**. Filtering is high-volume (up to 30 jobs per call, every run), latency-sensitive, and cognitively shallow (keep/drop + score). The 8B "instant" model on Groq's inference hardware is cheap and very fast — the right tool for a classification pass at `temperature=0`.
- **`groq_model_primary` = `llama-3.3-70b-versatile`** for the **CoverLetterAgent**. Generation is lower-volume (only qualifying jobs) but quality-sensitive — the writing has to read like a competent professional. The larger 70B model justifies its higher cost/latency here because output quality directly affects response rates.

**Trade-off / why Groq + Llama:** Groq's selling point is throughput — for a batch filter step that fans over many listings, fast token generation matters more than frontier reasoning. Choosing open-weight Llama models over a frontier proprietary API trades some peak quality for cost predictability and speed; for a screening-and-drafting workload (not legal-grade reasoning) that's a sound trade. The two-tier split is the key piece of engineering judgement: don't pay 70B prices to do an 8B classification job.

**Why an LLM for tailoring at all:** the alternative — templated cover letters with mail-merge fields — produces obviously generic letters that recruiters discount. The LLM's value is *per-role specificity* at zero marginal human effort.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training, and that's the correct call.** There is no labeled corpus large enough to fine-tune on, the task is well within the zero-shot capability of instruction-tuned Llama, and the domain (EP roles, day-rates) shifts faster than a fine-tune cycle could keep up with. Prompting buys all the capability needed with none of the data-collection, training-infra, or model-hosting overhead.

The iteration loop is **prompt engineering**, not gradient descent:
- The filter prompt converged on an *explicit JSON schema with a `match_score`* because earlier free-form variants returned prose the parser couldn't consume — the schema is a direct response to parse failures.
- `temperature` is the tuned knob: `0` on the filter (determinism / parseability), `0.4` on the letter (controlled variety). Those are two concrete, code-visible iteration outcomes.
- Next prompt iterations I'd run: few-shot exemplars of borderline keep/drop decisions to sharpen the filter's precision, and a resume-grounded letter template (per §4) measured against the LLM-judge rubric in §7.

If, after prompt iteration, the filter still mis-scored a *consistent* class of postings, the escalation path is a small fine-tune of the 8B classifier on the labeled eval set — but only after prompting is demonstrably exhausted.

## 7. Evaluation metrics

The code emits operational counters today, not quality metrics — `ScrapeResponse` returns `jobs_found`, `jobs_qualified`, `applications_submitted`, `skipped_duplicates`, `errors`. The metrics that *matter* for this agent:

- **Filter precision / recall (scrape coverage & filtering quality).** Against the §3 labeled set: precision = of jobs the agent kept, how many a human agrees qualify (guards against wasting applications on bad-fit roles); recall = of truly-qualifying jobs, how many it caught (guards against missing good gigs). For a job *application* agent, **precision is the priority** — a false-positive application costs reputation.
- **Tailoring / application relevance quality.** An LLM-judge (a separate model graded against a rubric: on-topic for the role, cites EP-relevant skills, correct length, no hallucinated credentials) scoring each generated letter 1–5, validated against the §3 human-approved reference letters.
- **Scrape coverage / precision.** Fraction of board listings successfully extracted vs. dropped, and field-level accuracy (rate/location parsed correctly) — directly bounds everything downstream.
- **Response / interview rate** — the true business metric: of applications submitted, what fraction get a recruiter reply or interview.

*Illustrative numbers (not measured — no eval harness exists in the repo yet):*
- *Illustrative:* filter precision ~0.9 / recall ~0.85.
- *Illustrative:* LLM-judge tailoring score ~4.2/5.
- *Illustrative:* response rate ~8–12% vs. a ~3–5% generic-letter baseline.

## 8. Deployment architecture

**Runtime shape.** A FastAPI app (`main.py`) exposing `/health` and `POST /scrape-trigger`, served by uvicorn on **port 8011**. A single `ApplicationPipeline` is instantiated at module load and reused across requests. CORS is open (`allow_origins=["*"]`) and an `X-Process-Time` middleware stamps per-request latency.

**Pipeline data flow** (`ApplicationPipeline.run`):

```
POST /scrape-trigger  (min_rate, location, max_results)
        │
        ▼
1. SCRAPE   JobScraper.scrape_all(location, max_results)
            → scrape_indeed + scrape_linkedin  (Playwright/BeautifulSoup, currently stubbed → [])
        │   returns List[Dict] of postings
        ▼
2. FILTER   FilterAgent.filter_jobs(jobs, min_rate, location)
            → Groq llama-3.1-8b-instant @ temp 0, JSON-array output → json.loads
        │   returns qualified List[Dict] (+ match_score)
        ▼
3. GENERATE (loop over qualified[:max_results])
   3a. CoverLetterAgent.generate(job)
            → Groq llama-3.3-70b-versatile @ temp 0.4 → 150–200w letter
   3b. NotionTool.create_job_entry(job)
            → notion-client pages.create into NOTION_EP_JOBS_DB
        │   (Title/Company/Rate/Status properties)
        ▼
4. RESPOND  ScrapeResponse{jobs_found, jobs_qualified,
            applications_submitted, applications[], skipped_duplicates, errors}
```

**Integrations (real, code-grounded):**
- **Groq** via `langchain_groq.ChatGroq` (async `ainvoke`) — the two LLM calls.
- **Notion** via `notion-client` `Client.pages.create` — application tracking DB (`NOTION_EP_JOBS_DB`).
- **Slack** — `slack_sdk` is a declared dependency and `SLACK_WEBHOOK_URL` is configured for run notifications, though no Slack call is wired into the pipeline in the current source.
- **Playwright + BeautifulSoup + httpx** — declared scraping stack (extraction not yet implemented).
- **APScheduler** is a dependency, signposting the intended deployment mode: a **scheduled/cron trigger** firing `/scrape-trigger` on an interval rather than purely manual invocation.

**Where it runs.** `infra/main.bicep` provisions an **Azure Container App**: external ingress on port 8011, `GROQ_API_KEY` injected as a secret, `0.5` vCPU / `1Gi` memory, autoscaling `minReplicas: 1` → `maxReplicas: 3`. The container image is the FastAPI app. This is a stateless HTTP service — all durable state lives in Notion, which is the right call for a scrape-and-forget agent.

**Submit-vs-queue note:** despite the "auto-apply" framing, the current pipeline *does not submit applications to job boards* — it generates the letter and records the application in Notion with `status: "applied"`. In practice that makes Notion a **review/queue** the human acts on, which is a safer default than blind auto-submission (see §10).

## 9. Business impact

*All figures below are Illustrative — there is no measurement harness in the repo.*

- *Illustrative:* collapses ~5–8 hours/week of manual board-trawling and letter-writing to a single scheduled run plus a short Notion review pass.
- *Illustrative:* ~20–40 qualified applications/day processed end-to-end (bounded by `max_results` and scrape coverage), versus a realistic manual ceiling of a handful.
- *Illustrative:* ~80% reduction in time-to-application, improving the odds of being early on time-sensitive EP postings.
- *Illustrative:* response-rate lift to ~8–12% (vs. ~3–5% generic baseline) from per-role tailored letters.

The defensible, non-illustrative claim: the architecture removes the two highest-effort manual steps (semantic screening and per-role writing) while keeping a human checkpoint in Notion, so throughput rises without surrendering control over what actually gets sent.

## 10. Lessons learned

- **Fragile structured output is the top risk.** `filter_jobs` does a raw `json.loads(response.content)` with no schema validation or repair. One stray token wraps the run in a `try/except` that — note the bug-shaped behavior — `return jobs` *unfiltered* on failure, silently defeating the filter. Fixes: LangChain's `with_structured_output` / a Pydantic-validated parser, or a JSON-mode model call. This is the first thing I'd harden.
- **Match the model to the task, not to the brand.** The 8B-for-filter / 70B-for-letter split is the clearest design win — it's how you keep an LLM pipeline cheap and fast without sacrificing the output that customers see.
- **Stubs vs. claims.** The README/INTERVIEW notes describe pagination, rate-limiting, and title+company+location dedup hashing — but the scraper returns `[]` and `skipped_duplicates` is hardcoded to `0`. Honest framing in an interview: the *orchestration and contracts* are built and tested; the scraping extractor and dedup are the unfinished edges. Claiming dedup works when `skipped_duplicates: 0` is a constant would be a credibility risk.
- **Keep a human in the loop for irreversible actions.** Treating Notion as a review queue rather than auto-submitting to boards is the right safety posture for an agent that acts in someone's professional name — auto-submission should be opt-in and gated.
- **Open CORS and a public ingress** (`allow_origins=["*"]`, external Container App) are fine for a demo but would need auth before this faces the internet — anyone could trigger paid LLM runs.
- **The pipeline is correctly un-agentic.** For a fixed linear flow, plain orchestration beats an LLM tool-use loop on latency, cost, and debuggability. LangGraph is a dependency but the flow doesn't yet need a graph; reach for it only when conditional branching/retries justify it.

## Likely follow-up questions

1. **"Your filter does `json.loads` on raw model output — what happens when parsing fails, and is that safe?"** → It falls into `except` and returns the *unfiltered* job list, so a parse error silently disables the filter; I'd replace it with `with_structured_output`/Pydantic validation and fail closed.
2. **"Why an 8B model for filtering but a 70B for the cover letter?"** → Filtering is high-volume, latency-sensitive, and shallow (cheap fast model at temp 0); letter quality is customer-facing and low-volume (larger model at temp 0.4) — match cost to task.
3. **"How do you prevent applying to the same job twice?"** → Not implemented today (`skipped_duplicates` is constant 0); I'd hash title+company+location and check the Notion DB before generating/recording — the design is described but the code isn't wired.
4. **"How would you actually evaluate that the cover letters are good?"** → LLM-judge against a rubric (on-topic, real EP skills, correct length, no hallucinated credentials) validated on ~20–30 human-approved reference letters, plus the real-world response/interview rate.
5. **"The cover-letter prompt hard-codes a generic EP persona — how do you make letters specific to the actual candidate?"** → Inject the candidate's structured resume/profile as a context block so the model cites real certifications and assignments, and add a job-summary field to the filter output for richer grounding.
6. **"This is billed as 'auto-apply' but nothing is submitted to a job board — defend that."** → Intentional: Notion acts as a human review queue; irreversible actions in a person's name should be opt-in and gated, not blind-fired.
7. **"How would you schedule and scale this, and what breaks first under load?"** → APScheduler (declared) fires `/scrape-trigger` on a cron; the Azure Container App autoscales 1→3 replicas; the first bottleneck is sequential LLM calls in the per-job loop — I'd batch/parallelize generation and add rate-limit/backoff against Groq and the boards.
8. **"Why Groq + open-weight Llama instead of a frontier proprietary API?"** → Throughput and cost predictability for a batch screen-and-draft workload that doesn't need frontier reasoning; the trade is some peak quality for speed and price, which suits this task.

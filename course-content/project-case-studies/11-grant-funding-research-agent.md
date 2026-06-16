# Grant Funding Research Agent — Case Study

**30-second pitch:** A FastAPI research agent that scrapes public grant sources (Grants.gov, SBA), uses Groq-hosted LLaMA models to extract structured grant fields and score each opportunity 0–100 against a candidate organization's profile, then returns the relevant, deduplicated set for tracking in Notion and alerting via Slack. The hard part isn't fetching pages — it's turning messy listing text into comparable structured records and producing a defensible relevance ranking for a small-business or veteran-owned applicant.

> **Implementation honesty note (grounded in code):** The pipeline, models, prompts, and LLM wiring are real (`src/grant_research/`). The scraper methods (`scrape_grants_gov`, `scrape_sba`) are currently **stubs returning `[]`**, and the Notion/Slack/APScheduler integrations are declared as dependencies and described in the README but are **not yet wired into `ResearchPipeline.run`**. Where this case study describes those paths as "designed," that reflects the intended architecture the code is scaffolded toward, not shipped behavior. All performance numbers are labeled `*Illustrative:*`.

---

## 1. Problem statement

Small businesses — especially veteran-owned ones — leave significant grant money unclaimed because discovering and qualifying opportunities is manual and slow. The relevant grants are scattered across federal portals (Grants.gov), agency sites (SBA), and niche veteran-focused directories. Each listing has a different layout, inconsistent fields (amount, deadline, eligibility), and the eligibility rules are written in prose. A founder has to read dozens of listings, mentally filter on "do I even qualify and is the award worth the paperwork," and re-check periodically because deadlines roll.

The system, as defined by the API contract in `models.py`, takes a `ResearchCriteria` profile:

```python
class ResearchCriteria(BaseModel):
    veteran_owned: bool = False
    business_type: str = "small_business"
    industry: List[str] = []
    min_amount: int = 0
```

and returns a `ResearchResponse` of relevant `Grant` records (title, source, amount, deadline, eligibility, application URL, `relevance_score`) plus counts (`grants_found`, `grants_relevant`, `grants_new`, `duplicates_skipped`). The goal: collapse hours of manual portal-trawling into one POST to `/research/run`.

## 2. Why AI/ML was needed

Two sub-problems resist deterministic code:

1. **Extraction from heterogeneous, unstructured listings.** Every source formats grants differently. A rules/regex parser would need a brittle per-source template that breaks on every site redesign. The `SummarizerAgent` instead asks an LLM to extract a fixed JSON schema (`title`, `amount`, `deadline` as `YYYY-MM-DD`, `eligibility`, `application_url`) from raw listing text — one prompt generalizes across sources.

2. **Relevance scoring against fuzzy eligibility.** Whether a "small business veteran set-aside in cybersecurity" grant matches a profile of `{veteran_owned: true, industry: ["security"]}` is a semantic judgment, not a keyword match. Eligibility is prose ("must be a service-disabled veteran-owned small business in an underserved area"). The `FilterAgent` delegates this to the LLM, which scores 0–100 and explains its reasoning — something a `WHERE` clause cannot do.

The deterministic parts (HTTP fetch, dedup hashing, threshold filtering, persistence) stay in plain Python. AI is used surgically only where natural-language understanding is unavoidable.

## 3. Dataset → Knowledge corpus & eval set

**There is no training dataset.** This is a retrieval-and-reasoning system, so the "data" is the live grant corpus plus the candidate profile.

**Grant sources (the corpus).** From `tools/scraper.py` and the README:
- **Grants.gov** — federal grants portal; scraped with keyword seeds `["veteran", "small business"]`.
- **SBA.gov** — Small Business Administration funding pages.
- README also names veteran-focused directories as a target source.

The README's rationale (echoed in `INTERVIEW.md` Q3) for scraping over API: Grants.gov's API exposes limited filtering and omits the full eligibility prose, which is exactly the text the relevance scorer needs. So the corpus is acquired via **Playwright (chromium) + BeautifulSoup** (declared in `pyproject.toml`), giving access to the rendered eligibility text. *(In the committed code these scrapers return `[]`; the corpus pipeline is scaffolded, not populated.)*

**Candidate org profile.** The `ResearchCriteria` object — veteran status, business type, industry list, minimum award amount. This is the "query side" of the match.

**Building an eval set (profile → relevant-grants).** This is the part I'd invest in for a senior-level system, because the model is only as trustworthy as our labels:
- **Sampling.** Snapshot ~200–500 real listings across all sources. Construct ~20–30 representative profiles spanning the criteria space (veteran-owned vs not, several industries, a range of `min_amount` thresholds).
- **Gold labels.** For each (profile, grant) pair, a human SME labels a binary `relevant` and ideally a graded relevance (0=irrelevant, 1=marginal, 2=strong) so we can compute ranking metrics, not just classification. The graded label is what makes nDCG meaningful.
- **Eligibility ground truth.** Separately, hand-extract the gold structured fields (amount, deadline, eligibility) for an extraction-accuracy eval — decoupled from the relevance eval so a bad extractor doesn't silently corrupt the ranking eval.
- **Freshness slice.** Keep a held-out time slice of *new* listings to test that scoring generalizes to grants the prompt was never tuned on.
- **Negative/adversarial cases.** Include grants that look relevant by keywords but fail a hard eligibility gate (e.g., wrong state, expired deadline, non-veteran set-aside) — these catch the model rewarding surface keyword overlap.

## 4. Feature engineering → Prompt & context engineering

There's no feature vector; the "features" are the prompts and the structured context fed to two specialized agents.

**Query / search construction.** Source acquisition is keyword-seeded (`["veteran", "small business"]` in `scrape_all`). A production version would template these seeds from the `industry` list and `business_type` so the crawl is profile-aware rather than fixed.

**Extraction prompt (`SummarizerAgent.SUMMARIZE_PROMPT`).** Takes raw listing text (truncated to 3000 chars to bound token cost) and demands a fixed JSON schema with a normalized date format (`YYYY-MM-DD`). Pinning the output schema is the key move — it makes downstream records comparable regardless of source layout. Run at `temperature=0.2` (low, but slightly above zero) on the **primary** model for higher-fidelity extraction.

**Matching / scoring prompt (`FilterAgent.FILTER_PROMPT`).** Injects the profile (veteran status, business type, industries, min amount) and a batch of up to 20 grants as JSON, and asks for a JSON array of `{title, relevance_score 0-100, reasoning}`. Design choices worth defending in an interview:
- **Batched scoring** (`grants[:20]`) — one call scores many grants, amortizing latency/cost, at the risk of cross-contamination between items and a token ceiling. A senior trade-off: batch for throughput, cap the batch to stay within context and keep per-item attention.
- **`temperature=0`** — scoring must be deterministic and reproducible; we don't want a grant's score to jitter between runs.
- **`reasoning` field** — forces the model to justify each score, which both improves calibration (a soft chain-of-thought) and gives a human an audit trail.

**Structured output & tool/integration definitions.**
- Output contracts are enforced by the Pydantic `Grant` / `ResearchResponse` models in `models.py` (fields: title, source, amount, deadline, eligibility, application_url, `relevance_score`, plus `notion_page_id` and `slack_notified` flags that anticipate the integration layer).
- The downstream "tools" are the scraper (Playwright/BeautifulSoup), and the declared **Notion** (`notion-client`) and **Slack** (`slack_sdk`) integrations for tracking and alerting, scheduled by **APScheduler** for periodic re-runs. `langgraph` is also declared, anticipating an agent-graph orchestration, though the current pipeline is a straight-line async pipeline.

**Threshold gating.** The pipeline keeps only grants with `relevance_score >= 70` (`research_pipeline.py`). That cutoff is a product decision — a precision/recall lever, not a model parameter — and should be tuned against the eval set above.

## 5. Model selection rationale

The provider is **Groq** (`langchain_groq.ChatGroq`), and the code uses a **two-model tiering** (`config.py`):

| Role | Model | Used by | Temp | Why |
|------|-------|---------|------|-----|
| Fast/cheap | `llama-3.1-8b-instant` | `FilterAgent` (relevance scoring, batched) | 0 | Scoring is high-volume and comparatively simple; the 8B instant model on Groq's LPU gives very low latency and cost per scored grant. Determinism via temp 0. |
| Primary | `llama-3.3-70b-versatile` | `SummarizerAgent` (field extraction) | 0.2 | Extraction needs stronger reading comprehension to pull clean fields from messy prose; the 70B model is the quality tier, reserved for the lower-volume extraction step. |

**Why this split is the right trade-off:** put the expensive 70B model only on the task that needs comprehension (extraction over a single noisy document), and the cheap 8B model on the repetitive task (scoring a batch of already-structured grants). This is classic cost/latency routing — most senior reviewers would expect exactly this, and Groq's draw is throughput/latency on open-weight LLaMA models rather than frontier reasoning.

**Trade-offs / risks I'd raise:** open-weight LLaMA models are weaker at strict JSON adherence than some hosted alternatives — `response.content` is parsed with a bare `json.loads`, which will throw on any prose preamble or markdown fences. There's no JSON-mode/grammar constraint and no schema-repair retry; that's the first robustness gap I'd close (structured-output mode or a tolerant parser + one repair pass). On search tooling, the choice was raw scraping over the Grants.gov API specifically to capture eligibility prose — defensible, but it trades robustness (sites change) for completeness.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training, and that's correct here.** Fine-tuning would be the wrong tool: (1) the grant corpus is live and changes daily, so any learned weights go stale; (2) the task is extraction + judgment over arbitrary new text, which instruction-following models already do zero-shot; (3) we have no labeled volume to justify a training run, and the labels we do build are better spent as an eval harness than as training data.

So the "training loop" is **prompt iteration** against the eval set from §3:
- Iterate the extraction prompt until JSON-schema conformance and date normalization are reliable; add explicit "return only JSON" constraints and few-shot exemplars if `json.loads` failures persist.
- Calibrate the scoring prompt so `relevance_score` separates the gold-relevant from the gold-irrelevant cleanly around the 70 cutoff; the `reasoning` field is the debugging surface for miscalibration.
- Tune the `>=70` threshold and the batch size (currently 20) empirically for the precision/recall point the product wants.

If anything were ever trained, the candidate would be a small, cheap **relevance classifier** distilled from LLM scores once enough labels accumulate — to drop the per-grant LLM cost — but only after the prompt approach is proven.

## 7. Evaluation metrics

Evaluation splits cleanly into two independent problems; conflating them hides which stage is failing.

**A. Relevance ranking quality** (the user-facing output). Against the graded eval set:
- **Precision@k / Recall** of grants the model marks relevant (score ≥ 70) vs human labels. Precision matters most — a founder's trust collapses fast if top results are junk.
- **nDCG@k** using the graded (0/1/2) labels — rewards putting *strongly* relevant grants above marginal ones, which is what `relevance_score` is supposed to do.
- **MRR** — how high the first truly-relevant grant lands, since users scan top-down.
- **Threshold sweep** — precision/recall as the 70 cutoff moves, to pick the operating point.

**B. Extraction accuracy** (the structured-record quality). Against hand-extracted gold fields:
- Per-field exact/normalized match for `amount`, `deadline`, `application_url`; fuzzy/semantic match for `eligibility`.
- JSON-parse success rate (currently a real failure mode given bare `json.loads`).

**Illustrative targets** (not measured — no eval harness is implemented in the repo):
- *Illustrative:* extraction field accuracy ~90% on `deadline`/`amount`, lower on free-text `eligibility`.
- *Illustrative:* relevance precision@10 ~0.8, nDCG@10 ~0.85 after prompt tuning.
- *Illustrative:* JSON-parse success ~95% before adding schema-repair, ~99%+ after.

All four numbers are placeholders to show the shape of a target, not results.

## 8. Deployment architecture

**Flow:** `POST /research/run {criteria}` → `ResearchPipeline.run`:

```
criteria ──► GrantScraper.scrape_all()        # Playwright+BS4 over Grants.gov, SBA  (stub: returns [])
         ──► FilterAgent.filter_grants()       # Groq llama-3.1-8b-instant, batch≤20, scores 0–100
         ──► filter score >= 70                 # keep relevant
         ──► (designed) SummarizerAgent         # Groq llama-3.3-70b extracts structured fields
         ──► (designed) dedup by hash(title+source+deadline)   # INTERVIEW.md Q2
         ──► (designed) Notion upsert + Slack alert            # notion-client / slack_sdk
         ──► ResearchResponse{counts, grants[]}
```

**Where it runs.** A **FastAPI** app (`main.py`) served by **uvicorn** on port 8016, with permissive CORS, a `/health` endpoint, and an `X-Process-Time` latency-header middleware. The pipeline is instantiated once at module load and called per request; all LLM and scraper calls are `async`. **APScheduler** is declared to drive periodic re-runs (so new grants surface without a manual call), and **langgraph** is declared for future graph-based orchestration. Configuration (Groq/Notion/Slack keys, model names) is environment-driven via `pydantic-settings` (`config.py`) with an LRU-cached settings singleton.

**Honest gaps in the deployed path:** error handling in both agents swallows failures and returns the input/empty (`FilterAgent` returns the *unscored* grants on exception; `SummarizerAgent` returns `{}`) — fine for a demo, but in production a failed scoring call silently passing grants through is a correctness bug. The dedup, Notion, and Slack steps from the README/`INTERVIEW.md` are not present in `ResearchPipeline.run` yet (`duplicates_skipped` is hardcoded to 0, `notion_page_id`/`slack_notified` are always null/false).

## 9. Business impact

All figures illustrative — there is no telemetry in the repo.

- *Illustrative:* reduces grant discovery from ~4–6 hours/week of manual portal-trawling to a single automated scheduled run.
- *Illustrative:* surfaces 5–15 relevant opportunities per run for a veteran-owned small business that would otherwise be missed.
- *Illustrative:* even one additional ~$25k award found per quarter dwarfs the operating cost (Groq inference on 8B/70B LLaMA is cents per run).
- *Illustrative:* Slack alerting + Notion tracking turn "I forgot to check" into a managed pipeline, cutting missed-deadline losses.

The honest pitch: the value is **recall of opportunities** (finding grants a human wouldn't) combined with **precision of the shortlist** (not wasting the founder's time), and the scheduled re-run is what converts a one-off search into ongoing coverage.

## 10. Lessons learned

- **Separate extraction from scoring.** Two agents, two models, two evals. Bundling them would make failures undiagnosable and force one temperature/model on two different tasks.
- **Model tiering is a real lever.** Cheap 8B for high-volume scoring, expensive 70B for comprehension-heavy extraction — measurable cost savings with little quality loss, but only valid because the tasks genuinely differ in difficulty.
- **Bare `json.loads` on LLM output is fragile.** Open-weight models wrap JSON in prose/fences; production needs structured-output mode or a tolerant parser plus a repair retry. This is the single highest-ROI hardening item.
- **Silent fallbacks hide bugs.** Returning unscored grants on a scoring exception inflates `grants_found`-style trust; failures should be surfaced, not swallowed.
- **Scraping vs API is a deliberate trade.** Choosing scraping to capture eligibility prose buys data completeness at the cost of fragility — acceptable, but it makes a per-source extraction eval and monitoring non-optional.
- **The eval set is the product.** Without graded profile→grant labels, "relevance_score ≥ 70" is an unvalidated guess. The threshold and batch size should be set by data, not vibes.
- **Ship the integration layer the contract promises.** The `Grant` model exposes `notion_page_id`/`slack_notified` and `duplicates_skipped`, but the pipeline doesn't populate them yet — the schema is writing a check the code hasn't cashed.

## Likely follow-up questions

1. **Your scorer returns the unscored grants on exception — what's wrong with that?** → It silently passes unfiltered grants downstream as if scored; failures should raise/flag, not degrade to "everything is relevant."
2. **You parse LLM output with `json.loads` — how do you make that robust?** → Groq structured-output/JSON mode, or a tolerant parser that strips fences plus one schema-repair retry against the Pydantic model.
3. **Why two different LLaMA models, and how would you prove the split is worth it?** → 8B-instant for high-volume scoring, 70B-versatile for comprehension-heavy extraction; prove it by ablating (run extraction on 8B) and comparing field accuracy vs cost on the eval set.
4. **How do you evaluate ranking quality, not just classification?** → Graded (0/1/2) human labels and nDCG@k / MRR, plus a precision/recall threshold sweep around the 70 cutoff.
5. **Batching 20 grants in one scoring call — risks?** → Token ceiling and cross-item contamination; mitigate by capping batch size, and validate per-item scores are stable vs single-item scoring on a sample.
6. **How do you dedup across runs and sources?** → Hash of `title+source+deadline` (per `INTERVIEW.md`); upsert against stored hashes before writing to Notion — currently designed but not implemented (`duplicates_skipped` is hardcoded 0).
7. **Scraping breaks when sites redesign — how do you detect and contain that?** → Per-source extraction-accuracy monitoring and JSON-parse-rate alerts; isolate each scraper so one broken source doesn't fail the run.
8. **Why not fine-tune a relevance model?** → Live, daily-changing corpus and no labeled volume; zero-shot instruction-following plus a tuned prompt/threshold is cheaper and doesn't go stale — distill a classifier only after labels accumulate.

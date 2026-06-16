# Tactical Affiliate Funnel — Case Study

**30-second pitch:** Tactical Affiliate Funnel is a high-volume LLM content factory for affiliate marketing. Given a single product (name, description, audience, price, affiliate link), it generates multiple platform-tailored social caption variants (Instagram, Twitter/X, Facebook) via Groq-hosted LLMs through LangChain, stamps each push with a UTM-tagged tracking URL, and returns a structured payload ready to publish. The design goal is throughput with attribution: produce dozens of A/B-testable creative variants per product and tie every click back to source, campaign, and medium.

---

## 1. Problem statement

Affiliate marketers live and die by two numbers: how many creative assets they can put in market, and how reliably they can attribute a conversion back to the asset that drove it. Writing platform-specific captions by hand does not scale — Instagram wants hashtags and a softer voice, Twitter/X has a 280-character ceiling and rewards punch, Facebook wants conversational length. Multiply that by N products, M platforms, and K variants per platform for A/B testing, and a human copywriter becomes the bottleneck.

The system solves a narrow, well-scoped problem: **turn one structured product record into many platform-correct caption variants, each carrying a tracking URL that makes downstream conversion measurable.** The repo's own description frames it precisely — "Multi-platform affiliate content generator with A/B testing and click tracking" (`pyproject.toml`).

## 2. Why AI/ML was needed

The core task is open-ended natural-language generation under per-platform constraints — exactly where an LLM beats templating. A Jinja2 template (the project ships `jinja2` as a dependency, used for landing-page rendering) can fill slots, but it cannot write three *distinct* punchy 280-character hooks for a product it has never seen, vary tone per audience, or pick context-appropriate hashtags. The variety requirement is the whole point: A/B testing only works if the variants are genuinely different creative bets, not the same sentence reworded.

So the LLM owns generation; deterministic code owns everything that must be correct and auditable — tracking-URL construction (`tools/tracking.py`), schema validation (`models.py`), and orchestration (`pipelines/funnel_pipeline.py`). That split is deliberate: never ask the model to do arithmetic, build URLs, or enforce invariants you can guarantee in code.

## 3. Dataset → Knowledge corpus & eval set

**There is no training corpus.** This is a zero-shot generation system; the "input data" is a structured product record, defined in `models.py` as the `Product` model:

- `name`, `description`, `affiliate_link`, `target_audience`, `price`

The generator (`content_generator.py`) consumes a subset of these (`name`, `description`, `target_audience`, `price`) plus a `platform` string and a `variants` count. Product records are expected to come from a Notion products database (`notion-client` dependency; `notion_products_db` / `NOTION_PRODUCTS_DB` in `config.py` and `.env.example`) — Notion is the content management source of record, the funnel is the generator.

**How I'd build an eval set (not present in the repo today):**

- **Content-quality eval set:** a fixed panel of ~30–50 representative products spanning categories, price points, and audiences. For each, freeze the generated variants and score them (see §7). This is the regression harness — re-run it on every prompt change.
- **Conversion holdout:** content quality is a proxy; the real metric is clicks/conversions. Reserve a slice of live products as a holdout where variants are published with their tracking URLs (UTM-tagged) and measured against a control (human-written or a baseline prompt). Because every asset already carries `utm_source`/`utm_campaign`/`utm_medium`, attribution is the cheap part — the discipline is holding the control constant.

## 4. Feature engineering → Prompt & context engineering

This is where the system actually lives. There is one prompt, `CONTENT_PROMPT` in `content_generator.py`, parameterized per call:

**Per-stage / per-platform conditioning.** The prompt is called once per platform inside the pipeline loop (`funnel_pipeline.py`), and the prompt body bakes in platform-specific constraints:

- Instagram: 2–3 sentences + 5–8 hashtags, with hashtags in a *separate* `hashtags` field
- Twitter/X: under 280 characters, punchy
- Facebook: 2–4 sentences, conversational

So "feature engineering" here is **context injection** — the product's `name`, `description`, `target_audience`, and `price` are formatted into the prompt, and the platform name selects which rule set the model should honor.

**Structured output.** The prompt instructs the model to return a JSON array of `{"variant", "caption", "hashtags"}` objects, which `content_generator.py` parses with `json.loads(response.content)`. The shape mirrors the `ContentVariant` Pydantic model (`variant`, `caption`, `hashtags`). This is prompt-instructed JSON, not a hard-enforced tool/function schema — an honest weakness called out in §10.

**Brand / tone constraints.** Tone is currently encoded implicitly: per-platform voice rules ("punchy", "conversational") plus `temperature=0.6` for controlled variety. There is no brand style guide, banned-words list, or disclosure-language requirement in the prompt today — a gap a senior reviewer should flag for a marketing system.

**Variant strategy for A/B testing.** A single call asks for `variants` (default 3) labeled "A", "B", … in one response. That is cheaper than N independent calls and lets the model deliberately diversify, but it couples the variants — a topic for §6.

**Tool / integration definitions.** The only "tool" is `TrackingTool.generate_tracking_url` (`tools/tracking.py`). It is *not* an LLM-callable tool; it is deterministic post-processing invoked by the pipeline. It builds `{tracking_domain}/go/{slug}?utm_source=...&utm_campaign=spring2026&utm_medium=affiliate`, slugifying the product name and URL-encoding params with `urllib.parse.urlencode`. Keeping UTM construction out of the model's hands is the right call — it must be byte-correct for attribution to work.

## 5. Model selection rationale

The system uses **Groq** as the inference provider via LangChain's `ChatGroq` (`langchain-groq`). Two models are configured in `config.py`:

- `groq_model_quality = "openai/gpt-oss-120b"` — the large open-weight model, used by `ContentGeneratorAgent` for the actual caption generation.
- `groq_model_fast = "llama-3.1-8b-instant"` — a small fast model, configured but **not yet wired into the generation path** (reserved for cheap/high-throughput steps such as bulk re-ranking, classification, or quick rewrites).

The trade-off for high-volume content is the classic cost/latency/quality triangle:

- **Quality:** captions are short and the failure mode (a flat or off-tone variant) is low-stakes, so a 120B-class model is comfortably sufficient — you do not need a frontier flagship.
- **Latency/throughput:** Groq's inference is chosen specifically for speed at volume, which matters when you are fanning out across products × platforms × variants. Batching variants into one call per platform (§4) further cuts round-trips.
- **Cost:** open-weight models on Groq are cheap per token relative to closed flagships, and captions are short — cost per asset is low (quantified illustratively in §7/§9).

Having a dedicated *fast* model in config signals the intended tiering: spend the quality model on creative generation, reserve the 8B instant model for the cheap mechanical work.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training. No fine-tuning. This is correct for this problem.** Fine-tuning buys you consistency on a narrow style at the cost of a labeling pipeline, training infra, and a redeploy on every change. Here the requirements are the opposite of narrow — you *want* variety across products and platforms, the constraints are simple enough to state in a prompt, and the per-platform rules change faster than any fine-tune cycle could keep up. Prompting is the right tool.

**Prompt iteration is the development loop.** With one prompt (`CONTENT_PROMPT`) and a temperature dial, iteration means: tighten the per-platform rules, harden the JSON instruction, add brand/tone/disclosure constraints, and re-run the §3 quality eval set to catch regressions.

**A/B testing of prompts (and of content).** The system is built for two layers of A/B testing:

1. **Content-level:** the multi-variant output (A/B/C) is published and the tracking URLs reveal which creative converts.
2. **Prompt-level:** competing prompt versions can be run on the same products and compared on downstream click-through, since every asset is attributable by UTM. The honest caveat: the current single shared `utm_campaign="spring2026"` and one tracking URL per *product* (not per variant) means variant-level attribution needs finer instrumentation than ships today (see §10).

## 7. Evaluation metrics

Three layers, from cheapest/fastest to most business-true:

1. **Content quality rating (offline).** Rubric-scored on the §3 eval panel — constraint compliance (Twitter under 280 chars, Instagram hashtag count in range, valid JSON parse), plus a 1–5 LLM-judge or human rating on hook strength, tone fit, and CTA presence. JSON-parse success rate is a free, hard metric to track since `json.loads` failure currently means an empty result.
2. **Click-through rate (online).** Derived directly from the UTM-tagged tracking URLs (`utm_source`, `utm_campaign`, `utm_medium`) — clicks per impression by platform and campaign.
3. **Conversion rate (online).** Affiliate conversions attributed back through the same tracking URL to source/campaign/medium.

*Illustrative targets (not measured — no eval harness ships in the repo):*

- *Illustrative:* JSON-parse / constraint-compliance rate ≥ 98%
- *Illustrative:* content-quality rating ≥ 4.0 / 5.0 on the eval panel
- *Illustrative:* cost per asset ≈ $0.0005–$0.002 (short captions on an open-weight Groq model, batched per platform)
- *Illustrative:* click-through uplift of AI variants vs. baseline copy, measured on the holdout

## 8. Deployment architecture

The intended runtime is a FastAPI service (`fastapi` + `uvicorn[standard]` in `pyproject.toml`; request/response contracts already defined as `GenerateRequest` / `GenerateResponse` in `models.py`), though the HTTP route layer is not in the files reviewed — the orchestration core is the `FunnelPipeline`.

Flow:

```
Notion products DB ──▶ GenerateRequest (product, platforms, variants_per_platform)
                              │
                              ▼
                    FunnelPipeline.generate_content   (pipelines/funnel_pipeline.py)
                              │
         ┌────────────────────┴─────────────────────┐
         ▼                                            ▼
  ContentGeneratorAgent  (per platform, looped)   TrackingTool.generate_tracking_url
   ChatGroq → openai/gpt-oss-120b                  UTM-tagged URL (deterministic)
   JSON array of variants                                 │
         └────────────────────┬─────────────────────┘
                              ▼
                    GenerateResponse
            { content_generated, products:[{ platforms, tracking_url,
                                              landing_page_updated }] }
                              │
                              ▼
          publish (social platforms) + landing page (Jinja2)
```

- **Generation:** one `ChatGroq.ainvoke` call per platform (async), so a product fans out across its platform list concurrently-friendly. Inference is offloaded to Groq's hosted API — no GPU to run.
- **Tracking:** synchronous, deterministic, in-process.
- **Landing page:** `landing_page_updated` is currently hardcoded `True` in the pipeline — a placeholder; `jinja2` is on hand to render the actual page.
- **Config / secrets:** `pydantic-settings` loads `GROQ_API_KEY`, `NOTION_API_KEY`, `TRACKING_DOMAIN` etc. from `.env` (`config.py`).

## 9. Business impact

*All figures below are **Illustrative** — the repo contains no measured production metrics.*

- *Illustrative:* one product × 3 platforms × 3 variants = **9 ready-to-publish assets per product per run**, generated in seconds. At a modest catalog cadence this is hundreds to low-thousands of **assets/day** versus a handful a human copywriter produces.
- *Illustrative:* **conversion uplift** — multi-variant A/B testing with UTM attribution lets you keep winners and kill losers; a +10–25% lift in click-through over a single hand-written caption is a reasonable target to validate on the holdout.
- *Illustrative:* **cost saved** — at roughly $0.0005–$0.002 per asset (short captions, open-weight Groq model), the model spend is negligible against the copywriter hours it displaces; the dominant saving is throughput, not per-token price.

The durable business value is the **attribution loop**: because every asset ships with source/campaign/medium baked into its URL, marketing spend becomes measurable and the content engine becomes self-optimizing.

## 10. Lessons learned

- **Keep deterministic work out of the model.** UTM construction, slugification, and schema are in plain Python (`tracking.py`, `models.py`). Attribution must be byte-correct; never trust an LLM to build a tracking URL.
- **Prompt-instructed JSON is a liability at volume.** `json.loads(response.content)` with a broad `except` that returns `[]` means a single malformed response silently yields zero content. At scale this needs structured-output enforcement (a tool/function-calling schema or a constrained decoder) and a retry, not a swallowed exception — otherwise failures are invisible.
- **Variant-level attribution is missing.** One `tracking_url` per product and a hardcoded `utm_campaign="spring2026"` mean you can attribute by platform but not cleanly by variant — yet variant A/B testing is the headline feature. Per-variant `utm_content` is the obvious fix.
- **`landing_page_updated: True` is a hardcoded promise, not a fact.** Don't let placeholder flags leak into a response contract a downstream system might trust.
- **The fast model is paid for but unused.** `llama-3.1-8b-instant` is configured and never called; either wire it into the cheap path (re-ranking, classification) or drop it.
- **Responsible-AI / disclosure is the real exposure.** This generates *marketing* copy at scale with **no brand-safety guardrails, no banned-claims list, and no AI-disclosure language** in the prompt. For affiliate content this matters concretely: false or unsubstantiated product claims, undisclosed affiliate relationships (an FTC concern in the US and analogous rules elsewhere), and platform policies on AI-generated content. A senior owner should add (1) a claims/compliance constraint and review step, (2) required affiliate-disclosure text in every caption, and (3) a human-in-the-loop gate before publish for regulated categories. Speed without these guardrails is a liability, not a feature.

## Likely follow-up questions

1. **The JSON parse fails silently and returns `[]` — how would you make generation reliable at volume?** → Switch to provider structured-output / tool-schema enforcement, validate against the `ContentVariant` model, add bounded retries with repair, and emit a metric on parse-failure rate instead of swallowing it.
2. **How do you actually attribute a conversion to *variant B* specifically?** → Add `utm_content=<variant_id>` per variant (and a per-variant tracking URL); the current per-product URL + shared `spring2026` campaign can't separate variants.
3. **Why Groq + `openai/gpt-oss-120b` instead of a closed flagship or a smaller model?** → Short, low-stakes captions don't need a frontier model; Groq gives high throughput at low cost, and the 8B fast model is reserved for cheap mechanical steps — quality where it pays, speed everywhere else.
4. **You batch all variants in one call — what does that cost you?** → Fewer round-trips and deliberate diversity, but coupled variants and a single point of failure (one bad response loses the whole platform); independent calls trade cost for isolation and true independence.
5. **How would you build the eval set and prove the AI copy actually converts better?** → Frozen quality panel for offline regression (constraint + LLM-judge scoring) plus a live holdout against a human/baseline control, compared on UTM-attributed click-through and conversion.
6. **What's your responsible-AI posture for AI-generated affiliate marketing?** → Mandatory affiliate-disclosure text, a banned-claims/compliance constraint with human review for regulated categories, and adherence to each platform's AI-content policy — none of which exists in the prompt today.
7. **Temperature is 0.6 — how did you land there and would you tune it per platform?** → It balances variety against on-brand coherence; I'd A/B it per platform (lower for Twitter's tight constraint, higher for Instagram creativity) and let the quality eval decide.
8. **Where are the bottlenecks if you 100× the product catalog?** → LLM call fan-out (mitigate with async batching and the fast model for non-creative steps), Groq rate limits/quota, Notion read throughput, and the absence of a queue/worker tier between the API and the generation loop.

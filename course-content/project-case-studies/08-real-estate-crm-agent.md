# Real Estate CRM Agent — Case Study

**30-second pitch:** A FastAPI webhook service that ingests inbound real-estate leads, uses a Groq-hosted Llama 3.3 70B model to score and categorize each lead (0–100, hot/warm/cold), and immediately kicks off a Day-0 outreach touch over Twilio SMS and SendGrid email. It is designed to feed a Notion "JMG Leads" CRM and escalate hot leads to the sales team, replacing the manual triage that normally happens hours or days after a form submission.

---

## 1. Problem statement

Real estate agents live and die by lead response time. When a prospect fills out a web form ("Looking for a 3BR home in Oakland"), the probability of conversion drops sharply with every minute that passes before a human responds. The reality at a small brokerage (here, "JMG Real Estate") is that:

- Leads arrive at all hours through a website form (`source = "website_form"` is the default in `LeadInput`).
- A human has to read each message, guess at intent and budget, decide whether the lead is worth chasing, and then manually fire off a text and an email.
- High-intent ("hot") leads sit in an inbox next to tire-kickers, with no triage, so the agent's scarce time is spread evenly across leads of wildly different value.

The system in this repo targets the **first-touch + triage** slice of that problem: qualify the lead and send the Day-0 SMS + email within the request lifecycle of the inbound webhook, and flag hot leads for human escalation.

## 2. Why AI/ML was needed

The qualification step is the part that genuinely needs an LLM rather than a rules table. Look at the actual input contract (`models.py › LeadInput`): the structured fields (`property_interest`, `budget_range`) are optional and frequently empty; the signal lives in a free-text `message` field. The qualifier prompt (`agents/qualifier.py`) explicitly asks the model to weigh *"budget clarity, timeline urgency, pre-approval status, specific criteria"* — these are concepts a prospect expresses in natural language ("we're pre-approved up to 800k and need to move before September"), not in clean form fields.

A pure rule engine would require brittle keyword matching and would miss paraphrases ("got the financing sorted" == pre-approved). An LLM does zero-shot intent and urgency extraction from a single message and emits a normalized score, which is exactly the gap between unstructured intake and a structured CRM record. The outreach copy (the Day-0 SMS and email) is currently templated, but the same reasoning extends to LLM-generated, lead-specific outreach (covered in §4).

## 3. Dataset → Knowledge corpus & eval set

**There is no training dataset.** This is an inference-only, prompt-driven system. The relevant "data" is the runtime lead payload and the eval set you would build around it.

**Lead data (the live input).** From `LeadInput`:

| Field | Type | Notes |
|---|---|---|
| `source` | str | defaults to `"website_form"` |
| `name`, `email`, `phone` | str | required identity/contact fields |
| `message` | str | free text — the primary signal |
| `property_interest` | str | optional |
| `budget_range` | str | optional |

The qualifier reads all of these except `source` into the prompt.

**How I'd build a labeled eval set.** Since qualification is the model's core judgment, I would assemble a golden set of historical leads, each labeled by a senior agent with the *correct* `score` band and `category`:

1. Sample a few hundred real past leads spanning the full quality spectrum (form-spam, vague browsers, financed-and-urgent buyers).
2. Have two experienced agents independently label each as hot/warm/cold and assign a 0–100 band; reconcile disagreements to get a gold label and an inter-annotator agreement baseline (the human-vs-human ceiling).
3. Bucket-stratify the set so cold/warm/hot are all well represented — real intake is heavily cold-skewed, and an unstratified set would let a "predict warm" model look deceptively good (note the error fallback literally returns `category: "warm"`).
4. Include adversarial rows: empty `message`, contradictory signals ("budget $2M" + "just curious"), and non-English messages, to probe robustness.

This eval set is what every prompt change is regression-tested against (§7).

## 4. Feature engineering → Prompt & context engineering

This is where the engineering actually lives, since there's no model training.

**Qualification prompt + scoring schema** (`agents/qualifier.py`). The prompt is a single templated instruction that injects the six lead fields and demands a strict JSON contract:

```
Qualify this real estate lead. Score 0-100 and categorize as hot/warm/cold.

Lead Info:
Name / Email / Phone / Message / Property Interest / Budget Range

Consider: budget clarity, timeline urgency, pre-approval status, specific criteria.

Return JSON:
{ "score": <0-100>, "category": "<hot|warm|cold>", "reasoning": "<brief explanation>" }
```

Design choices worth calling out in an interview:

- **Constrained output schema.** The response is parsed with `json.loads(response.content)` and validated downstream by the `Qualification` Pydantic model (`score: int, ge=0, le=100`). The schema is the contract; the prompt's job is to make the model fill it reliably.
- **Low temperature (0.2).** Qualification is a scoring/classification task, not creative writing — you want determinism and reproducibility, so the temperature is pulled down rather than left at a chatty default.
- **`reasoning` field as a built-in audit trail.** Forcing the model to justify the score gives free explainability for the sales team and a debugging hook when a score looks wrong.
- **Graceful degradation.** On any exception (LLM error, malformed JSON), the agent returns a neutral `{"score": 50, "category": "warm", "reasoning": "Error: ..."}` instead of throwing. This keeps the webhook responsive but is a deliberate trade-off — a silent failure becomes an unremarkable "warm" lead (see Lessons Learned).

**Outreach generation prompts.** In the current code the Day-0 outreach is **template-based, not LLM-generated** (`pipelines/lead_pipeline.py`): `WELCOME_SMS` and `WELCOME_EMAIL` are Python format strings that only interpolate `{name}`. This is a defensible MVP choice — templates are zero-cost, zero-latency, and can't hallucinate a wrong price or fabricate a listing in a compliance-sensitive domain. The natural next iteration is to feed the qualifier's `reasoning` and the lead's `property_interest`/`budget_range` into a generation prompt so the first text references the actual home they asked about, gated by a guardrail prompt that forbids inventing inventory or quoting prices.

**Tool definitions.** The "tools" here are deterministic side-effect wrappers, not LLM-selected function-calls:

- `SMSTool.send_sms(to, body)` → Twilio `client.messages.create(...)` (`tools/sms_tool.py`).
- `EmailTool.send_email(to, subject, html_content, from_email)` → SendGrid `Mail(...)` + `client.send(...)` (`tools/email_tool.py`).

Both are constructed defensively: the client only initializes if the relevant credentials are present, and both methods return `False` (logging a warning) rather than raising when the integration is unconfigured. The pipeline orchestrates them directly in code rather than letting the LLM decide when to call them — a sound choice for a fixed Day-0 sequence where the steps are known in advance.

## 5. Model selection rationale

**LLM:** Groq-hosted **Llama 3.3 70B Versatile** (`groq_model_primary = "llama-3.3-70b-versatile"`), accessed via `langchain_groq.ChatGroq`. A faster fallback, **Llama 3.1 8B Instant** (`groq_model_fast = "llama-3.1-8b-instant"`), is configured but not currently wired into the qualifier.

Trade-offs behind this choice:

- **Latency.** Qualification runs *inside* the inbound webhook request, before the SMS/email fire. Groq's inference is the headline reason to pick it — its LPU serving is built for very low time-to-first-token, which matters when response speed is the entire business value proposition.
- **Cost.** Open-weight Llama on Groq is cheap per call relative to frontier closed models, and lead qualification is a high-volume, low-complexity task. Paying frontier prices for a hot/warm/cold call would be over-engineering.
- **Capability headroom.** 70B is chosen over the 8B fast model for the qualifier because reading nuance/urgency out of free text benefits from the larger model; the 8B remains available for cheaper, higher-volume tasks (e.g., bulk re-scoring or template personalization) where the quality bar is lower.

**Why an LLM for qualification vs. rules.** A rules engine ("if budget_range contains a number AND message contains 'pre-approved' → hot") is cheaper and fully deterministic, but it can't read intent from prose, can't handle synonyms/typos/paraphrase, and needs a developer to extend every time the market or messaging shifts. The LLM generalizes zero-shot across phrasings. The honest middle ground: keep a *rules backstop* for unambiguous cases (obvious spam, missing contact info) and reserve the LLM for the judgment-heavy middle — that's both cheaper and more robust than either alone.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training and no fine-tuning happens in this project, by design.** The qualifier is a frozen pre-trained Llama 3.3 70B called zero-shot. That's the right call here for several reasons:

- The task (score + 3-way categorize from a short message) is squarely within a 70B instruct model's zero-shot ability — fine-tuning would be solving a problem the base model doesn't have.
- There is no labeled training corpus in the repo, and gathering enough high-quality labels to beat a well-prompted 70B would be expensive.
- Prompting keeps iteration cheap: a brokerage can change what "hot" means (e.g., tighten the budget threshold) by editing one string, with no retraining loop.

**Prompt iteration is the development loop.** The workflow I'd run: hold the §3 eval set fixed, change one thing in `QUALIFY_PROMPT` (add a few-shot exemplar, sharpen the definition of "urgency," or tighten the JSON instruction), re-run against the gold labels, and accept the change only if category accuracy and score correlation improve without regressing the adversarial rows. Concrete near-term prompt improvements: add 2–3 few-shot examples to anchor the score scale, and explicitly define each category band ("hot = financed + timeline < 60 days + specific criteria") so scores are reproducible across model versions. Fine-tuning only becomes worth it if zero-shot plateaus below the human ceiling on a stable, sizable label set.

## 7. Evaluation metrics

There is no eval harness in the repo today (only two unit tests on the Pydantic models, `tests/test_qualifier.py`), so the metrics below describe what I'd measure; all numbers are illustrative.

- **Qualification accuracy vs. human.** 3-class (hot/warm/cold) accuracy and macro-F1 against the gold labels, reported relative to the human-vs-human agreement ceiling from §3. *Illustrative:* target ≥ 85% of the human agreement rate before trusting auto-escalation.
- **Lead-scoring precision/recall.** Because `sales_team_notified` fires only on `category == "hot"`, the cost of errors is asymmetric. **Recall on "hot"** matters most — a missed hot lead is lost revenue — while **precision on "hot"** governs how much human time is wasted. *Illustrative:* tune for hot-recall ≥ 0.90 even at the expense of some precision.
- **Score calibration.** Correlation (Spearman) between model `score` and the human band, to confirm the 0–100 number is monotonically meaningful and not just noise around the category.
- **Schema validity rate.** Fraction of calls returning JSON that parses and passes `Qualification` validation (i.e., how often the `score: 50 / warm` error fallback is silently triggered). This is a production health metric, not just an offline one.
- **Business uplift (the real scorecard).** Reply rate and conversion uplift from same-second Day-0 outreach vs. the prior manual baseline, ideally measured via an A/B holdout. *Illustrative:* +X pp reply rate, +Y% lead-to-appointment conversion.

## 8. Deployment architecture

**Flow:**

```
Website form  --POST /webhook/lead-->  FastAPI (main.py, port 8013)
                                              |
                                    LeadPipeline.process_lead()
                                              |
                        +---------------------+----------------------+
                        |                     |                      |
                 QualifierAgent          SMSTool                 EmailTool
              (Groq Llama 3.3 70B)   (Twilio SMS)            (SendGrid email)
                  score/category      Day-0 welcome SMS      Day-0 welcome email
                        |
                  sales_team_notified = (category == "hot")
                        |
                  Notion "JMG Leads" CRM  (intended; see note)
```

Concretely (`main.py`, `pipelines/lead_pipeline.py`):

1. **Intake.** `POST /webhook/lead` validates the body against `LeadInput`. A request-timing middleware stamps `X-Process-Time` on every response, and there's a `/health` endpoint that reports whether Twilio and SendGrid are configured.
2. **Qualify.** `QualifierAgent.qualify()` calls Groq async (`ainvoke`) and returns the `{score, category, reasoning}` dict.
3. **Outreach (Day 0).** The pipeline generates a `lead_id` (`lead_<UTC-date>_<6 hex>`), sends the templated welcome SMS via Twilio and welcome email via SendGrid, and records per-channel `sent`/`failed` status in the response.
4. **Respond.** Returns a `LeadResponse` including the qualification, the `follow_up_sequence` status (with a planned `"Day 1: Property match email"` next touchpoint), and `sales_team_notified`.

**Where it runs.** A single FastAPI app served by Uvicorn on port 8013; an `infra/main.bicep` file indicates an Azure deployment target. The qualifier runs async, but the SMS/email tool calls are synchronous within the request.

**Honest gaps between the README and the code** (worth naming in an interview rather than overclaiming):

- **Notion CRM write is not implemented.** The README architecture shows "Notion CRM (update)" and config carries `notion_api_key`/`notion_leads_db`, but `process_lead` hard-codes `notion_page_id: None` — there is no Notion client call yet.
- **The drip campaign is not scheduled.** The README mentions APScheduler and multi-touch sequences, but only the Day-0 touch executes; `next_touchpoint` is a string label, not a scheduled job. There is no scheduler in the code.
- **CORS is wide open** (`allow_origins=["*"]`) and the webhook is unauthenticated — fine for a demo, must be locked down (signed webhook + origin allowlist) before production.

## 9. Business impact

All figures below are **illustrative** — the repo contains no measured metrics or analytics instrumentation. They represent the impact model you'd present and then validate via the §7 A/B holdout.

- **Lead response time.** *Illustrative:* from a manual baseline of hours (or overnight for after-hours leads) down to **< 5 seconds** for the Day-0 SMS + email, since outreach fires inside the webhook. This is the single biggest lever — speed-to-lead is the project's whole reason to exist.
- **Conversion uplift.** *Illustrative:* **+15–25% lead-to-appointment conversion** attributable to instant, 24/7 first-touch plus better triage of hot leads to humans.
- **Agent hours saved.** *Illustrative:* **~5–8 hours/week per agent** of manual reading, scoring, and copy-pasting first-touch messages eliminated, redirected to high-value hot leads that the system surfaces via `sales_team_notified`.
- **Triage quality.** *Illustrative:* hot-lead recall around 0.90 means the agent's time concentrates on the leads most likely to close, rather than being spread uniformly.

The qualification `reasoning` string doubles as a sales aid — the agent opens a hot lead already knowing *why* it scored high.

## 10. Lessons learned

- **A "safe" error fallback can hide failures.** Returning `{score: 50, category: "warm"}` on any exception keeps the API up, but it silently demotes a possibly-hot lead to an unremarkable warm one with no alarm. Production needs a distinct error sentinel, a metric on fallback rate, and a dead-letter path for re-qualification — never let a parse failure masquerade as a real score.
- **JSON-from-prose is fragile without enforcement.** `json.loads` on raw model output will eventually hit a stray markdown fence or trailing prose. Use the provider's structured-output/JSON mode or a tolerant parser, and treat the Pydantic validation failure rate as a first-class health metric.
- **Don't overclaim the architecture.** The README promises Notion sync and APScheduler drips that the code doesn't yet do. Shipping the honest Day-0 slice first is fine — but the diagram and the code must agree, or you erode trust.
- **Outreach in a regulated domain should start templated.** Real estate copy touches fair-housing and pricing-claim risk. Beginning with deterministic templates (current state) and layering LLM personalization behind guardrails is the right sequencing, not the other way around.
- **Synchronous side-effects in the request path don't scale.** Twilio and SendGrid calls run inline in the webhook; under load these should move to a background queue so a slow provider doesn't stall intake.
- **Tighten security before launch.** Open CORS plus an unauthenticated webhook is an open door for spam and abuse; add webhook signature verification and an origin allowlist.

## Likely follow-up questions

1. **Your error fallback returns "warm/50" — what's wrong with that and how would you fix it?** → It hides failures and can demote hot leads silently; replace with a typed error state, a fallback-rate metric, and a dead-letter re-qualification queue.
2. **The qualifier does `json.loads` on raw LLM output — how do you make that robust?** → Use Groq/structured JSON mode or a tolerant extractor, validate via the `Qualification` model, and alert on validation-failure rate rather than swallowing it.
3. **Why Groq Llama 3.3 70B and not a frontier model or the 8B fast model?** → Latency (Groq LPU) and cost for a high-volume, low-complexity task; 70B over 8B for free-text nuance, with 8B reserved for cheaper bulk work.
4. **The README claims Notion sync and drip scheduling — does the code do that?** → No; `notion_page_id` is hard-coded `None` and only the Day-0 touch fires. I'd implement the Notion write and a real scheduler (or a queue/cron) next.
5. **How would you evaluate qualification quality without ground truth?** → Build a senior-agent-labeled, stratified golden set, measure 3-class macro-F1 and hot-recall against the human agreement ceiling, and track score calibration.
6. **Why send templated outreach instead of LLM-generated messages?** → Cost/latency/compliance for the MVP; LLM personalization comes later behind guardrails that forbid inventing inventory or quoting prices.
7. **You run SMS/email synchronously inside the webhook — what breaks at scale?** → A slow provider stalls intake; move side-effects to a background queue and keep only qualification (or even that too) async.
8. **How do you handle hot-lead escalation reliably given asymmetric error costs?** → Tune for high hot-recall, route `sales_team_notified` to a real notification channel with retries, and monitor missed-hot leakage as a tracked metric.

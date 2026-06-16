# AI Inbox Cleaner — Case Study

**30-second pitch:** A Gmail triage agent that polls unread primary-inbox mail, classifies each message into one of six categories with a confidence and priority using Groq's `llama-3.1-8b-instant`, then runs an action router that labels, stars, drafts replies (via the larger `llama-3.3-70b-versatile`), and fires Slack alerts. It's a FastAPI service that turns a noisy inbox into labeled, prioritized, partially-pre-drafted work — keeping a human in the loop for anything that gets sent.

## 1. Problem statement

A single operator (here, someone juggling security/EP job offers, real-estate leads, client work, and active job applications) receives a high-volume, heterogeneous inbox. The cost is not reading — it's *triage*: deciding what each email is, how urgent it is, what to do with it, and whether it deserves a reply. That decision work is repetitive but context-sensitive, so rigid Gmail filters (sender/subject regex) break down the moment a new recruiter domain or a differently-worded lead shows up.

The system's job: for every new unread email, decide a category, decide a priority, take the right Gmail action (label / star / mark-read / draft), and surface the important ones into Slack — without auto-sending anything irreversible.

## 2. Why AI/ML was needed

Gmail's native filters are deterministic string/sender rules. They can't generalize: "Interview Invitation - Executive Protection Agent" from an unseen HR domain, or a buyer inquiry phrased a hundred different ways, won't match a hand-written rule. The categories here (`security_job`, `real_estate_lead`, `client_communication`, `job_application_response`, `newsletter`, `spam`) are *semantic* distinctions that depend on intent and content, not keywords.

An LLM is the right tool because:
- It generalizes to unseen senders/phrasings with zero per-rule maintenance.
- It can emit a structured, typed verdict (category + confidence + priority + reasoning) in one call — the `reasoning` field also gives an auditable trace for why an action was taken.
- The label taxonomy can evolve by editing one prompt, not retraining or rewriting a rules engine.

The trade-off I accepted: an LLM is non-deterministic and costs a network call per email, so I pinned `temperature=0` for classification and constrained output to a Pydantic schema to make it as deterministic and parseable as possible.

## 3. Dataset → Knowledge corpus & eval set

There is no classic training dataset — the system is pure inference over live data. The data it consumes:

- **Source:** Gmail API. `sync_new_emails()` pulls with query `is:unread category:primary newer_than:31d`, capped at `max_results=5` per run (a deliberately small batch for a poll). Each message is fetched `format="full"`, and `_parse_message()` extracts `from`, `subject`, and the first `text/plain` MIME part (base64url-decoded).
- **Unit of work:** one email = `{from, subject, body}`. The classifier only sees `body[:1000]`; the drafter sees `body[:2000]`.

**The six-category schema** (from `classifier.py` / `CATEGORY_LABEL_MAP`):

| Category | Gmail label |
|---|---|
| `security_job` | Jobs/Security |
| `real_estate_lead` | Leads/RE |
| `client_communication` | Clients |
| `job_application_response` | Applications |
| `newsletter` | Newsletter |
| `spam` | Spam (archived, not labeled) |

**How I'd build a golden/eval set:** hand-label a few hundred representative real emails across all six categories — deliberately over-sampling the boundary cases (newsletter vs. spam, security_job vs. job_application_response, client_communication vs. real_estate_lead). Store as `{from, subject, body, gold_category, gold_priority}`. Stratify so every category and every priority level is represented, and include adversarial examples (a phishing email dressed as a job offer; a marketing blast from a real client domain). This frozen set becomes the regression harness for every prompt change. *Illustrative:* target 300–500 labeled emails, ~50–80 per category.

## 4. Feature engineering → Prompt & context engineering

The GenAI analog of feature engineering here is the prompt + the structured-output contract + the router logic.

**Classification prompt** (`CLASSIFICATION_PROMPT`): an enumerated category list *with a one-line definition each* (this is the key feature — definitions disambiguate the tricky pairs), an explicit priority axis (high/medium/low), and the email rendered as `From / Subject / Body` with the body truncated to 1000 chars to bound tokens and cost.

**Structured output as the contract:** classification uses `llm.with_structured_output(EmailClassification)`, where `EmailClassification` is a Pydantic model (`category, confidence, priority, reasoning`). This forces the LLM into a typed, parseable verdict instead of free text — no brittle regex on prose. `temperature=0` makes it as repeatable as possible.

**Confidence + reasoning as first-class fields:** every verdict carries a `confidence` float and a `reasoning` string. These are surfaced into Slack messages so a human reviewer can sanity-check the model's call.

**Action-router logic** (`EmailPipeline.process_email`) — the deterministic policy layer that converts a classification into side effects:
- If `category != "spam"`: get-or-create the mapped Gmail label and apply it. (Spam is simply left un-labeled — effectively archived/ignored, never starred or drafted.)
- If `priority == "high"`: add the `STARRED` label **and** generate a reply draft.
- If `category == "job_application_response"`: Slack alert to `#job-alerts`.
- If `category == "newsletter"`: Slack alert to `#newsletter-alerts`.
- If `category == "real_estate_lead"`: append a `notion_forward` action marked `status: "pending"` (the Notion CRM push is stubbed, not yet wired).
- Always: remove `UNREAD` (mark read).
- Every action is recorded with an explicit `status` (`executed` / `failed` / `pending`), and any failure routes a full traceback to a Slack `#exceptions` channel via `notify_slack_error`.

**Tool definitions:** the "tools" are concrete API wrappers, not LLM-callable function-calling tools — `GmailTool` exposes `list_messages`, `get_message`, `get_or_create_label`, `modify_labels`, `create_draft`. The orchestration is code-driven (a pipeline), not model-driven (the LLM does not decide which tool to call).

## 5. Model selection rationale

Two Groq-hosted Llama models, chosen by matching model size to task difficulty:

- **Classification → `llama-3.1-8b-instant`** (config `groq_model_fast`, `temperature=0`). Classification into six well-defined buckets is an easy, high-volume task that runs on *every* email. I chose the small 8B model because it's cheap and fast, and the enumerated-category prompt plus structured-output schema do most of the heavy lifting — accuracy doesn't need a 70B model. Running the big model on every inbound email would be wasteful.

- **Reply drafting → `llama-3.3-70b-versatile`** (config `groq_model_primary`, `temperature=0.4`). Drafting a professional reply is a harder generation task that demands fluency and nuance, and it runs *only* on high-priority emails (a small fraction). So I spend the bigger model's cost/latency exactly where quality matters and frequency is low. The higher temperature (0.4 vs 0) gives the draft natural variation; the classifier stays at 0 for determinism.

This is the core trade-off: **small fast model for the frequent, easy, must-be-deterministic decision; large model for the rare, hard, quality-sensitive generation.** I accept that the 8B model will occasionally mis-bucket a genuinely ambiguous email — and I mitigate that with the confidence field and human-in-the-loop on anything that gets sent. Groq was chosen as the host for its low inference latency, which matters for a per-email poll loop.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No model training or fine-tuning is done — by design.** Reasons:
- There's no labeled corpus large enough to fine-tune on, and building one would be slower than iterating a prompt.
- The category taxonomy is a moving target (a new lead type, a new label) — a prompt edit ships that change instantly; a fine-tune would need a new dataset and a retrain every time.
- A zero-/few-shot 8B model already clears the bar for six clearly-defined buckets.

**The iteration loop is prompt engineering**, not gradient descent:
1. Tighten the per-category one-line definitions to fix specific confusions (the most leverage is on the boundary pairs).
2. Lock determinism with `temperature=0` and enforce the schema with `with_structured_output` so output is always valid.
3. Run against the frozen golden set (§3), inspect the `reasoning` field on misclassifications, and adjust definitions or add a clarifying instruction.

If accuracy ever plateaued below target, the next steps — *before* fine-tuning — would be few-shot exemplars in the prompt, or escalating low-confidence emails to the 70B model for a second opinion.

## 7. Evaluation metrics

The code does not yet ship an eval harness, so these are the metrics I'd track (targets are *Illustrative:*):

- **Overall classification accuracy** on the golden set. *Illustrative:* target ≥ 90%.
- **Per-category precision/recall/F1.** Recall on `spam` and precision on the high-value categories matter most asymmetrically (see below). *Illustrative:* per-category F1 ≥ 0.85.
- **Spam false-archive rate** — the most dangerous error, since a real email mis-tagged as spam gets silently dropped from triage. *Illustrative:* keep < 1%. I'd deliberately tune the prompt to be *conservative* about calling something spam.
- **Priority calibration** — fraction of true-high emails the model marks `high` (drives both starring and draft generation). *Illustrative:* high-priority recall ≥ 0.9.
- **Draft human-approval rate** — of LLM-generated drafts, the share a human sends with no/minor edits. This is the real measure of draft quality. *Illustrative:* target ≥ 60% accepted with minor edits.
- **Confidence reliability** — does low `confidence` actually correlate with errors? If so, route low-confidence emails to human review or the larger model.

Operationally, the `X-Process-Time` middleware header already gives per-request latency, and every action carries an `executed`/`failed` status that could be aggregated into an action success-rate dashboard.

## 8. Deployment architecture

```
Gmail (Gmail API, gmail.modify scope)
   │  poll: is:unread category:primary newer_than:31d  (max 5/run)
   ▼
EmailPipeline.sync_new_emails()  ──► _parse_message()  (FastAPI service, port 8018)
   ▼
ClassifierAgent  ── ChatGroq llama-3.1-8b-instant, temp=0, structured output
   ▼
Action Router (process_email)
   ├─ label (get_or_create_label + modify_labels)      [all non-spam]
   ├─ star  (STARRED)                                   [priority=high]
   ├─ draft_reply ── ChatGroq llama-3.3-70b, temp=0.4   [priority=high]  ──► Gmail create_draft (approval, not sent)
   ├─ slack_notify #job-alerts                          [job_application_response]
   ├─ slack_notify #newsletter-alerts                   [newsletter]
   ├─ notion_forward (pending/stub)                     [real_estate_lead]
   └─ mark_read (remove UNREAD)                         [always]
        │
        └─ on any failure ──► Slack #exceptions (full traceback)
```

**Runtime:** FastAPI app (`src.inbox_cleaner.main:app`) on uvicorn, port 8018. Endpoints: `GET /health` (reports whether the Gmail credentials file exists), `POST /classify` (classify one ad-hoc email), `POST /sync/trigger` (run the poll-and-process batch). CORS is wide-open and there's process-time middleware on every request.

**Auth:** Gmail via OAuth2 desktop flow (`gmail.modify` scope), caching `token.json`; Groq via `GROQ_API_KEY`; Slack via `SLACK_BOT_TOKEN` (bot posting to `#job-alerts`, `#newsletter-alerts`, `#exceptions`). `apscheduler` is a dependency, implying the intended prod trigger is a scheduled poll (the README also mentions a Gmail push webhook as the alternative).

**Where it'd run in prod:** a small always-on container (the FastAPI service) plus a scheduler firing `/sync/trigger`. Notably, `EmailPipeline` is instantiated once at module import and the Gmail OAuth flow can open a local browser — fine for a single-user desktop/server, but for true production I'd move to a service account / pre-provisioned refresh token and switch from polling to Gmail push notifications (Pub/Sub) to cut latency and API quota. The `max_results=5` cap and reads marked synchronously also flag this as a single-tenant deployment, not multi-user SaaS yet.

## 9. Business impact

All figures *Illustrative:* — none are measured in code.

- *Illustrative:* triage ~100–200 emails/day per user fully unattended (label + prioritize + mark-read).
- *Illustrative:* ~10–15 seconds of human triage saved per email → ~30–45 minutes/day reclaimed for a busy inbox.
- *Illustrative:* high-priority emails surfaced to Slack within seconds of a poll, so interview invites and hot leads don't sit unread.
- *Illustrative:* ~60% of high-priority replies start from an LLM draft, cutting reply-composition time roughly in half for those.
- *Illustrative:* near-zero missed leads, since `real_estate_lead` and `job_application_response` get pushed to dedicated channels rather than relying on the user noticing them.

The defensible, non-numeric claim: the system converts *unstructured triage labor* into a *review-and-approve* workflow, and keeps the human gate on anything that would actually be sent.

## 10. Lessons learned

- **Structured output is the unlock.** `with_structured_output(EmailClassification)` + `temperature=0` removes the entire class of "parse the LLM's prose" bugs. Pin determinism on the classifier; save temperature for generation.
- **Match model size to task and frequency, not to ambition.** 8B on every email, 70B only on the rare high-priority draft. This is where the cost/latency budget is actually controlled.
- **Make the router fail soft.** Every action is wrapped, records an explicit `executed`/`failed`/`pending` status, and routes tracebacks to a Slack `#exceptions` channel. A failed label or a failed draft never aborts the whole email — and a *classification* failure falls back to category `newsletter`/`low` rather than crashing the batch. Honest caveat: that silent fallback could hide a systemic classifier outage, so it needs a failure-rate alert.
- **Keep humans on the irreversible path.** Drafts are created in Gmail for *approval* (`create_draft`), never auto-sent. Spam is left un-actioned rather than hard-deleted. Both are deliberate guardrails against an LLM mistake doing real damage.
- **Watch the truncation.** Body is cut to 1000 chars for classification / 2000 for drafting — cheap, but a long email with its real intent buried at the bottom can be mis-read. A summary-first or subject-weighted strategy would harden this.
- **Some integrations are stubs.** `notion_forward` is `status: "pending"` and the `notion-client` dependency isn't wired into the pipeline yet — honest about scope: the Notion CRM push is designed but not implemented.

## Likely follow-up questions

- **Why an LLM instead of a fine-tuned classifier (e.g., DistilBERT)?** → Faster iteration on an evolving taxonomy, zero labeled-corpus requirement, and a free `reasoning`/confidence trace; revisit fine-tuning only if cost or latency at scale forces it.
- **How do you stop a real email being silently archived as spam?** → Tune the prompt conservatively, track spam false-archive rate (*Illustrative:* < 1%), and review low-confidence spam calls instead of auto-acting — note spam is currently left un-actioned, not deleted.
- **The classifier falls back to `newsletter`/`low` on failure — what's the risk?** → It silently masks a classifier outage; mitigate with a classification-failure-rate alert, since the failure already posts to `#exceptions`.
- **Why poll with `max_results=5` and `newer_than:31d`? Does this scale?** → It's a single-tenant safety throttle; for prod I'd switch to Gmail push (Pub/Sub) webhooks and pagination to cut latency and quota use.
- **How do you evaluate before shipping a prompt change?** → A frozen, stratified golden set (§3) run as a regression harness, inspecting per-category F1 and the `reasoning` on misses — no eval harness ships in the code yet.
- **The LLM doesn't choose tools — why a hard-coded router instead of function-calling?** → Determinism, auditability, and cheaper/safer execution; the policy from category→action is simple and stable enough that code is more reliable than letting the model orchestrate.
- **How do you keep draft quality and tone safe?** → Drafts are human-approved (never auto-sent), generated by the 70B model at temp 0.4, and tracked via an approval-rate metric (*Illustrative:* ≥ 60% accepted with minor edits).
- **What breaks first at 10× volume?** → Groq rate limits / per-email latency and the synchronous single-process pipeline; I'd add batching, async fan-out, and a queue between Gmail intake and classification.

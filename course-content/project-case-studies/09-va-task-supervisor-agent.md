# VA Task Supervisor Agent — Case Study

**30-second pitch:** An LLM-driven supervisor that takes incoming tasks (titled, prioritized, skill-tagged) and assigns them to the best-fit virtual assistant by reasoning over each VA's skills and current workload, then notifies the team via Slack and tracks state in Notion. The reasoning core is Llama 3.3 70B served through Groq (`langchain_groq.ChatGroq`), wrapped in a FastAPI service exposing a `/tasks/assign` endpoint. It replaces a coordinator's manual "who's free and good at this?" judgment with a structured, auditable JSON decision plus a written rationale.

## 1. Problem statement

A team running a pool of virtual assistants faces a constant routing decision: every new task must go to *someone*, and the "right" someone depends on a fuzzy match between the task's required skills and each VA's competencies, balanced against who is already overloaded. Done manually by an ops coordinator, this is slow, inconsistent, and a single point of failure. Tasks pile up unassigned, skilled VAs sit idle while others drown, and there is no written record of *why* a task went where it did.

The system in this repo (`va_task_supervisor_agent`) targets the assignment step specifically: given a `TaskInput` (`title`, `priority`, `due_date`, `skills_required`, `estimated_hours` — see `models.py`), pick the best VA, post a Slack notification, mark Notion as assigned, and return a daily digest snapshot.

## 2. Why AI/ML was needed

The assignment is not a clean lookup. The task carries `skills_required: List[str]` (e.g. `["crm"]`) and each VA carries a `skills` list (e.g. `["crm", "communication", "real_estate"]`). A rules engine can do exact set-membership matching, but real tasks describe needs in free-text titles ("Follow up with leads") that imply skills never explicitly tagged, and the decision must *trade off* skill fit against workload — a soft optimization, not a hard filter.

The LLM earns its place by doing three things a brittle rules table struggles with at low engineering cost:
- **Fuzzy skill inference** — relating a title and skill tags to a VA's competencies even when the tags are sparse.
- **Multi-criteria balancing** — "best skills match AND lowest workload" is an explicit instruction in `ASSIGN_PROMPT`; the model weighs both rather than applying a fixed priority order.
- **Human-readable justification** — the prompt forces a `reasoning` field, so every assignment ships with an explanation an ops lead can audit or override.

This is a deliberately *thin* use of an LLM: one call, structured output, low temperature. It is the "good enough and explainable" tier, not a trained scheduler.

## 3. Dataset → Knowledge corpus & eval set

There is **no training dataset** and no vector store — this is a zero-shot reasoning agent. The "corpus" is the runtime context assembled per request:

- **VA profiles** — name + skills list. In `supervisor_pipeline.py` these are currently **hard-coded** (Maria/James/Priya with their skill arrays), but the architecture in `config.py` provisions `notion_va_profiles_db`, i.e. the intended source of truth is a Notion "VA Profiles" database queried via `NotionTool.query_database`.
- **Workloads** — a `Dict[str, float]` of hours per VA (hard-coded `{"Maria": 6, "James": 12, "Priya": 9}` today; intended to be derived from the Notion Tasks DB, `notion_tasks_db`).
- **Tasks** — arrive as request payloads, source-of-truth being the Notion Tasks database.

**How I'd build an eval set of tasks → correct assignment.** I'd assemble a labeled set of `(task, VA roster, workload snapshot) → expected_VA` triples:
- **Golden labels from history:** pull historical Notion task records where a human coordinator already assigned and the outcome was good (task completed on time, no reassignment). The human's pick is the label.
- **Synthetic edge cases:** hand-author tricky cases — skill ties broken by workload, tasks whose title implies a skill not in the tag list, all-VAs-overloaded escalation cases.
- **Disagreement set:** cases where two reasonable coordinators might differ; score these with a tolerance band (top-2 acceptable) rather than exact match.
Each eval row freezes the exact `va_profiles` and `workloads` the agent would see, so the assignment is reproducible. Correctness is then "did the model's `assigned_to` match the human label," reported per-slice (by priority, by skill area).

## 4. Feature engineering → Prompt & context engineering

This is where the real engineering lives, because the model itself is fixed. The single prompt (`ASSIGN_PROMPT` in `assigner.py`) is the entire decision logic.

**The assignment reasoning prompt.** It is a flat instruction template filled at call time:

```
Assign this task to the best VA based on skills match and workload.

Task:
Title: {title}
Priority: {priority}
Skills Required: {skills}
Estimated Hours: {hours}

VA Profiles:
{va_profiles}

Current Workloads:
{workloads}

Select the VA with the best skills match AND lowest current workload.
Return JSON:
{ "assigned_to": "<VA name>", "reasoning": "<why this VA>" }
```

Several context-engineering choices matter:
- **Tasks and VAs are framed as plain-text context, not tools.** Notion and Slack are *not* exposed to the model as callable tools (no tool-calling / function-calling). Instead, the pipeline pre-fetches VA profiles and workloads and *renders them into the prompt string* (`profiles_text`, `workloads_text` in `assigner.py`). The LLM sees a flattened snapshot — `- Maria: ['crm', 'communication', 'real_estate']` and `- James: 12hrs` — and only emits a decision. The side effects (Slack message, Notion update) happen in deterministic Python *after* the model returns. This keeps the LLM in a pure-reasoning role and the I/O in testable, non-LLM code.
- **Structured output by instruction, not by schema enforcement.** The prompt asks for a two-field JSON object and the code does `json.loads(response.content)`. There is no JSON-mode flag, no Pydantic-constrained decoding, no retry-on-parse-failure. If the model wraps the JSON in prose or markdown fences, the parse throws and the `except` returns `{"assigned_to": "Unassigned", ...}` — a safe-but-blunt fallback. This is the prompt's biggest fragility (see Lessons).
- **Low temperature (0.2)** to make the routing decision near-deterministic and reduce JSON-format drift.
- **Workload is pre-summarized to a single float per VA** rather than handing the model raw task lists — feature reduction that keeps the prompt short and the comparison crisp.

The deliberate trade-off: by rendering context-as-text rather than giving the model live Notion/Slack tools, you lose autonomy (the agent can't decide to go look something up) but gain determinism, lower latency (one round-trip), and dramatically easier testing.

## 5. Model selection rationale

The code uses **Llama 3.3 70B Versatile** (`groq_model_primary = "llama-3.3-70b-versatile"`) via **Groq** (`ChatGroq`), with a configured-but-unused fast tier **Llama 3.1 8B Instant** (`groq_model_fast`). Groq is chosen for its very low inference latency (Groq's LPU serving), which suits an interactive assignment endpoint where a coordinator or webhook is waiting on the response.

**Why a 70B model for a two-field output?** The output is tiny but the *reasoning* — fuzzy skill matching plus a workload trade-off plus a coherent justification — benefits from a capable model. The 8B fast tier is provisioned as a cheaper fallback/escalation lever (e.g. for bulk re-balancing or digest generation where stakes are lower).

**LLM vs a rules engine.** A pure rules engine (score = skill-overlap − workload-penalty, pick argmax) would be cheaper, deterministic, free, and trivially testable — and for *exactly-tagged* tasks it would likely match or beat the LLM. The LLM is justified only where the inputs are messy: titles implying untagged skills, ambiguous priorities, and the need for a written rationale that a human will read. The honest senior take: this problem sits on the boundary, and a production system would likely run the rules engine as the default path and reserve the LLM for low-confidence / tie / free-text cases — using the LLM where it adds judgment, not as the only router.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training and no fine-tuning.** The system is zero-shot prompting against a hosted model; there are no weights to update and no labeled training corpus in the repo. This is the right call here:
- The decision logic is small and expressible in a few sentences of instruction — cheap to author and to change.
- VA rosters and skills churn constantly; encoding them in prompt context (eventually from Notion) means *no retraining* when a VA is added or learns a new skill. A fine-tuned model would go stale the moment the roster changes.
- There isn't enough labeled assignment history (in-repo) to justify fine-tuning, and the marginal accuracy gain over a good prompt would be small relative to the operational cost.

**Prompt iteration is the development loop.** Improvement happens by editing `ASSIGN_PROMPT`: tightening the "skills match AND lowest workload" instruction, adding the explicit JSON contract, and (next steps) adding few-shot examples for tie-breaking and escalation, plus an instruction to emit *only* raw JSON to harden parsing. Each prompt revision is validated against the eval set from §3 rather than by eyeballing one example.

## 7. Evaluation metrics

No evaluation harness ships in the repo, so all targets below are *Illustrative:* and would be measured against the §3 eval set.

- **Assignment correctness vs human** — % of cases where the agent's `assigned_to` matches the human coordinator's pick. Report exact-match and top-2 (tolerance) variants. *Illustrative:* ~85% top-1 agreement, ~95% top-2.
- **Skill-coverage rate** — fraction of assignments where the chosen VA actually possesses the `skills_required`. This is directly checkable in code without human labels and should be near 100% for tagged tasks. *Illustrative:* target ≥98%.
- **Workload-balance / fairness** — variance in hours-per-VA after a batch of assignments vs the rules-engine baseline; the agent should not worsen balance. *Illustrative.*
- **Escalation accuracy** — when all VAs are overloaded or no skill matches, does the agent correctly route to `Unassigned` / human review rather than force-fit? Currently `Unassigned` only appears on *error*, not on a reasoned "no good fit," so this metric also tracks a needed feature. *Illustrative:* target ≥90% correct escalation.
- **SLA / throughput** — p50/p95 latency of `/tasks/assign` (the service already emits `X-Process-Time`), and assignments-per-minute under load. *Illustrative:* p95 < 2s given Groq's low latency.
- **JSON parse-failure rate** — operational metric; fraction of model responses that fail `json.loads`. *Illustrative:* should be <1% after hardening the prompt.

## 8. Deployment architecture

The system is a **FastAPI** service (`main.py`), intended to run under `uvicorn` on port 8017 (`uv run uvicorn src.va_supervisor.main:app`). Request flow:

```
Task intake                Supervisor pipeline              Side effects
-----------                -------------------              ------------
POST /tasks/assign  -->  SupervisorPipeline.assign_task  -->  SlackTool.send_message
(AssignmentRequest,        |                                   (webhook -> #channel)
 validated by Pydantic)    |-- gather va_profiles            NotionTool.update/create
                           |   + workloads (Notion DB,        (mark task assigned)
                           |   hard-coded today)
                           |-- AssignerAgent.assign
                           |   -> ChatGroq (Llama 3.3 70B)
                           |   -> JSON {assigned_to, reasoning}
                           v
                     AssignmentResponse
                     {assignment, notifications, daily_digest}
```

Concrete components from the code:
- **Intake:** `POST /tasks/assign` accepts an `AssignmentRequest` (Pydantic-validated `TaskInput`). A `/health` and a stub `/tasks/overdue` endpoint also exist. CORS is wide-open (`allow_origins=["*"]`) and a middleware stamps `X-Process-Time` on every response.
- **Reasoning:** `AssignerAgent` (one `ChatGroq.ainvoke` call, async).
- **Notify — Slack:** `SlackTool` supports two paths — `send_message` posts to an incoming **webhook** (`SLACK_WEBHOOK_URL`), and `send_dm` calls Slack's **`chat.postMessage`** Web API with a **bot token** (`SLACK_BOT_TOKEN`). The pipeline currently uses the webhook path to announce the assignment.
- **State — Notion:** `NotionTool` wraps the official **`notion-client`** SDK (`query_database`, `create_page`, `update_page`) against the Tasks and VA-Profiles databases. Both tools are **fail-soft**: if the relevant key is unset, calls no-op (return `[]` / `False` / `None`) rather than crash — so the service runs in dev without credentials.
- **Email:** a `SENDGRID_API_KEY` is provisioned in config for future digest emails (not yet wired).
- **Where it runs:** a single stateless FastAPI process; horizontally scalable behind a load balancer since there's no in-process state beyond the pipeline singleton. Secrets come from a `.env` via `pydantic-settings`.

Honest gaps for production: the polling/webhook **Task Monitor** in the README diagram isn't implemented (assignment is request-driven only), `daily_digest` numbers are hard-coded, and VA profiles/workloads aren't yet read from Notion.

## 9. Business impact

All figures here are *Illustrative:* — no measurement harness exists in the repo.

- **Coordination overhead saved** — *Illustrative:* removing manual triage of, say, 150 tasks/week at ~3 min of coordinator decision time each ≈ 7.5 hours/week of ops time reclaimed.
- **Faster assignment / lower task latency** — *Illustrative:* time-to-assignment drops from minutes/hours (waiting on a human) to sub-2s, so tasks start sooner.
- **Consistency & auditability** — every assignment ships a `reasoning` string and a workload snapshot, giving an auditable trail the manual process lacked (qualitative, not a number).
- **Load balancing** — *Illustrative:* by explicitly factoring workload, fewer VAs are over-allocated, reducing burnout and missed deadlines.

The defensible, non-illustrative claim: the system converts an implicit human judgment into a *structured, logged, repeatable* decision — value that holds even before any accuracy number is measured.

## 10. Lessons learned

- **Fragile JSON contract is the weakest link.** Relying on `json.loads(response.content)` with no JSON-mode, no fence-stripping, and no retry means any formatting drift collapses straight to `"Unassigned"`. The fix is structured-output enforcement (JSON mode / schema-constrained decoding) plus a parse-and-retry loop — cheap insurance for a one-call agent.
- **`Unassigned` conflates "error" with "no good fit."** Today it only fires on exceptions, so a legitimate "everyone's overloaded, escalate to a human" outcome is indistinguishable from an API failure. These deserve separate, explicit branches.
- **Context-as-text beats tool-calling for this problem.** Pre-fetching Notion data and rendering it into the prompt (rather than giving the LLM live tools) made the agent deterministic, single-round-trip, and easy to test — a good trade when the agent doesn't need to *decide* what to look up.
- **Hard-coded profiles/workloads are a demo shortcut, not the design.** `config.py` already names `notion_tasks_db` and `notion_va_profiles_db`; the lesson is to wire the real Notion read before trusting any accuracy metric, since the whole decision quality depends on input freshness.
- **The LLM may be over-spec'd for the easy cases.** For exactly-tagged tasks a rules engine is cheaper and more predictable. A hybrid (rules default, LLM for ambiguous/tie/free-text) would likely cut cost and latency with no accuracy loss — knowing *when not* to call the model is the senior move.
- **Fail-soft tools are great for dev, risky for prod.** Notion/Slack calls silently no-op on missing keys, which is perfect locally but in production can mask a real outage (the API returns success while nothing was actually notified). Production needs these failures surfaced, not swallowed.

## Likely follow-up questions

1. **"Your assignment output is parsed with bare `json.loads`. What happens when the 70B model wraps it in markdown, and how would you harden it?"** → It throws and the agent returns `"Unassigned"`; fix with JSON/structured-output mode, fence-stripping, and a parse-retry loop.
2. **"Notion and Slack aren't exposed as LLM tools — they're rendered into the prompt. Why, and what do you give up?"** → Determinism, single round-trip, and testability; you give up agent autonomy to fetch/act on its own. Justified because the agent only needs to *reason*, not *decide what to look up*.
3. **"Why an LLM here at all instead of `argmax(skill_overlap − workload_penalty)`?"** → Only for fuzzy/free-text/tie cases and the human-readable rationale; I'd actually run the rules engine as default and gate the LLM to low-confidence cases.
4. **"How would you measure that the assignments are actually correct?"** → Build the §3 eval set from historical Notion assignments + synthetic edge cases; report top-1/top-2 agreement, skill-coverage, and escalation accuracy per slice.
5. **"The roster and workloads are hard-coded. What breaks when you move them to Notion, and how do you keep them fresh?"** → Latency and failure modes enter the hot path; cache profiles, compute workloads from open tasks, and surface (not swallow) Notion read failures.
6. **"How does the system escalate when no VA fits or everyone's overloaded?"** → It currently can't distinguish that from an error — both yield `Unassigned`; I'd add an explicit "no-fit → human review" branch and a workload-threshold guard.
7. **"You picked 70B but provisioned an 8B fast model — when would you route to which?"** → 70B for the judgment-heavy assignment call; 8B for bulk re-balancing, digest text, and low-stakes/high-volume paths where latency and cost dominate.
8. **"This service is stateless with `daily_digest` hard-coded. How do you make the monitoring/reporting real and scale it?"** → Add the README's Task Monitor (poll/webhook on Notion), compute digest metrics from the Tasks DB, and scale the stateless FastAPI process horizontally behind a load balancer.

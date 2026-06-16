# Smart Notion Sync Agent — Case Study

**30-second pitch:** A FastAPI service that keeps a Notion "Command Center" in bi-directional sync with Google Workspace (Calendar) and Slack. Deterministic timestamp/hash diffing handles the common case; a Groq-hosted Llama 3.3 70B agent (`ConflictResolverAgent`) is the escape hatch that merges records when the *same* item was edited differently in both systems. LangGraph drives the Slack-to-Notion classification/extraction flow and the Notion-to-Slack change-notification flow.

---

## 1. Problem statement

A small team runs its operational source-of-truth in Notion (Tasks, Leads, Jobs, Grants, Calendar, Files, Notes databases — see `config.py`) but lives day-to-day in Google Calendar and Slack. Manually keeping those systems aligned is the classic last-mile glue work: a milestone date moved in Notion, an event rescheduled in Google Calendar, a "fix the login bug by EOD" message dropped in Slack that should have been a tracked task. Each of these is a tiny reconciliation that a human ends up doing repeatedly.

The hard part is not the API plumbing — it is the **collision case**. When the same record is touched in both Notion and Google Calendar between sync runs, a naive last-writer-wins overwrites real edits. The system needs a defensible way to decide *use Notion's version, use Google's version, or merge the two*.

Concretely, the service must:
- Mirror Notion Calendar pages to Google Calendar events and back (`pipelines/notion_sync.py` → `SyncEngine.sync_calendar`).
- Turn Slack messages into Notion Task or Note pages, and push Notion task changes back to a Slack channel (`pipelines/slack/`).
- Detect conflicts and resolve them without silently destroying data.

## 2. Why AI/ML was needed

Most of this system is deliberately **not** AI — and that is a feature. The calendar sync uses `last_edited_time` (Notion) vs `updated` (Google) timestamp comparison plus field-level change detection (`SyncEngine._check_if_changed`, `_normalize_gcal_event`). That is cheap, deterministic, auditable, and correct for the 95%+ of cases where only one side changed.

AI earns its place in exactly two spots where the input is unstructured natural language or genuinely ambiguous:

1. **Conflict merge** (`agents/conflict_resolver.py`). When both sides changed, there is no deterministic rule that knows whether "Q3 Planning — Room 4B" (Notion) and "Q3 Planning Sync — Room 4A" (Google) are the same event with a typo fix plus a room change, or a real divergence. An LLM can read both records and propose a field-by-field merge with a reasoning string. A rules engine would need an unbounded list of hand-coded merge heuristics.
2. **Slack intent + extraction** (`pipelines/slack/nodes.py`). Classifying a free-text Slack message as `task` / `note` / `skip`, then extracting `{name, due_date, priority, related_job, related_lead}` from it, is exactly what LLMs do well and regexes do badly.

So the honest framing for an interview: this is an **automation agent**, not a trained model. The "ML" is prompt-engineered LLM calls wrapped in deterministic guardrails, used surgically.

## 3. Dataset → Knowledge corpus & eval set

There is no training dataset and no vector store. The "corpus" is live operational data pulled at sync time:

- **Records being synced:** Notion pages (properties dicts: `Name` title, `Start Date`/`End Date`, `Location`, `Type` select, plus a hidden `Sync ID` rich-text that stores the Google event ID — see `SYNC_ID_PROPERTY` and `calendar_mapping.py`), Google Calendar events (`summary`, `description`, `location`, `start`/`end`), and raw Slack message events.
- **Identity / linkage:** the hidden `Sync ID` property is the join key between a Notion page and its Google event. New Notion pages have no `Sync ID` (→ create in Google); Google events whose ID is absent from the `Sync ID` map are new (→ create in Notion). This is the dedup/identity-resolution layer that any sync needs before conflict logic can even run.

**How I'd build an eval set of conflict cases** (this is the part that does not exist in the repo yet and is the obvious next step):
- Take ~50–100 real synced records and construct *paired* "both sides edited" snapshots: `(notion_data, source_data, source_name)` — the exact signature `ConflictResolverAgent.resolve` takes.
- For each pair, have a human label the **gold resolution**: one of `use_a` / `use_b` / `merge`, plus the gold `merged_data`.
- Seed the set with hard cases: typo-vs-real-change, partial overlap (Notion changed location, Google changed time), and conflicting values for the same field (the case where `merge` is genuinely wrong and a human must decide).
- *Illustrative:* a starter set of ~80 labeled conflict pairs (no eval harness ships in the repo today).

The Slack flow would get its own eval set: messages labeled with gold `classification` and gold extracted fields, to measure classification accuracy and field-extraction F1.

## 4. Feature engineering → Prompt & context engineering

This is where the real design work lives, since there is no model to train. "Feature engineering" here means deciding *what context the LLM sees and what structured output it must return.*

### 4.1 Framing a sync conflict as a prompt

The conflict resolver (`CONFLICT_RESOLUTION_PROMPT` in `agents/conflict_resolver.py`) serializes both sides of the collision as pretty-printed JSON and asks for a structured decision:

```
You are a data conflict resolver. Two systems have modified the same record differently.

Source A (Notion):
{notion_data}

Source B ({source_name}):
{source_data}

Resolve the conflict by merging the best of both. Return JSON:
{
  "resolution": "use_a|use_b|merge",
  "reasoning": "why this resolution",
  "merged_data": {...merged record...}
}
```

Design choices worth defending in an interview:
- **Both records are fully serialized** via `json.dumps(..., indent=2)`. The LLM sees the complete field set of each side — this is the "feature vector." No pre-summarization that could hide the diff.
- **`source_name` is templated in** (`Notion` vs e.g. `google_calendar`) so the model knows which system is "B," which matters for reasoning about authority (a calendar is more authoritative about *times*; Notion is more authoritative about *task metadata*).
- **Constrained output schema** — `resolution` is a closed enum (`use_a|use_b|merge`), plus a free-text `reasoning` (for the audit log / human review) and a `merged_data` object that is directly write-back-able to Notion. The schema *is* the contract; the rest of the system consumes it.
- **`temperature=0.1`** — near-deterministic. Conflict resolution is not a creative task; you want the same conflict to resolve the same way every time for reproducibility.
- **Async + fail-safe default.** `resolve()` is `async` (`self.llm.ainvoke`) and wrapped in try/except: on *any* failure (bad JSON, API error) it returns `{"resolution": "use_a", "merged_data": notion_data}` — i.e. **fall back to Notion, the human-owned source of truth.** This is the single most important safety decision: a broken LLM call degrades to "don't touch the canonical system," not to data loss.

The corresponding output model is `ConflictResolution` in `models.py` (`source`, `record_id`, `resolution`, `reasoning`, `merged_data`).

### 4.2 The Slack pipeline as a multi-stage prompt graph

The Slack-to-Notion flow (`pipelines/slack/`) is a LangGraph `StateGraph` over a `SlackSyncState` dataclass, and it shows a second flavor of prompt engineering — **decompose one fuzzy decision into narrow, cheap LLM calls:**

- `classify_node` — one prompt, **one-word output** (`task` / `note` / `skip`), `temperature=0`. The prompt gives explicit definitions for each label. The router (`route_classification`) then sends `task` → extract, `note` → note, `skip` → END. Anything not in `("task","note")` is coerced to `skip` — defensive parsing of the model output.
- `extract_node` — only runs on the `task` branch, and asks for a **strict JSON object** with `null` for missing fields. It strips ``` fences with a regex before `json.loads`, and on any parse failure falls back to using the raw message text as the task name. Same fail-safe philosophy as the conflict resolver.
- The non-LLM nodes (`task_node`, `note_node`, `slack_ack_node`) do the deterministic Notion writes and the Slack ✅ reaction.

This staged design is itself the "feature engineering": instead of one mega-prompt that classifies *and* extracts *and* formats, each LLM call has a single job and a tightly constrained output, which makes parsing reliable and failures local.

### 4.3 "Tool definitions"

This codebase does not use LLM function-calling / tool-calling. The "tools" (`tools/notion_client.py`, `google_calendar.py`, `slack_client.py`) are plain Python wrappers the *application* calls, not tools the model invokes. The LLM's only job is to emit JSON; the orchestrator decides what to do with it. That is a legitimate and often-preferable pattern: deterministic control flow, model used only for the judgment call. Worth stating explicitly in an interview so you don't oversell it as an "agent with tools."

### 4.4 Change-detection features (the non-LLM half)

Before any LLM is consulted, `SyncEngine` builds comparable feature views: `_normalize_date` (everything to UTC `%Y-%m-%dT%H:%M:%SZ`), `_normalize_gcal_event` (keep only `summary`/`description`/`location`/`start`/`end`), and `_check_if_changed` (field-by-field title/location/type/start/end comparison). The Slack-to-Notion poller does field-level diffing via an in-memory `_last_property_snapshot` (`pipelines/slack/state.py`, `nodes.py:_compute_field_changes`). These hand-built comparators are what keep the LLM off the critical path for the easy cases.

## 5. Model selection rationale

- **Model:** `llama-3.3-70b-versatile` served via **Groq** (`langchain_groq.ChatGroq`), configurable through `GROQ_MODEL_PRIMARY` (`config.py`). Same model for both the conflict resolver and the Slack classify/extract nodes.
- **Why Groq + Llama 3.3 70B:** Groq's inference is optimized for very low latency, which matters because the Slack flow runs inline with a user dropping a message (they expect the ✅ ack quickly) and the calendar sync runs on a polling loop. A 70B open-weights model is more than capable of a 3-way classification and a JSON merge; you are not paying frontier-model prices for a judgment task that is mostly structured.
- **Cost/latency trade-off:** the system is architected so the LLM is the *exception path*, not the hot path. Calendar conflicts (and Slack messages) are a small fraction of total sync volume; the deterministic timestamp/diff logic handles the bulk at zero token cost. That is the real cost control — not the choice of model, but *how rarely you call it.*
- **Why an LLM for conflict resolution vs deterministic rules:** a rules engine can encode "newer timestamp wins" (and indeed `SyncEngine` does exactly that for the simple case). What it *cannot* cheaply do is reason over two semantically-similar-but-different records and decide "these are the same event, merge the better fields from each." The LLM generalizes across the open-ended space of *what kind of conflict this is* without an ever-growing rule table. The trade-off is non-determinism and the need for the `temperature=0.1` + fail-safe-to-Notion guardrails above.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training and no fine-tuning — by design.** There is no labeled corpus, the task volume per deployment is small, and the judgments (classify a message, merge two records) are well within a general instruction-tuned model's zero-shot ability. Fine-tuning would add a data-collection and retraining burden for marginal gain on a low-volume task; prompting is the right tool.

"Iteration" here means **prompt iteration**, and the code already shows the scars of it:
- The conflict prompt pins a closed `resolution` enum and demands a `merged_data` object — that structure is what makes the output consumable, and it is the kind of thing you tighten after seeing the model return prose.
- `extract_node` strips markdown code fences with `re.sub(r"```(?:json)?|```", "", raw)` before parsing — a direct response to the very common failure where the model wraps JSON in a fenced block.
- `classify_node` coerces any unexpected output to `skip` — defensive handling of the model occasionally returning more than one word.

The natural next iteration (not yet in the repo): build the §3 eval set, run the prompts against it, and tune wording until conflict-resolution accuracy and extraction F1 plateau. Possibly move to Groq/LangChain structured-output / JSON-mode to eliminate the fence-stripping hack entirely.

## 7. Evaluation metrics

No eval harness ships in the repo today, so every number below is **illustrative**, not measured. What I *would* track:

- **Conflict-resolution accuracy vs human:** fraction of conflicts where the agent's `resolution` + `merged_data` matches the human gold label. *Illustrative:* target ≥ 90% agreement on the §3 eval set.
- **False-merge rate:** fraction of cases where the agent chose `merge` (or `use_b`) but a human would have flagged it as a genuine conflict needing manual decision — the most dangerous error class, because it silently writes a wrong record. *Illustrative:* keep < 2%.
- **Human-approval rate:** if a review step is added (recommended — see §10), the fraction of agent resolutions a human approves unchanged. *Illustrative:* ≥ 85% would justify auto-applying low-risk merges.
- **Slack classification accuracy / extraction F1:** for the Slack flow, against labeled messages. *Illustrative:* classification ≥ 95%, field-extraction F1 ≥ 0.8.
- **Operational metrics (these the code *can* emit today):** `records_synced` and `conflicts_resolved` counters per source (`SourceSyncResult`), `error_rate`, retry counts from the `with_retry` exponential-backoff decorator. The README's sample output shows `error_rate: 0.002` and `conflicts_resolved: 1` — those are **illustrative sample payloads**, not measured production numbers.

Honest caveat for the interview: in the current code, `SyncEngine.sync_calendar` resolves the both-changed case by **timestamp comparison, not by calling `ConflictResolverAgent`** — `conflicts_resolved` stays at 0. The LLM resolver is built and wired to its prompt/model but is not yet invoked on the calendar critical path. Wiring it in (and gating it behind the eval-measured false-merge rate) is the headline open item.

## 8. Deployment architecture

Single FastAPI service (`main.py`), run with `uvicorn` on **port 8019**.

**Sync triggers:**
- `POST /sync/trigger` — manual/scheduled full sync; takes a `SyncRequest` (`action`, `sources`, `direction`) and calls `SyncEngine.full_sync`.
- A background loop started in the FastAPI `lifespan` runs `invoke_notion_to_slack()` every 10 seconds (poll Notion tasks → post changes to Slack).
- `POST /slack/events` — Slack Events API webhook receiver; verifies `url_verification` challenges, ignores Slack timeout-retries, and fires `invoke_slack_to_notion` for real user messages (skipping bot/subtype messages).
- `GET /health`, `GET /sync/status` — health + per-integration config status.

**Pipeline flow:**
1. **Calendar:** `list_events` (Google) + `query_database` (Notion) → identity-resolve via hidden `Sync ID` → create missing items each way → for items in both, **timestamp diff** (`last_edited_time` vs `updated`) → write the newer side, guarded by `_check_if_changed` / `_normalize_gcal_event` to avoid no-op writes. (Intended hook: when both changed → `ConflictResolverAgent.resolve` → write `merged_data` back to Notion/Google.)
2. **Slack→Notion:** LangGraph `slack_to_notion` graph — `ingest → classify (LLM) → [extract (LLM) → task] | note → slack_ack(✅)`.
3. **Notion→Slack:** LangGraph `notion_to_slack` graph — `poll → format → notify`, with field-level diffing against the in-process `_last_property_snapshot`.

**External services (all real, all in code):** Groq (LLM inference, `langchain_groq`), Notion API (`notion_client` SDK, API version `2022-06-28`, service integration token), Google Calendar (`googleapiclient` + service-account JSON), Slack (`slack_sdk` WebClient, bot token + signing secret). LangGraph (`langgraph.StateGraph`) for orchestration.

**Reliability:** `with_retry` decorator gives exponential backoff (`delay * 2**attempt`) on calendar/Notion writes; every external tool wrapper degrades to a no-op + log when its credential is unset (`if not self.client: return ...`) rather than crashing the service. State (`_last_property_snapshot`) is in-process, so it resets on restart — a known single-instance limitation (§10).

## 9. Business impact

All figures **illustrative** — the repo has no production telemetry.

- *Illustrative:* eliminates ~10–15 manual reconciliations/week per user (a moved date, a rescheduled event, a Slack ask that should have been a tracked task), at ~2–3 minutes each → ~30–45 minutes/user/week recovered.
- *Illustrative:* the deterministic-first design means the paid LLM path fires only on the small fraction of records that are genuinely ambiguous (conflicts + Slack intent), keeping per-sync token cost near zero for routine runs.
- *Illustrative:* fewer "I edited it in Notion but Calendar still shows the old time" support pings, because both systems converge automatically and the fail-safe never silently destroys the Notion source of truth.
- Qualitative and real-from-code: a single Notion Command Center stays authoritative across Calendar and Slack without a human acting as the sync layer.

## 10. Lessons learned

- **Use the LLM as the exception handler, not the engine.** The strongest design decision here is that deterministic timestamp/diff logic owns the common path and the LLM is reserved for the genuinely ambiguous merge. This keeps cost, latency, and (most importantly) *predictability* under control.
- **Fail safe toward the source of truth.** Both LLM call sites degrade gracefully: the conflict resolver defaults to `use_a` (Notion) on any error; `extract_node` falls back to raw text. A flaky model never causes data loss — at worst it causes a no-op.
- **Constrain the output schema and parse defensively.** The fence-stripping regex and the `skip`-coercion are evidence that real model output is messy; the closed enums and JSON contracts are what make the downstream code reliable. Moving to provider-native JSON/structured output would remove the hacks.
- **Build the eval set before trusting the resolver on the write path.** The biggest current gap: `ConflictResolverAgent` is implemented but not yet invoked by `sync_calendar`, and there is no measured false-merge rate. The right sequence is eval-set → measure → human-in-the-loop for the merge case → only then auto-apply.
- **In-memory state limits horizontal scaling.** `_last_property_snapshot` and the lifespan poll loop assume a single process; a multi-replica or restart-resilient deployment needs that snapshot moved to a durable store (and the README's "dead letter queue" is described but not implemented in the code I read).
- **Don't oversell the "agent."** This is prompt-engineered LLM calls inside deterministic control flow — no tool-calling, no autonomous planning. That is the *right* architecture for a sync system, and naming it accurately is itself a senior signal.

## Likely follow-up questions

1. **"Your README says ChatGroq resolves conflicts, but `sync_calendar` only compares timestamps — walk me through what actually happens on a both-sides edit."** → Honest answer: today it's last-writer-wins by timestamp; the `ConflictResolverAgent` is built and prompt/model-wired but not yet called on the write path. I'd gate it behind an eval-measured false-merge rate before enabling.
2. **"How do you stop the LLM from silently corrupting the Notion source of truth?"** → Fail-safe default to `use_a`/Notion on any error, closed-enum `resolution`, near-zero temperature, and a planned human-approval step for `merge` decisions.
3. **"Why Llama 3.3 70B on Groq instead of a frontier model?"** → Task is structured (3-way classify + JSON merge), not frontier-hard; Groq gives the low latency the inline Slack path needs; the LLM is the rare exception path so model cost barely moves the bill.
4. **"How would you build and measure an eval set for conflict resolution?"** → Paired `(notion_data, source_data, source_name)` snapshots with human-gold `resolution` + `merged_data`; metrics are accuracy-vs-human and especially false-merge rate; seed with typo-vs-real-change and conflicting-same-field cases.
5. **"What breaks when you run two replicas of this service?"** → `_last_property_snapshot` is in-process so each replica has a partial diff view, and the 10s lifespan poll loop would double-post to Slack; fix is durable shared state + a single leader for the poller (or a distributed lock).
6. **"You strip ``` fences before `json.loads` — what's the more robust fix?"** → Use Groq/LangChain structured-output or JSON mode so the model is constrained to emit valid JSON, removing the regex hack and the `skip`-coercion.
7. **"How do you handle Notion/Google API rate limits and partial failures?"** → `with_retry` exponential backoff on writes, paginated reads (`query_database` cursor loop), and per-tool no-op degradation when a credential is missing; the README's dead-letter-queue is the next step but isn't in the code yet.
8. **"When would you NOT use an LLM here at all?"** → Whenever a deterministic rule suffices (one-sided edits, identity resolution via `Sync ID`, no-op detection) — which is most of the volume. The LLM only earns its place on unstructured Slack text and genuinely ambiguous two-sided merges.

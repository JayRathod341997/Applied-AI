# Customer Support Engine — Case Study

**30-second pitch:** A stateful, multi-node LangGraph agent that classifies an incoming customer message, retrieves grounding context from an Azure AI Search knowledge base, reasons out resolution steps, drafts a customer-facing reply, and self-evaluates the customer's follow-up to decide whether to retry, finish, or escalate to a human. State is persisted per-conversation via a custom Azure Cosmos DB checkpointer, and the whole thing is served over a FastAPI app with both a REST `start` endpoint and a streaming WebSocket. The LLM is Groq-hosted `llama-3.3-70b-versatile`, used purely through prompting and structured-JSON outputs — no fine-tuning.

> **Grounding note:** This case study is written against the *actual source code* in `backend/src/`, which in several places diverges from the aspirational `README.md`/`INTERVIEW.md`. Where they disagree, the code wins, and I call out the divergence explicitly — that honesty is itself a useful interview signal.

---

## 1. Problem statement

Customer support inboxes are dominated by a long tail of repetitive, well-documented questions — billing disputes, "I can't log in", "what are your hours" — interleaved with a smaller set of genuinely hard or high-stakes issues (production outages, fraud, legal) that *must* reach a human quickly. Routing all of it through human agents is slow and expensive; routing all of it through a naive bot produces confidently wrong answers and frustrated customers who can't escape the loop.

The system needs to:
- Triage each message into an issue type (`billing | technical | general | greeting`) and a severity.
- Answer the easy, documented questions *grounded in the company knowledge base* so it doesn't hallucinate policy.
- Detect when its own answer didn't land and either try again with refined context or hand off cleanly.
- Never get stuck in an infinite "that didn't help → retry" loop.
- Remember the conversation across turns so a multi-message thread (e.g. "my invoice is wrong" → "it's $200 but should be $150") accumulates context.

## 2. Why AI/ML was needed

The triage and resolution steps are fundamentally natural-language understanding problems that resist hard-coded rules:

- **Intent + severity classification.** "Our entire production API is down and we're losing revenue every minute" must be recognized as `technical` / high severity, while "what are your support hours?" is `general` / low. A keyword matcher can't generalize across the phrasings customers actually use. The `classifier_node` uses the LLM with a constrained JSON schema for exactly this. (There is a deterministic fast-path for trivial greetings — `hello/hi/hey/...` short-circuit the LLM — which is the right engineering call: don't pay for a model call on a one-word "hi".)
- **Grounded resolution synthesis.** The `reasoner_node` takes retrieved KB chunks plus the customer's issue and produces a numbered resolution plan. This is RAG: the *knowledge* lives in the corpus, the *reasoning and phrasing* come from the model.
- **Feedback interpretation.** The `feedback_evaluator_node` reads the customer's next reply and classifies it `helpful | not_helpful`. "That's not what I meant" vs "thanks, sorted" is a semantic judgment, not a regex.

None of these require a *trained* model — they require a capable instruction-following LLM plus good prompts and good retrieval. That's the core "why RAG + tool-use, not fine-tuning" argument expanded in §6.

## 3. Dataset → Knowledge corpus & eval set

**The knowledge corpus.** There is no labeled training set. The "data" is the **support knowledge base**, ingested into **Azure AI Search**. The ingestion path is real and visible in `tools/kb_search.py`:

- Input format is **JSONL**, one record per line, with an `id` and a `content` (or `text`) field — see `ingest_knowledge_base()`.
- The index (`create_index`) is intentionally minimal: two fields, `id` (key) and `content` (searchable string). Retrieval is `QueryType.SIMPLE` — i.e. Azure AI Search's keyword/BM25-style search over `content`, returning the `top_k=5` chunks ordered by relevance score.
- Docs are loaded with `client.upload_documents()` and the script logs succeeded/failed counts.

So the corpus is whatever support articles, policy snippets, and FAQ entries the team curates into `knowledge_base.jsonl`. The README's example chunks ("Duplicate charges are automatically refunded within 3–5 business days", "Support is available Monday–Friday, 9 AM–6 PM EST") illustrate the granularity: short, atomic, answer-shaped passages — which is correct for a keyword index where each chunk should stand alone as a citable fact.

**How I'd build a golden eval set.** The repo ships no eval harness, so this is how I'd construct one for this exact graph:

1. **Golden Q→A pairs with relevance labels.** Sample real support transcripts, and for each customer question record (a) the *expected* issue_type and severity, (b) the set of KB doc `id`s that *should* be retrieved (relevance judgments for retrieval quality), and (c) a reference resolution. This lets me measure retrieval recall@5 and classification accuracy independently of the final answer.
2. **Escalation labels.** Tag each case with the correct terminal action: `auto_resolve`, `retry_then_resolve`, or `escalate`. High-severity outages, fraud, and legal complaints get `escalate`; documented FAQs get `auto_resolve`. This is the ground truth for escalation precision/recall (§7).
3. **Multi-turn cases.** Because the system is stateful, the eval set must include *threads*, not just single questions — e.g. the "invoice $200 vs $150" follow-up — to test that checkpointed memory actually changes the second-turn answer.
4. **Adversarial / out-of-KB cases.** Questions with *no* good KB match, to verify the system degrades gracefully (the reasoner is instructed to "use your best judgment" when context is thin — I'd want those flagged for escalation rather than confidently answered).

## 4. Feature engineering → Prompt & context engineering

This is a RAG + stateful-agent system, so "features" are really **(a) the assembled context per node, (b) the prompts, and (c) the graph's state machine.**

### 4a. The LangGraph state machine (nodes, edges, state)

**State schema** (`graph/state.py`) is a `TypedDict` called `SupportState`:

| Field | Purpose |
|---|---|
| `messages: Annotated[list, add_messages]` | Conversation log; the `add_messages` **reducer** appends rather than overwrites, so each turn accumulates. |
| `issue_type` | `billing | technical | general | greeting | None` — classifier output, drives routing. |
| `severity` | `low | medium | high | critical | None`. |
| `kb_chunks: list[str]` | Retrieved KB passages. |
| `resolution_steps: list[str]` | Reasoner output. |
| `status` | `open | resolving | resolved | escalated | None`. |
| `feedback_signal` | `helpful | not_helpful | None`. |
| `retry_count: int` | The loop guard — the single most important field for correctness. |
| `conversation_id` | Tracing / ticket linkage. |

**Nodes** (`graph/nodes.py`), each a pure `state -> dict` function returning a partial state update:

1. `classifier_node` — greeting fast-path, else LLM → `{issue_type, severity}` as JSON (with code that strips ```json fences before `json.loads`, falling back to `general/low` on parse failure).
2. `retrieval_node` — instantiates `KnowledgeBaseSearch`, queries Azure AI Search with the latest human message, writes `kb_chunks`.
3. `reasoner_node` — joins `kb_chunks` into context, asks the LLM for a JSON array of resolution steps.
4. `response_generator_node` — turns steps into warm prose (separate, friendlier prompt for the greeting path); appends an `AIMessage` and sets `status`.
5. `feedback_evaluator_node` — classifies the latest human reply as `helpful`/`not_helpful`; increments `retry_count` on `not_helpful`.
6. `escalation_node` — creates a Cosmos ticket via `EscalationHandler`, returns an apology message with the ticket ID and `status="escalated"`.

(There is also a `router_node`, but it only *logs*; the actual branching is done by conditional edges. Worth noting in interview — it's a no-op kept for observability/symmetry.)

**Edges** (`graph/edges.py`) — three conditional routers:

- `route_after_classifier`: maps `issue_type` → `billing_retrieval | technical_retrieval | general_retrieval`, and crucially routes `greeting` *straight to* `response_generator` (skip retrieval entirely). The three retrieval labels are **aliases that all map to the same `retrieval_node` function** in `builder.py` — a deliberate seam so per-type retrieval logic can diverge later without touching the graph topology.
- `route_after_response`: greetings → `__end__` (no feedback loop); everything else → `feedback_evaluator`.
- `route_after_feedback`: the heart of the agent. `helpful → __end__`; `not_helpful` **and** `retry_count >= settings.MAX_RETRIES → escalation`; otherwise → back to `reasoner` for another attempt.

So the live graph is:

```
classifier ──┬─(billing)──> billing_retrieval ──┐
             ├─(technical)─> technical_retrieval ─┼─> reasoner ─> response_generator ─┐
             ├─(general)───> general_retrieval ───┘                                    │
             └─(greeting)─────────────────────────────────────> response_generator ─> __end__
                                                                                       │
                  ┌──────────────── reasoner (retry) <─(not_helpful, retries left)─────┤
                  │                                                                     │
  __end__ <─(helpful)── feedback_evaluator <──────────────────────────────────────────┘
                  │
                  └─(not_helpful, retries exhausted)──> escalation ──> __end__
```

> **Code-vs-doc divergence worth naming:** the README/INTERVIEW describe the retry edge looping back to **retrieval** with a *refined/augmented query*. The actual `route_after_feedback` loops back to **`reasoner`**, and the retrieval query is just the latest human message verbatim (no query reformulation is implemented). In an interview I'd flag this as the most impactful gap to close — re-reasoning over the *same* chunks is much weaker than re-retrieving with the customer's clarification folded in.

### 4b. Context assembly & prompt design

- **Classifier prompt:** a tight system prompt enumerating the four categories and *demanding* a strict JSON object `{"issue_type": ..., "severity": ...}`, with explicit handling that greetings carry `severity: null`. Temperature is `0` for determinism. This is structured-output-via-prompt (not the provider's native JSON mode), hence the defensive fence-stripping + try/except fallback.
- **Reasoner context window:** `Customer issue: {text}` + `Knowledge base context: {joined kb_chunks}`, with an explicit "if context is insufficient, use your best judgment" instruction and a demand for a JSON array of step strings.
- **Responder prompt:** deliberately *de-structures* — "write in natural prose, no bullet points, end with an offer to help further" — because the customer-facing surface should read like a human, not a numbered list.
- **Feedback prompt:** biased toward `helpful` ("be generous — if the customer seems satisfied... choose helpful") to avoid over-triggering the retry/escalation path on ambiguous replies.

### 4c. Conversational memory

Memory is the **checkpointer**, not a prompt trick. `CosmosDBCheckpointer` (`memory/checkpointer.py`) implements LangGraph's `BaseCheckpointSaver`:

- Keyed by `thread_id` (the `conversation_id`), partition key `/thread_id`.
- `put()` serializes the checkpoint with the typed serde (`dumps_typed`), base64-encodes the bytes, and upserts a Cosmos doc; `get_tuple()` fetches the latest checkpoint (`ORDER BY c.ts DESC TOP 1`) and reattaches any pending writes.
- Because every super-step is checkpointed, a service restart mid-conversation can resume from the last completed node, and the `add_messages` reducer means turn N+1 sees the full prior history. `delete_conversation()` supports GDPR-style erasure and is wired to the `DELETE /support/history/{id}` route.

### 4d. Structured outputs & tools

Two "tools" in the agentic sense: `KnowledgeBaseSearch.search()` (retrieval) and `EscalationHandler.create_ticket()` (human handoff). The ticket payload is a structured Cosmos doc — `ESC-{uuid8}` id, issue_type, severity, serialized message history, resolution_steps, retry_count, `status="escalated"`, timestamp — giving the human agent full context on pickup.

## 5. Model selection rationale

- **LLM: Groq-hosted `llama-3.3-70b-versatile`** (`langchain_groq.ChatGroq`, `temperature=0`). A single model instance is reused across *all* LLM nodes (classify, reason, respond, evaluate). The rationale: Groq's LPU inference gives very low latency, and a 70B open-weights model is more than capable for classification and KB-grounded synthesis, at a fraction of frontier-model cost — important when one customer turn can fan out to 3–4 LLM calls. Temperature 0 keeps classification and JSON formatting stable.
  > **Divergence:** the README and `az` setup scripts describe **Azure OpenAI GPT-4o** + `text-embedding-ada-002`. The *running code* uses Groq Llama and **no embedding model at all** (Azure AI Search runs keyword/SIMPLE search, not vector search). I'd present the Groq path as the real one and GPT-4o as the documented-but-not-wired alternative.
- **Retrieval: Azure AI Search, `QueryType.SIMPLE`, top_k=5.** Keyword/lexical retrieval over short answer-shaped chunks. For a curated FAQ-style KB, lexical search is cheap, fast, and explainable; the obvious upgrade is semantic/vector or hybrid search (and the README's `ai_search.bicep` + embedding deployment anticipate exactly that), but it isn't in the code today.
- **Why LangGraph over a plain chain or ReAct loop?** Support is non-linear and stateful: the customer can say "that didn't help," which must route *backward*, but only a bounded number of times, then sideways to a human. A LangChain `Chain` has no notion of looping back; a free-form ReAct agent *can* loop but you can't cleanly assert "after exactly 3 unhelpful attempts, escalate." LangGraph makes the control flow an explicit, testable state machine with conditional edges and a checkpointer — you can unit-test each edge function (`route_after_feedback`) in isolation and persist/replay state. That determinism and testability is the whole point.

**Cost/latency trade-off:** the multi-node design means a worst-case turn is classify → retrieve → reason → respond → evaluate → (retry: reason → respond → evaluate) × up-to-MAX_RETRIES. Each LLM hop adds latency and tokens, so the greeting fast-path and the retry cap aren't just UX niceties — they're cost controls.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No training, and that's the correct call here.** The knowledge changes (new policies, new FAQs) far faster than you could re-fine-tune, and the *facts* must be auditable and swappable — that's a retrieval problem, not a weights problem. RAG + tool-use gives you: update the KB JSONL and re-ingest, and the agent's answers change immediately, with no risk of the model "memorizing" a now-outdated refund window.

What *was* engineered instead is **prompt iteration**, and the code shows the scars of it:
- JSON-only system prompts with worked examples, plus fence-stripping and try/except fallbacks because a 70B model occasionally wraps JSON in ```` ```json ```` or adds prose.
- The "be generous → helpful" tuning of the feedback prompt to stop spurious retries.
- The greeting deterministic short-circuit added in front of the classifier to avoid model variance on trivial inputs.

A fine-tune would only be worth it later to (a) shrink the classifier to a tiny cheap model for the highest-volume hop, or (b) bake in house tone — neither is justified at this stage.

## 7. Evaluation metrics

The repo has no eval harness; everything below is how I'd measure this system, with illustrative targets clearly tagged.

**Retrieval / grounding**
- **Retrieval recall@5** — fraction of golden cases where the correct KB doc id appears in the top-5 (the code's `top_k`). The primary lever for answer quality.
- **Faithfulness / groundedness** — does the resolution only assert facts present in `kb_chunks`? I'd run an LLM-judge (claim-by-claim) over reasoner output vs the retrieved context. Especially important because the reasoner is *told* it may "use best judgment" when context is thin — that's the hallucination surface.

**Answer quality**
- **Answer accuracy** vs the golden reference resolution (LLM-judge or human rating).
- **Classification accuracy** — issue_type and severity vs labels (cheap, deterministic, run on every CI build).

**Escalation behaviour**
- **Escalation precision/recall** vs the §3 escalation labels. Recall matters most: missing a true escalation (e.g. a high-severity outage answered by a bot) is the costly failure. Precision guards against dumping easy tickets on humans.
- **Deflection rate** — share of conversations resolved without escalation. The core ROI metric.

**Operational**
- **p95 end-to-end latency** per turn, and per-node latency (the README's observability plan emits `latency_ms` per node). Watch the retry path — a `not_helpful` turn roughly doubles the LLM hops.

| Metric | *Illustrative:* target |
|---|---|
| Retrieval recall@5 | *Illustrative:* ≥ 0.90 |
| Faithfulness (grounded claims) | *Illustrative:* ≥ 0.95 |
| Issue-type classification accuracy | *Illustrative:* ≥ 0.92 |
| Escalation recall (true escalations caught) | *Illustrative:* ≥ 0.98 |
| Escalation precision | *Illustrative:* ≥ 0.80 |
| Deflection rate | *Illustrative:* 60–70% |
| p95 latency (no-retry turn) | *Illustrative:* < 3 s |

## 8. Deployment architecture

**Serving layer — FastAPI** (`src/main.py`, `api/routes/support.py`):
- App is created with a `lifespan` context manager that, on startup, builds the graph **with the `CosmosDBCheckpointer`**, and — importantly — **falls back to in-memory `MemorySaver` if Cosmos init fails** (logged as a warning). So the service stays up even if the state store is misconfigured, at the cost of losing cross-turn persistence.
- `POST /support/start` — accepts `{message, conversation_id?}` (`StartRequest`); generates a `conversation_id` if absent; calls `run_graph(conversation_id, message)`; returns `{conversation_id, reply, issue_type, severity, status}` (`StartResponse`). `_extract_reply` pulls the last `AIMessage`.
- `WS /ws/{conversation_id}` — streaming/interactive loop: receive JSON `{message}`, run the graph, send back `{reply, issue_type, severity, status}`; `"exit"` closes gracefully. (Note: it's request/response per message over WS, not token-level streaming yet — token streaming via LangGraph's streaming API is the stated next step.)
- `GET /support/history/{id}` reads `graph.get_state(config)` and maps messages to `HistoryItem`s; `DELETE /support/history/{id}` calls the checkpointer's `delete_conversation`.
- CORS is wide-open (`allow_origins=["*"]`) — fine for dev, must be locked down in prod.

**Request flow:**
```
client ──HTTP/WS──> FastAPI route ──> core.graph_runner.run_graph(conversation_id, msg)
                                          │
                                          ▼  thread_id = conversation_id
                              LangGraph compiled graph
                                ├─ classifier (Groq Llama-3.3-70B)
                                ├─ {billing|technical|general}_retrieval ─> Azure AI Search
                                ├─ reasoner (Groq)
                                ├─ response_generator (Groq)
                                ├─ feedback_evaluator (Groq)
                                └─ escalation ─> Cosmos ticket (EscalationHandler)
                                          │
                          checkpoint each step ──> Azure Cosmos DB (CosmosDBCheckpointer)
```

**Backing services:** Azure AI Search (KB), Azure Cosmos DB (both LangGraph checkpoints *and* escalation tickets — they share the same Cosmos account/container config), Groq API (LLM).

**Where it runs in prod:** the README provisions **Azure Container Apps** (Bicep templates: `container_app.bicep`, `cosmos_db.bicep`, `ai_search.bicep`), built via `az acr build` and rolled out with `az containerapp update`. Observability is *planned* as per-node OpenTelemetry → Application Insights → Log Analytics, with `conversation_id` as the trace-correlation key (described in README, not yet wired in the code shown). Local dev runs `uvicorn` on port 8003. AKS would be the heavier-weight alternative if the team needs finer-grained scaling/networking control, but Container Apps is the right default for a single stateless API in front of managed state.

## 9. Business impact

*All figures illustrative — no measured production metrics exist in the repo.*

- *Illustrative:* **60–70% ticket deflection** on the FAQ long tail (billing/general), freeing human agents for the hard, high-severity cases the graph deliberately escalates.
- *Illustrative:* **cost/ticket** down sharply — a deflected ticket costs a few Groq LLM calls + one Azure AI Search query (cents) vs. minutes of agent time (dollars).
- *Illustrative:* **CSAT** held or improved by (a) instant first response, (b) grounded answers that cite real policy, and (c) a *clean* escalation path with a ticket ID and full context handed to the human, so customers don't repeat themselves.
- *Illustrative:* **faster handoff** — the escalation ticket carries the serialized conversation + resolution attempts, cutting human ramp-up time per escalated case.

## 10. Lessons learned

- **The retry guard is the system.** `retry_count >= MAX_RETRIES` is one line in `route_after_feedback`, but it's what separates a usable agent from one that traps customers in an infinite "didn't help" loop. Bounded loops + forced escalation is the pattern. (Watch the config: `MAX_RETRIES` defaults to **3** in `config.py`, while the README narrative says 2 — exactly the kind of doc drift that bites you in review.)
- **Docs drift from code — trust the code.** README says GPT-4o + vector search + retry-into-retrieval-with-query-reformulation; the running code is Groq Llama + keyword search + retry-into-reasoner with no reformulation. A senior engineer reads the source before quoting the README.
- **Structured output from open models needs guardrails.** Every LLM-JSON node has fence-stripping and a try/except fallback. Don't assume clean JSON; design for the model occasionally misbehaving.
- **Graceful degradation beats hard dependencies.** The Cosmos→MemorySaver fallback keeps the API alive when state storage is down — a deliberate availability-over-durability trade for a support front door, but one that must be alarmed so you *know* persistence was lost.
- **Re-reasoning over stale context is a weak retry.** The single highest-leverage improvement is folding the customer's clarification into a *re-retrieval* before re-reasoning, plus a confidence gate that escalates immediately when top KB similarity is low rather than spending a low-confidence attempt.
- **Cheap, separable nodes pay off.** Reusing one `temperature=0` Llama instance across nodes and gating greetings deterministically keeps both cost and latency predictable.

## Likely follow-up questions

1. **"Your README says GPT-4o but the code uses Groq Llama — which is it, and why does the difference matter?"** → The running system is `llama-3.3-70b-versatile` on Groq for low-latency, low-cost multi-hop inference; GPT-4o is documented-but-not-wired. It matters because eval numbers, cost models, and the no-vector-search reality all follow the *code*, not the doc.

2. **"Walk me through what happens when a customer replies 'that still didn't work.'"** → `feedback_evaluator_node` classifies `not_helpful` and increments `retry_count`; `route_after_feedback` loops back to `reasoner` if `retry_count < MAX_RETRIES`, else routes to `escalation`. Honest caveat: it re-reasons over the *same* chunks (no re-retrieval/query reformulation today).

3. **"How is conversation state persisted, and what happens if the service restarts mid-thread?"** → `CosmosDBCheckpointer.put()` upserts a serialized, base64-encoded checkpoint per super-step keyed by `thread_id`; on restart `get_tuple()` restores the latest checkpoint and the `add_messages` reducer replays history, so the next turn resumes with full context.

4. **"Why LangGraph instead of a ReAct agent or a plain chain?"** → Need backward, *bounded* loops (retry cap) and deterministic, testable routing to a human. A chain can't loop back; ReAct can't cleanly assert "escalate after exactly N failures." LangGraph encodes that as conditional edges you can unit-test.

5. **"How would you measure whether this is actually helping, and catch a regression?"** → Golden Q→A set with retrieval-relevance + escalation labels (§3); CI on classification accuracy + retrieval recall@5; LLM-judge faithfulness; track deflection rate and escalation precision/recall in prod; replay checkpointed conversations as regression tests.

6. **"Where's the biggest hallucination risk and how do you cut it?"** → The reasoner is told to "use best judgment" when KB context is thin — that's the unguarded surface. Add a similarity/confidence gate that escalates on weak retrieval instead of answering, and an LLM-judge faithfulness check that fails any claim not grounded in `kb_chunks`.

7. **"The retrieval is keyword/SIMPLE search with no embeddings — when does that break, and what's the upgrade?"** → It breaks on paraphrase and synonym gaps (customer says "double-billed," KB says "duplicate charge"). Upgrade to hybrid (keyword + vector) search using the embedding deployment the infra already anticipates, then re-measure recall@5.

8. **"What's missing for production readiness?"** → Token-level streaming from the responder (currently per-message over WS), real OpenTelemetry wiring (described but not in code), locked-down CORS, an alarm on the Cosmos→MemorySaver fallback, query reformulation on retry, and the eval harness itself.

# Multi-Agent Researcher — Case Study

**30-second pitch:** A CrewAI multi-agent system that turns a single research topic into a verified, cited markdown report. Three role-specialized agents — a Researcher (Azure AI Search + web search), a Critic (fact-verification and re-search delegation), and a Writer (synthesis + Cosmos DB persistence) — run as a sequential crew with shared memory, all backed by GPT-4o on Azure OpenAI and exposed through a single FastAPI `POST /research` endpoint.

---

## 1. Problem statement

Producing a trustworthy research brief on a topic is a multi-step knowledge task: you have to gather raw facts from several sources, sanity-check each one against independent evidence, drop or re-investigate the weak claims, and only then write something an executive can read. A naive single LLM call collapses all of that into one prompt and produces fluent but unverified prose — confident-sounding claims with no provenance, no contradiction-checking, and no persistence for later audit.

The system in this repo (`multi_agent_researcher`) targets exactly that gap: given a topic string (3–500 chars, validated in `main.py`'s `ResearchRequest`), it must return a structured markdown report where every factual statement carries a citation, the claims have been independently scored, and the final artifact is saved with source provenance.

## 2. Why AI/ML was needed

The core operations here are irreducibly language-and-judgment tasks that have no deterministic rule-based solution:

- **Query formulation** — expanding a topic into multiple faceted search queries (`research_task` asks for ≥3 index queries and ≥3 web queries with varied formulations).
- **Claim extraction** — reading retrieved document chunks and web snippets and distilling them into discrete factual claims with attached sources.
- **Verification judgment** — the Critic assigns each claim a 0–10 verification score and labels it supported / contradicted / unverifiable. This is qualitative source-reasoning, not arithmetic.
- **Synthesis** — composing an executive summary, thematic sections, and inline citations from a verified claim set.

All four require an LLM. The retrieval layer (Azure AI Search hybrid keyword+vector, embeddings via `text-embedding-ada-002`) is ML for relevance ranking; the agents are ML for reasoning and generation. There is no classical-ML or heuristic substitute for "is this claim well-supported by these sources?"

## 3. Dataset → Knowledge corpus & eval set

There is no training dataset. The "data" the agents consume is gathered live at inference time from two sources, plus a memory store:

- **Indexed document corpus** — `AzureDocSearchTool` (`search_tool.py`) runs hybrid search over an Azure AI Search index (`research-index`). It embeds the query with `AzureOpenAIEmbeddings` (`text-embedding-ada-002`), issues a `VectorizedQuery` against the `content_vector` field combined with keyword `search_text`, and returns up to `top_k` chunks with `id`, `content`, `source_file`, and `page_number`. If vector fields are unavailable it falls back to keyword-only search. The page-level metadata is what makes document citations auditable.
- **Live web results** — `WebSearchTool` (`web_search_tool.py`) returns `{title, url, snippet}` triples. It uses SerperDev (Google) when `SERPER_API_KEY` is set and silently falls back to DuckDuckGo (`duckduckgo-search`) otherwise. This is the freshness source for "what's true *now*."
- **Memory / persistence** — `CosmosMemoryTool` (`memory_tool.py`) upserts finished reports into Azure Cosmos DB (NoSQL), partitioned by a slugified topic key (`/topic_slug`), storing `topic`, `content`, `sources[]`, and a UTC `created_at`. It also supports `retrieve` by topic slug, so a prior report becomes reusable context. Separately, the crew itself has `memory=True` (CrewAI's built-in short/long-term memory) so agents can refer back to earlier findings *within* a run.

**Building an eval set for research-answer quality.** Since there's no labeled corpus, I'd construct a held-out set of ~50–100 topics spanning factual/stable, time-sensitive, and contested categories. For each I'd record: (a) a gold set of must-include facts and their authoritative sources (human-curated), and (b) a set of known-false "trap" claims to test the Critic's rejection behavior. Scoring dimensions per run: claim recall against the gold facts, citation validity (does the cited URL actually support the claim — checked with an LLM-as-judge plus spot human review), hallucinated-claim rate, and Critic precision/recall on the planted traps. This gives a regression harness so prompt/role edits can be measured rather than eyeballed.

## 4. Feature engineering → Prompt & context engineering

This is where the real engineering lives — there are no learned features, only **role prompts, task decomposition, tool schemas, and inter-agent context passing.**

**Agent role prompts (`agents.py`).** Each `crewai.Agent` is defined by a `role`, `goal`, and `backstory` that together act as a persistent system prompt, plus a constrained toolset and an iteration budget:

- **Researcher** — role `"Research Specialist"`. Goal mandates ≥10 distinct factual claims each with a source URL/doc reference, gathered via the index and live web. Backstory primes it to "cast a wide net" and to refine queries when the Critic requests a re-search. Tools: `[_doc_search, _web_search]`. `allow_delegation=False`, `max_iter=8`.
- **Critic** — role `"Fact Verification Specialist"`. Goal: score every claim 0–10, flag contradictions/stale data, and for any claim < 6 issue a *targeted* re-search with specific refined terms. Tools: `[_web_search]` (it can independently cross-check on the web but deliberately has no index or memory access). `allow_delegation=True` — this is the agent permitted to delegate work back. `max_iter=6`.
- **Writer** — role `"Research Report Writer"`. Goal: synthesize verified claims into a structured report (exec summary, themed sections with inline citations, conclusion, numbered references) and then persist it via the memory tool. Tools: `[_cosmos_memory]` only. `allow_delegation=False`, `max_iter=5`.

The toolset asymmetry is intentional context engineering: the Researcher gathers, the Critic verifies (web-only, so it can't just re-read the Researcher's index hits), and the Writer persists. No agent has more capability than its role requires.

**Task decomposition (`tasks.py`).** `build_tasks(topic)` produces three `crewai.Task` objects whose `description` strings are step-by-step procedures and whose `expected_output` strings pin the exact output schema (a markdown claims list, then a `| # | Claim | Score | Source | Status |` verification table, then an ≥800-word report ending in `Report saved to Cosmos DB: <id>`). Pinning `expected_output` is what lets the downstream FastAPI regexes in `main.py` (`_extract_sources`, `_extract_cosmos_id`) reliably parse the result.

**Context passing between agents.** The hand-off is explicit, not implicit:
- `critic_task` declares `context=[research_task]` — the Critic literally receives the Researcher's output as its working input.
- `writer_task` declares `context=[critic_task]` — the Writer's source of truth is the *verified* claim list, not the raw one.
- The crew runs `Process.sequential` (`crew_builder.py`), so the order Researcher → Critic → Writer is guaranteed, and `memory=True` gives a shared scratchpad across the three.

The re-search loop is modeled as Critic delegation: a low-scoring claim triggers the Critic (which has `allow_delegation=True`) to send refined query terms back to the Researcher, who appends new findings. This is the "self-correction" that a single pass cannot do.

## 5. Model selection rationale

**LLM.** All three agents share one model instance, `_llm` in `agents.py`: `AzureChatOpenAI` pointed at the Azure OpenAI deployment named by `settings.azure_openai_deployment` (default `"gpt-4o"`), `api_version="2024-02-01"`, `temperature=0.2`. Embeddings use `text-embedding-ada-002` (`azure_embedding_deployment`). The low temperature is the right call for a factuality-first workload — you want determinism and faithful synthesis, not creative variance. GPT-4o is a sensible default: it's strong at tool-use/function-calling (essential for the three CrewAI tools) and at long-context synthesis, and routing through Azure OpenAI keeps it inside the same Azure tenancy as Search and Cosmos for data-residency/compliance reasons.

*Trade-off note:* a single shared model keeps things simple but is not necessarily cost-optimal. The Critic's job (scoring/flagging) and the Researcher's query-refinement are arguably cheaper-model tasks; a production iteration could route those to a smaller/faster deployment and reserve the top model for the Writer's synthesis. The code currently uses one model for all three.

**Why multi-agent (CrewAI) vs a single agent — and what it costs.** A single agent *could* be prompted to "research, verify, then write." The reason this is decomposed into three:

1. **Separation of concerns / role focus.** Each agent has a narrow goal, a narrow toolset, and its own `max_iter` budget. A focused "fact-verification specialist" with only a web tool behaves more skeptically than one omnibus prompt juggling gather-verify-write simultaneously, where verification tends to get short-changed.
2. **Adversarial self-correction.** The Critic is structurally separate from the Researcher, with the explicit power to *reject* and *re-delegate* (score < 6). That structural independence is hard to enforce inside a single agent that grades its own homework.
3. **Auditability.** Three discrete task outputs (raw claims → scored table → final report) give intermediate artifacts you can inspect and test, versus one opaque generation.

The cost is real and worth stating plainly in an interview:
- **Latency** — sequential execution means three agents run back-to-back, each potentially looping (max_iter 8/6/5) and making multiple tool/LLM calls. `main.py`'s endpoint docstring itself states *"expect 2–5 minutes for a full report"* (*Illustrative:* operator estimate in the code, not a measured benchmark).
- **Tokens/cost** — re-feeding the Researcher's claims into the Critic and the Critic's table into the Writer (the `context=[...]` chaining) multiplies prompt tokens versus one call. The re-search loop adds further round-trips. Roughly *Illustrative:* 3–6× the token cost of a single-shot generation, depending on how many claims trigger re-search.

For a high-stakes, citation-required research output, that latency/cost premium buys verification and provenance — a defensible trade. For a low-stakes summary it would be over-engineering.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**There is no training and no fine-tuning, and that is the correct choice here.** The task is orchestration of reasoning over *live* data — the corpus changes every run (fresh web results, an evolving Azure Search index), so any fine-tuned weights would be stale immediately and couldn't encode "today's" facts. The leverage is entirely in retrieval quality + prompt/role design, which is exactly what an orchestrated-prompting (agentic) approach optimizes.

The iteration loop is on **prompts and roles, not gradients**:
- Tightening each agent's `goal`/`backstory` (e.g., the Researcher's explicit "≥10 claims with sources," the Critic's explicit "< 6 → re-search").
- Pinning `expected_output` schemas so downstream parsing is stable.
- Tuning structural knobs: `max_iter` per agent, `temperature=0.2`, which tools each role gets, and `allow_delegation` (only the Critic has it).
- Adjusting the verification threshold (the `< 6` re-search trigger) to trade thoroughness against latency.

If quality plateaued, the next levers — still short of fine-tuning — would be better retrieval (chunking, reranking, more index queries) and possibly model routing per role. Fine-tuning would only enter the picture for a fixed, narrow domain with stable terminology, which this general-purpose researcher is not.

## 7. Evaluation metrics

The repo ships task-level `expected_output` contracts and FastAPI parsers but no automated quality scorer, so the metrics below are the ones I'd track; numbers are illustrative.

- **Research-answer quality** — human or LLM-judge rubric over the final report (coverage, structure, readability). The Writer task already enforces structural minimums (required sections, ≥800 words).
- **Factuality / citation rate** — fraction of factual statements carrying a valid inline citation whose source actually supports the claim. The pipeline is *designed* to make this measurable: `main.py:_extract_sources` parses the `## References` section into structured `SourceProvenance` items, and the Critic's score gate is meant to keep only claims scoring ≥ 6. *Illustrative target:* ≥ 95% of statements cited, ≥ 90% citation-validity.
- **Task-completion rate** — fraction of runs that emit a well-formed report ending in `Report saved to Cosmos DB: <id>` (parsed by `_extract_cosmos_id`). A missing id signals the Writer failed to persist — a concrete success/fail signal already wired in.
- **Critic effectiveness** — precision/recall on planted false claims from the eval set (§3); how often re-search actually raises a claim above the 6 threshold.
- **Cost & latency per run** — wall-clock (the API returns `elapsed_seconds` via `time.perf_counter()`, so latency *is* measured per request) and total tokens/USD per report. *Illustrative:* 2–5 min/run and 3–6× single-shot token cost (see §5). `elapsed_seconds` is the one genuinely measured number here; token cost is not currently instrumented.

## 8. Deployment architecture

**Crew orchestration flow.** A request to `POST /research` (`main.py`) validates the topic, then calls `build_crew(topic)` (`crew_builder.py`), which assembles:

```
Crew(process=Process.sequential, memory=True, verbose=True, full_output=True)
  agents = [researcher_agent, critic_agent, writer_agent]
  tasks  = [research_task, critic_task, writer_task]
```

Execution path on `crew.kickoff()`:

```
POST /research {topic}
   │
   ▼
Researcher  ── azure_doc_search (Azure AI Search, hybrid vector+keyword)
   │          ── web_search (Serper → DuckDuckGo fallback)
   │          → markdown list of ≥10 raw claims + sources
   ▼   (critic_task.context = [research_task])
Critic      ── web_search (independent cross-check)
   │          → scores each claim 0–10; claim < 6 ⇒ re-search delegation back to Researcher
   │          → verified claims table (score ≥ 6 only) + flagged issues
   ▼   (writer_task.context = [critic_task])
Writer      ── cosmos_memory (operation="save")
   │          → structured markdown report w/ inline citations + References
   │          → upsert to Cosmos DB, returns "Report saved to Cosmos DB: <id>"
   ▼
FastAPI parses report → ResearchResponse{report_markdown, sources[], elapsed_seconds, cosmos_db_id}
```

**Where it runs.** The service is a FastAPI app (`title="Multi-Agent Researcher"`, `/health` liveness + `/research`) served by Uvicorn on port 8001. The README's deployment target is Azure Container Apps (built via `az acr build`, container image `multi-researcher`), with Azure OpenAI (GPT-4o + ada-002 embeddings), Azure AI Search, and Azure Cosmos DB as the three backing services, provisioned by Bicep templates under `infra/`. The crew runs **synchronously** inside the request — which is why the endpoint warns of multi-minute latency. A production hardening step would be to move `crew.kickoff()` to a background task/queue and return a job id, since a 2–5 minute synchronous HTTP request is fragile under load and timeouts.

## 9. Business impact

*All figures here are illustrative and not measured by the code.*

- *Illustrative:* a thorough, cited research brief that takes an analyst 2–4 hours of manual searching, cross-checking, and writing is produced in ~2–5 minutes of crew runtime — on the order of **20–50× faster** for a first draft.
- *Illustrative:* if a team produces ~40 such briefs/month, that's roughly **80–160 analyst-hours/month saved**, with the human shifting from gather-and-draft to review-and-approve.
- **Quality/risk angle (qualitative, real):** because the Critic gates claims and the Writer persists provenance to Cosmos DB, every report is auditable after the fact — a governance benefit that a single-shot LLM summary does not provide. The value isn't just speed; it's a *defensible* artifact.

The honest framing for an interview: the win is draft-acceleration plus auditability, not full automation — a human still reviews before anything is published.

## 10. Lessons learned

- **Decomposition buys verification, and you pay for it in latency/tokens.** Splitting research/critique/writing into separate agents is what makes adversarial fact-checking and re-search possible, but it triples (or more) the call count. Know when the topic is worth that premium.
- **Tool asymmetry is a feature.** Giving the Critic *only* web search (no index, no memory) forces genuine independent cross-checking instead of re-confirming the Researcher's own hits. Constraining toolsets per role is a real design lever.
- **Pin output schemas or downstream parsing breaks.** The FastAPI layer extracts sources and the Cosmos id with regexes that depend on the Writer emitting exactly `## References` and `Report saved to Cosmos DB: <id>`. The `expected_output` contracts in `tasks.py` are load-bearing — drift in the prompt silently breaks `_extract_sources`/`_extract_cosmos_id`.
- **Synchronous crew-in-request doesn't scale.** A 2–5 minute blocking HTTP call is a known weak point; the clear next step is async job submission + polling.
- **Graceful tool degradation matters.** Both the doc-search (vector → keyword fallback) and web-search (Serper → DuckDuckGo fallback) tools degrade instead of crashing, which keeps the crew alive when a backend or API key is missing — important for a long pipeline where one failed tool call shouldn't waste the whole run.
- **No fine-tuning was the right default.** With live-changing data, prompt/role iteration and retrieval quality were the high-leverage knobs; gradients would have added cost and staleness for no gain.

## Likely follow-up questions

1. **"Why three agents instead of one well-prompted agent?"** → Structural separation enables an independent Critic that can reject and re-delegate (score < 6), plus inspectable intermediate artifacts; the cost is ~3–6× tokens and multi-minute latency (§5).
2. **"How do you stop the re-search loop from running forever?"** → Per-agent `max_iter` caps (Researcher 8, Critic 6, Writer 5) and the Critic's discrete < 6 threshold bound the iterations; I'd also add a global wall-clock/turn budget at the crew level.
3. **"How do you actually measure factuality, not just claim it?"** → Build the §3 eval set (gold facts + planted false claims), then score citation-validity and Critic precision/recall with LLM-as-judge plus human spot-checks; today only `elapsed_seconds` is truly measured.
4. **"What happens if a tool fails — say Azure Search or the Serper key is missing?"** → Both tools degrade gracefully (vector→keyword, Serper→DuckDuckGo) and return error strings rather than throwing, so the crew continues; the Writer's Cosmos save returning no id is the failure signal the API surfaces.
5. **"This blocks the HTTP request for minutes — how would you productionize it?"** → Move `crew.kickoff()` to a background worker/queue, return a job id immediately, and let the client poll `/research/{id}`; the current synchronous design is fine for a demo, not for concurrency.
6. **"Could you cut cost without hurting quality?"** → Route per-role models (smaller model for Critic scoring and Researcher query-refinement, GPT-4o reserved for Writer synthesis), cache/retrieve prior reports from Cosmos via the memory tool's `retrieve` op, and cap re-searches.
7. **"How does context actually flow between agents — is it shared global memory or explicit?"** → Explicit `context=[research_task]` and `context=[critic_task]` hand-offs define the data dependency, on top of CrewAI's `memory=True` shared scratchpad; the explicit context is what guarantees the Writer uses the *verified* claims, not the raw ones.
8. **"Why GPT-4o at temperature 0.2, and would Claude or a smaller model change the design?"** → 0.2 favors faithful, deterministic synthesis for a factuality-first task; GPT-4o is strong at tool-use and stays in-tenancy with Azure Search/Cosmos. The architecture is model-agnostic — any strong tool-calling chat model could back the agents; the decomposition, not the specific model, is what delivers verification.

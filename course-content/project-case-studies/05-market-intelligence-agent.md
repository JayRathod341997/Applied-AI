# Market Intelligence Agent — Case Study

**30-second pitch:** A multi-agent RAG platform that turns a market question into an evidence-backed executive briefing. An orchestrator coordinates four specialized roles — retrieval (hybrid Azure AI Search), reasoning (GPT-4o synthesis), and a separate validation agent that scores how well every claim is grounded in retrieved evidence using embedding cosine similarity. The validation loop is the anti-hallucination spine: nothing ships without a 0.0–1.0 confidence score and a HIGH/MEDIUM/LOW label.

---

## 1. Problem statement

Strategy, corp-dev, and investment teams need timely synthesis of market signals — competitor moves, industry trends, financial figures — pulled from a growing corpus of reports and news. Doing this by hand is slow, inconsistent, and doesn't scale across the volume of incoming material. Worse, a naive LLM summarizer over this corpus will confidently fabricate statistics, company names, and dates, which is unacceptable for decisions involving real money and risk.

The concrete requirements baked into the code:
- Produce a **structured executive briefing** (Executive Summary, Key Market Signals, Competitive Landscape, Strategic Implications, Evidence Gaps) — see the `SYSTEM_PROMPT` in `orchestrator.py` and `reasoning_agent.py`.
- Attach a **machine-checkable confidence score** to every output so a human knows when to trust it (`ValidationAgent`, `CONFIDENCE_THRESHOLD=0.75`).
- Every factual claim must **trace back to a retrieved chunk**; insufficient context must be stated explicitly rather than extrapolated.

## 2. Why AI/ML was needed

This is a natural-language synthesis problem over unstructured documents — exactly where deterministic rules and keyword search fall short:

- **Synthesis across sources.** The output isn't an extract; it's a reasoned narrative that connects signals across multiple chunks into competitive and strategic implications. That requires an LLM (GPT-4o here).
- **Semantic retrieval.** Analysts ask questions in natural language ("latest competitive moves by hyperscalers in the AI chip market") that don't lexically match the source text. Dense vector retrieval over embeddings is needed alongside keyword matching — hence the **hybrid BM25 + vector** search.
- **Grounding verification at scale.** A human can eyeball whether a paragraph is supported by sources, but you can't put a human on every output. The `ValidationAgent` operationalizes "is this grounded?" as an embedding-similarity computation, giving a numeric, reproducible signal.

The design deliberately avoids training a model: the knowledge changes constantly (new reports daily), so the leverage is in *retrieval freshness + a validation gate*, not in baking facts into weights (see §6).

## 3. Dataset → Knowledge corpus & eval set

**The corpus.** There is no labeled training set. The "dataset" is a **knowledge corpus indexed in Azure AI Search** (`settings.azure_search_index = "market-intel-index"`). Each document chunk carries the fields the retrieval layer selects: `id`, `content`, `source`, `title`, `published_date`, plus a `content_vector` field holding the dense embedding (`retrieval_agent.py` / `search_tool.py`). Source provenance (`source`, `published_date`) is first-class so the reasoning agent can attribute claims with `[Source: ...]` and so a reader can judge recency.

**Embeddings.** Chunks are embedded with Azure OpenAI `text-embedding-ada-002` (`azure_openai_embedding_deployment`) — the same model used at query time and at validation time, so all three live in one vector space (critical: the validation comparison is only meaningful because claim and source embeddings come from the same embedder).

**Storage of outputs.** Final reports are persisted as JSON to **Azure Blob Storage** (`reports` container) partitioned by date (`reports/YYYY/MM/DD/<uuid>.json`) via `BlobStorageTool`. This output store doubles as a labeling queue for building an eval set.

**Building a golden eval set with factuality labels (how I'd do it).** *Illustrative design, not in the repo:*
- Sample ~200 representative queries spanning competitor analysis, market sizing, and trend questions.
- For each, freeze the retrieved chunk set and the generated briefing, then have analysts label each atomic claim as `supported` / `unsupported` / `contradicted` against those chunks — yielding a per-claim factuality label and a per-report groundedness label.
- Keep a held-out slice of "trap" queries whose corpus genuinely lacks the answer, to measure whether the system correctly emits an **Evidence Gaps** section instead of hallucinating.
- This golden set lets you calibrate the `0.75` confidence threshold against human-judged groundedness (turn the cosine score into a tuned decision boundary rather than a guessed constant).

## 4. Feature engineering → Prompt & context engineering

This is where the multi-agent RAG design earns its keep. The pipeline is **Retrieval → Reasoning → Validation**, exposed two ways: a deterministic `RAGChain` (fixed sequence, fast, predictable) and an agentic `OrchestratorAgent` (a LangChain `AgentExecutor` that can decide to retrieve multiple times).

**Stage 1 — Retrieval Agent (`retrieval_agent.py`, `search_tool.py`).**
- **Hybrid search.** Embeds the query with `AzureOpenAIEmbeddings`, then issues a single Azure AI Search call that combines BM25 full-text (`search_text=query`) with a `VectorizedQuery` (`k_nearest_neighbors=top_k`, `fields="content_vector"`). Hybrid recall beats either lexical or vector alone — keyword catches exact ticker/company tokens, vectors catch paraphrase.
- **Context engineering.** `RetrievalResult.to_context_string()` formats chunks into a numbered block (`[1] Source: ... | Title: ... | Date: ...`) so the reasoning model can cite by source and date. `top_k` defaults to 10 (`config.py`), overridable per request (`/analyze` accepts `top_k` 1–50).

**Stage 2 — Reasoning Agent (`reasoning_agent.py`).**
- GPT-4o at `temperature=0.2` (low, for factual stability).
- Its `SYSTEM_PROMPT` enforces **STRICT RULES**: every claim grounded in provided context; state the limitation if context is insufficient; **do NOT fabricate statistics, company names, dates, or financial figures**; attribute facts with `[Source: ...]`. The `HUMAN_TEMPLATE` injects `{query}` + `{context}` and demands the fixed five-section output format. This prompt is the *first* line of hallucination defense — constrain generation to the evidence.

**Stage 3 — Validation Agent (`validation_agent.py`) — the hallucination guard.**
- Splits the generated analysis into sentences (`claim.split(".")`, keeping fragments >20 chars to skip noise).
- Embeds each claim sentence and each source chunk with the same `text-embedding-ada-002`.
- For each sentence, takes the **max cosine similarity** across all source chunks (best-supporting evidence), then averages those per-sentence maxima into a single `confidence_score`.
- Labels via thresholds: `>= 0.75` → **HIGH** (well-grounded), `0.50–0.74` → **MEDIUM** (some extrapolation risk), `< 0.50` → **LOW** (hallucination risk, review recommended). Empty sources or no scorable sentences → score `0.0` / LOW (fail-closed).
- This catches the failure the prompt can't fully prevent: a fluent sentence with **no embedding support in any retrieved chunk** drags the mean down and flips the label, surfacing the risk to the caller instead of hiding it. (Note: there are two implementations — the dataclass-returning `ValidationAgent` in `validation_agent.py` used by the pipeline, and a thinner standalone `validate_and_score()` in `validation.py` returning just the float.)

**Orchestrator prompt (`orchestrator.py`).** The agentic path adds a tool-use loop: the `SYSTEM_PROMPT` instructs the agent to call `azure_market_search`, synthesize, optionally **refine the query and search again**, then call `save_report_to_blob`. It runs as a `create_openai_functions_agent` inside an `AgentExecutor` (`max_iterations=10`, `handle_parsing_errors=True`, `return_intermediate_steps=True`). Crucially, the orchestrator collects the tool observations from `intermediate_steps` and feeds them to the *same* `ValidationAgent` for post-hoc scoring — so even the dynamic agent path is gated by groundedness validation.

## 5. Model selection rationale

- **LLM: Azure OpenAI GPT-4o** (`azure_openai_deployment = "gpt-4o"`, `api_version="2024-02-01"`, `temperature=0.2`). Chosen for strong instruction-following on the strict no-fabrication rules and reliable structured-section output; low temperature trades creativity for factual consistency. Running on **Azure OpenAI** (vs. another provider) keeps the LLM, embeddings, vector store, and storage inside one Azure tenant — data residency, single auth surface, and enterprise compliance.
- **Embeddings: `text-embedding-ada-002`.** Same model for indexing, query, and validation — non-negotiable, because the validation cosine comparison is only valid within one embedding space.
- **Retrieval: Azure AI Search, hybrid (BM25 + vector).** Trade-off: a pure vector DB (e.g. a bare ANN store) would miss exact-token matches (tickers, product names); pure BM25 misses paraphrase. Hybrid is the pragmatic best-recall default, and Azure AI Search gives both in one managed index alongside the metadata fields needed for attribution.
- **Why a separate validation agent (not just trust the prompt).** Prompt rules reduce hallucination but can't *prove* grounding — the model can still emit a confident, unsupported sentence. Separating validation into an independent, embedding-based check means: (a) it's model-agnostic and not fooled by fluent prose, (b) it produces a numeric score you can threshold, log, and calibrate, and (c) it's reusable across both the deterministic and agentic paths. Defense-in-depth: constrain generation *and* verify the result.
- **Two execution modes by design.** `RAGChain` (deterministic, single retrieval) for predictable low-latency Q&A; `OrchestratorAgent` (multi-round tool-use) when a question needs iterative evidence gathering. The API defaults to the cheaper deterministic path (`use_agent=False`).

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No model training or fine-tuning — deliberately.**

- The knowledge is **volatile** (new market reports/news continuously). Fine-tuning bakes facts into weights that go stale immediately and can't cite sources. Retrieval keeps the system current by just re-indexing; the LLM stays a fixed reasoning engine over fresh evidence.
- **Attribution and auditability** require pointing at a `source`/`published_date`, which a fine-tuned model cannot do — RAG can.
- The right "training loop" here is a **validation loop**, not gradient descent: generate → score groundedness → gate. That gives a continuous quality signal without the cost, latency, and staleness of fine-tuning.

**What gets iterated instead — the prompts.** The leverage is in prompt engineering: the strict no-fabrication rules, the mandatory five-section format, the `[Source: ...]` attribution requirement, and the explicit "state Evidence Gaps rather than extrapolate" instruction. The intended iteration cycle (using the golden eval set from §3): run candidate prompts, measure groundedness/validation labels and the trap-query gap-detection rate, and tighten the prompt where unsupported claims slip through. The `0.75` confidence threshold is itself a tunable knob calibrated against human factuality labels.

## 7. Evaluation metrics

The codebase computes and exposes these per request (`AnalyzeResponse`, `validation_details`):

- **Confidence / groundedness score (measured, in-code).** Mean of per-sentence max cosine similarity between claim sentences and source chunks (`ValidationAgent`), with `sentence_scores`, `sentences_evaluated`, and `sources_compared` returned for diagnostics. This is the system's faithfulness proxy.
- **Confidence label (measured).** HIGH / MEDIUM / LOW from the 0.75 / 0.50 thresholds — the operational pass/review/block signal.
- **Sources used (measured).** Count of evidence chunks the answer rests on.
- **Latency (measured).** `latency_ms` is timed end-to-end in `/analyze` via `time.perf_counter()`.

Metrics I'd track on the golden eval set to validate the validator (*Illustrative targets, not measured*):

- **Validation catch-rate (hallucinations blocked).** Of reports a human labels as containing an unsupported claim, the % the validator flags below threshold. *Illustrative target: ≥ 85% of hallucinated reports scored MEDIUM/LOW.*
- **Groundedness/faithfulness vs. human labels.** Correlation between the cosine confidence score and human per-claim factuality. *Illustrative: Pearson r ≈ 0.7.*
- **Answer accuracy.** % of HIGH-confidence briefings judged factually correct by analysts. *Illustrative target: ≥ 90%.*
- **False-block rate.** % of genuinely-grounded reports wrongly pushed below 0.75 (the cost of the gate). *Illustrative: < 10%.*
- **Latency p50/p95** and **cost/query.** Embedding + GPT-4o token cost dominates; validation adds N+M extra embedding calls (N claim sentences + M chunks). *Illustrative: p95 ≈ 6–9 s, ≈ $0.02–0.05/query for the deterministic path.* Token usage (`prompt_tokens`/`completion_tokens`) is already captured in `ReasoningResult` for cost tracking.

*Known limitation to call out in interview:* cosine-similarity groundedness rewards topical/lexical overlap, so a sentence that's *on-topic but factually wrong* can still score high (a paraphrased-but-false statistic that's near a real one). It catches off-evidence hallucination well; it does not catch subtle numerical fabrication — that's why I'd pair it with an LLM-judge faithfulness check (claim-by-claim NLI/entailment) as a second validation pass.

## 8. Deployment architecture

**Runtime.** Containerized FastAPI service on **Azure Container Apps** (`src/main.py`; `infra/*.bicep`). Two endpoints: `POST /analyze` (run pipeline) and `GET /health`. Agents are warmed at startup via the FastAPI `lifespan` hook (`_orchestrator` + `_rag_chain` instantiated once, reused per request).

**Request flow (the multi-agent pipeline):**

```
User / Scheduler
      │  POST /analyze {query, use_agent, top_k}
      ▼
FastAPI (Azure Container Apps)
      │
      ├─ use_agent=false (default) ──► RAGChain.arun()
      │        Retrieval Agent ──► Reasoning Agent ──► Validation Agent
      │
      └─ use_agent=true ────────────► OrchestratorAgent.run()
               AgentExecutor loop (create_openai_functions_agent, GPT-4o)
                 ├─ tool: azure_market_search (hybrid BM25+vector)   [multi-round]
                 ├─ synthesize structured briefing
                 ├─ tool: save_report_to_blob
                 └─ post-hoc ValidationAgent scoring
                          │
                          ▼
   ┌──────────────┬───────────────────┬─────────────────┐
   │ Azure AI     │ Azure OpenAI      │ Azure Blob      │
   │ Search       │ GPT-4o +          │ Storage         │
   │ (vector +    │ ada-002 embeds    │ reports/Y/M/D/  │
   │  BM25 index) │                   │  <uuid>.json    │
   └──────────────┴───────────────────┴─────────────────┘
```

- **Orchestrator → Retrieval → Reasoning → Validation → Storage**, exactly as the agent roles table in the README. The deterministic path runs the three agents in fixed sequence; the agentic path lets the orchestrator decide how many `azure_market_search` rounds to run and persists via `save_report_to_blob`.
- **External dependencies:** Azure AI Search (retrieval), Azure OpenAI (GPT-4o + embeddings), Azure Blob Storage (report persistence). Config via `pydantic-settings` from env (`config.py` / `.env`).
- **Async throughout** (`arun`/`ainvoke`/`aembed_documents`) so the service handles concurrent `/analyze` calls without blocking, even though the Azure Search SDK itself is synchronous (wrapped).
- **Failure handling:** pipeline exceptions return HTTP 500 with the error; pre-warm not finished returns 503; empty evidence fails closed to confidence 0.0 / LOW.

**Where I'd harden it for production (*illustrative*):** put the validation threshold on the response path so HIGH auto-publishes while MEDIUM/LOW route to human review; add caching of query embeddings; emit the confidence score and latency to App Insights for monitoring drift.

## 9. Business impact

*All figures Illustrative (not measured in the repo):*

- *Illustrative:* analyst time per market briefing cut from ~2–3 hours to minutes, with consistent structure and source attribution.
- *Illustrative:* the confidence gate auto-clears ~70% of briefings (HIGH) for immediate use, routing the rest to review — concentrating scarce analyst attention on the genuinely uncertain outputs.
- *Illustrative:* hallucination incidents reaching a decision-maker reduced sharply because every claim carries a groundedness score and `[Source: ...]` attribution, making unsupported statements visible before they ship.
- *Illustrative:* persisted JSON reports in Blob Storage create an auditable trail of what was claimed, on what evidence, and how confident the system was — valuable for compliance and post-hoc review.

## 10. Lessons learned

- **Separate the validator from the generator.** Trusting prompt rules alone to prevent hallucination is wishful; an independent, embedding-based groundedness check turns "trust me" into a number you can threshold and log.
- **Same embedding model everywhere or the score is meaningless.** Indexing, query, and validation all use `text-embedding-ada-002` — mixing embedders would silently break the cosine comparison.
- **Cosine groundedness is a topicality proxy, not truth.** It catches off-evidence hallucination but can be fooled by on-topic-but-false numbers; a real system needs a second, claim-level entailment/LLM-judge pass for numerical faithfulness.
- **Hybrid retrieval beats picking one.** Keyword for exact tokens (tickers, product names), vectors for paraphrase — both in one Azure AI Search call.
- **Give yourself two execution modes.** A deterministic `RAGChain` for predictable, cheap, low-latency answers and an agentic orchestrator for questions needing iterative evidence — and gate *both* through the same validation agent.
- **Fail closed.** No sources or no scorable sentences → confidence 0.0 / LOW, not a silent pass.
- **Capture tokens, latency, and provenance from day one.** They're already in the data classes/response — that's what makes later cost analysis and eval-set construction possible.

## Likely follow-up questions

1. **Your validation agent uses cosine similarity — how does it actually catch a hallucination, and where does it fail?** → It scores each claim sentence by its best (max) cosine match to any source chunk and averages; an unsupported sentence has no near chunk and drags the mean below 0.75. It fails on *on-topic but numerically false* claims that sit near a real one in embedding space — pair it with claim-level NLI/LLM-judge.

2. **Why a separate validation step instead of just a stricter system prompt?** → Prompts reduce but can't prove grounding; an independent embedding check is model-agnostic, yields a numeric, calibratable score, and is reused across both the deterministic and agentic paths (defense-in-depth).

3. **How did you pick the 0.75 / 0.50 thresholds, and how would you validate them?** → They're configured constants (`CONFIDENCE_THRESHOLD=0.75`); I'd calibrate them against a golden set of human per-claim factuality labels, choosing the boundary that maximizes catch-rate at an acceptable false-block rate.

4. **Why hybrid BM25 + vector retrieval rather than pure vector?** → Keyword catches exact tokens (tickers, product/company names) that embeddings blur; vectors catch paraphrase the query doesn't lexically match — hybrid gives best recall, in a single Azure AI Search call.

5. **When does the agentic orchestrator earn its cost over the deterministic RAGChain?** → When one retrieval round is insufficient and the agent needs to refine the query and search again (`max_iterations=10`); for straightforward Q&A the deterministic path is faster, cheaper, and more predictable, so it's the API default (`use_agent=False`).

6. **You don't fine-tune — defend that for a market-intelligence product.** → Market facts are volatile and must be cited; fine-tuning bakes in stale, unattributable knowledge. Retrieval keeps facts fresh and auditable; the "training loop" is a generate→validate→gate loop, plus prompt iteration on the golden set.

7. **How do you handle a query the corpus genuinely can't answer?** → The prompts mandate an explicit **Evidence Gaps** section and "state the limitation rather than extrapolate"; if nothing scores well the validation score collapses to LOW. I'd measure this with held-out trap queries (gap-detection rate).

8. **What breaks first at scale, and how do you monitor it?** → Cost/latency from the extra embedding calls in validation (N sentences + M chunks) and GPT-4o tokens; I'd cache query embeddings, emit `confidence_score`/`latency_ms`/token usage to telemetry, and watch for confidence-distribution drift signaling stale or degraded retrieval.

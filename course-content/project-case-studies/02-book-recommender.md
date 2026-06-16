# Book Recommender — Case Study

**30-second pitch:** A semantic book recommender that takes a natural-language reading intent ("a melancholy story about memory and loss set in post-war Europe") and returns ranked books with LLM-written justifications. It chunks and embeds book descriptions with Azure OpenAI `text-embedding-ada-002`, stores them in Azure AI Search (HNSW vector index), retrieves via hybrid vector+keyword search, sharpens ranking with a `cross-encoder/ms-marco-MiniLM-L-6-v2` reranker, and uses `gpt-4o` to explain why each book matches. It is a retrieval-first system: the LLM is the last and cheapest-to-swap stage, not the engine.

---

## 1. Problem statement

Traditional book discovery is keyword- and tag-driven: you search "WWII Europe" and get a genre shelf, but you cannot express tone, theme, or emotional resonance. Users describe what they *want to feel* ("quiet, melancholic, about memory") far better than they can name authors or categories. The system must map free-text intent onto a catalog and return a short, ranked, explained list — not 10,000 keyword hits.

The serving contract is concrete in the code: `POST /recommend` takes `{query, top_k, filters?}` (`models.py` `RecommendationRequest`, `top_k` bounded `1..50`) and returns `RecommendationResponse` with a list of `{title, author, reason, score}` (`models.py` `BookRecommendation`).

## 2. Why AI/ML was needed

The core requirement — "understand intent beyond keyword matching" — is exactly what lexical search (BM25 alone) cannot do. Three capabilities make this an AI problem:

1. **Semantic matching** — dense embeddings place "melancholy story about memory" near a synopsis that never uses those words. This is the embedding step.
2. **Relevance ranking under ambiguity** — first-stage vector recall is high-recall/low-precision; a cross-encoder reads the (query, passage) pair jointly to re-order the shortlist.
3. **Explanation** — the product value is not just *which* books but *why*; `gpt-4o` generates the 1–2 sentence rationale per book.

Note the division of labor: matching and ranking are done by embeddings + a small reranker (cheap, deterministic, no generation risk); only the human-facing explanation uses a large LLM. That keeps cost and latency on the hot path low.

## 3. Dataset → Knowledge corpus & eval set

**The corpus.** Source is book *metadata* (CSV in `data/sample_books.csv`; `indexer.py` reads it with pandas). Each row is normalized via `col_map` (`authors→author`, `categories→genre`, `published_year→year`) and must contain `{title, author, genre, year, description}`. The retrievable text is the **`description` (synopsis)** field — that is what gets chunked and embedded. Metadata (`genre`, `year`, `title`, `author`) is carried as filterable/facetable index fields for hybrid filtering.

**Chunking strategy & sizes.** `chunker.py` `sentence_aware_chunking` splits the description into overlapping **word-level** windows: `chunk_size=512`, `overlap=64`, stride `= chunk_size - overlap = 448` words. Honest read of the code: despite the name, it is a *word-count* sliding window (`text.split()`), not true sentence-boundary chunking — the docstring itself flags that spaCy/NLTK would be the real implementation. For short book synopses, most books produce a single chunk; only long descriptions split. Each chunk becomes its own index document carrying full book metadata plus `chunk_index` and `chunk_text` (`indexer.py`), so one book can occupy several rows.

**Building a relevance-judged eval set.** Code gives a recipe (`README` Evaluation Strategy) but no labels. I would build:
- **Golden (query → expected book) pairs** — curate 100–300 natural-language intents with one or more known-correct titles, drawn from real user phrasings, covering tone/theme/setting axes, not just genre.
- **Graded judgments** for nDCG — for each query, label a candidate pool (the union of top-K from a few retrieval variants) on a 0–3 relevance scale so we can measure *ordering* quality, not just hit/miss.
- **Hard negatives** — same-genre-but-wrong-tone books to catch the failure where embeddings collapse on surface topic and ignore mood.
- **De-duplication caveat:** because chunks are per-document, eval must aggregate chunks back to the book level before scoring, or recall@k is inflated by multiple chunks of the same title.

## 4. Feature engineering → Prompt & context engineering

The GenAI analog of feature engineering is the entire ingest→retrieve→rerank chain. Each stage is a deliberate representation choice.

**(a) Chunking** — see §3. Trade-off baked into the code: a 512-word window with 64-word overlap is large enough to keep a synopsis coherent (avoid fragmenting a plot summary) while overlap prevents losing context at boundaries. For book synopses this is generous; the risk is that *very long* descriptions dilute a single chunk's signal.

**(b) Embedding** — `embedder.py` `BookEmbedder` wraps `AzureOpenAIEmbeddings` (deployment `text-embedding-ada-002`). `embed_chunks` uses `embed_documents` (batch) for ingest; `embed_query` for a single query at serve time. Output is **1536-dim** (`indexer.py EMBEDDING_DIM = 1536`). Same model embeds documents and queries — essential so query and corpus live in one space.

**(c) Indexing** — `indexer.py` provisions an Azure AI Search index (`_ensure_index_exists`) with a `content_vector` field (`Collection(Single)`, `vector_search_dimensions=1536`) backed by an **HNSW** algorithm config + vector-search profile. Metadata fields are typed and `filterable`/`facetable` (`genre`, `year`) and `searchable` (`title`, `author`, `chunk_text`, `description`) — this is what enables hybrid + filtered retrieval. Docs are upserted via `upload_documents` with per-result success accounting.

**(d) Retrieval** — `search.py` `hybrid_search` issues a single Azure AI Search call combining `search_text=query` (keyword/BM25) and a `VectorizedQuery(vector=query_embedding, fields="content_vector", k_nearest_neighbors=top_k)` — true **hybrid** retrieval fused server-side. It `select`s only the fields the downstream needs and returns `@search.score`. The pipeline deliberately **over-retrieves**: `pipeline.py` calls `hybrid_search(top_k=top_k*3)` to give the reranker a wide pool.

**(e) Reranking** — `reranker.py` `rerank_results` loads a lazily-cached `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")`, builds `(query, chunk_text or description)` pairs, scores them jointly, sorts descending, and keeps `top_k`, stamping each survivor with `rerank_score`. This is the precision stage that bi-encoder vector search cannot provide on its own.

**(f) Prompt / context engineering** — `pipeline.py RECOMMENDATION_PROMPT` injects the query and a numbered candidate block (`title by author — description[:200]...`) and asks `gpt-4o` (temperature `0.3`) for a JSON list of `{title, author, reason, score}`, instructed to focus on "thematic alignment, narrative tone, emotional resonance." Robustness engineering in the code: the parser strips ```` ```json ```` / ```` ``` ```` fences, and on any JSON failure **falls back** to returning the reranked list with rerank scores and a generic reason — so the API never hard-fails on a malformed LLM response.

## 5. Model selection rationale

| Stage | Real component (from code) | Why |
|---|---|---|
| Embeddings | Azure OpenAI **`text-embedding-ada-002`** (1536-dim) | Managed, no GPU to host, strong general-purpose semantic quality, batched ingest via `embed_documents`. Azure deployment keeps data in-tenant. |
| Vector store | **Azure AI Search** (HNSW + hybrid) | Gives vector ANN *and* BM25 *and* metadata filtering in one managed service — avoids stitching a separate vector DB to a keyword engine. HNSW for low-latency ANN. |
| Reranker | **`cross-encoder/ms-marco-MiniLM-L-6-v2`** (sentence-transformers) | Small, fast cross-encoder; MS-MARCO-trained for passage relevance. Reads (query, passage) jointly → much better precision than cosine similarity, cheap enough to run on the over-retrieved shortlist. |
| Explanation LLM | Azure OpenAI **`gpt-4o`** (temp 0.3) | Only used to write rationales, not to rank, so quality matters more than cost-per-call; low temperature for stable, on-topic JSON. |

**Why a reranker on top of vector search.** A bi-encoder (ada-002) encodes query and document *independently*, so similarity is a coarse dot product — great for recall, mediocre for fine ordering, and prone to topic-matching while missing tone. The cross-encoder re-reads each candidate *conditioned on the query*, which is where "post-war Europe, melancholy, memory" gets separated from "WWII action thriller." The standard pattern — **cheap high-recall first stage → expensive high-precision rerank on a small pool** — is exactly what `top_k*3` over-retrieve + `rerank_results(top_k)` implements.

**Cost / latency / quality trade-offs.** Embeddings and Azure AI Search are the per-query network cost; the cross-encoder is local CPU (lazy-loaded singleton, first call pays model load). The `gpt-4o` generation call is the dominant latency and dollar cost on the hot path — which is why ranking is *already settled* before the LLM is invoked: if you dropped the LLM, you would still have correctly ordered results, just without prose reasons.

## 6. Training process → Prompt iteration / fine-tuning (or why not)

**No model is trained.** Every model is pretrained and used as-is: ada-002 (frozen embeddings), the MS-MARCO cross-encoder (frozen), gpt-4o (frozen). This is the right call here:

- **Embeddings/reranker are general semantic tasks** — book-synopsis matching is in-distribution for web-trained embeddings and an MS-MARCO reranker; the marginal gain from fine-tuning rarely justifies building a labeled training set and an MLOps retraining loop for a catalog this size.
- **Fine-tuning would freeze the catalog into weights** — books change; embeddings + an index let you ingest new titles by re-running `indexer.py`, no retraining.

**What we iterate instead (the real "training loop"):**
- **Chunk size / overlap** (`chunk_size`, `overlap` in `chunker.py`) — tune against retrieval metrics.
- **Over-retrieve factor** (`top_k*3` in `pipeline.py`) — bigger pool = better rerank recall, more cross-encoder cost.
- **`similarity_threshold = 0.72`** (`config.py`) — a configured coverage cutoff to suppress weak matches (the README's "embedding coverage" metric); note it is defined but not yet enforced inside `hybrid_search`, so wiring/tuning it is open work.
- **Prompt** — the explanation prompt and temperature (`0.3`) are iterated for JSON reliability and rationale quality; the markdown-fence stripping and fallback path are direct artifacts of that iteration.

## 7. Evaluation metrics

The code declares intent (`README` Evaluation Strategy) but ships no eval harness, so targets below are labeled illustrative.

**Retrieval quality (the part that actually determines recommendations):**
- **Hit-rate@k / Recall@k** — fraction of golden queries whose correct book appears in top-k. Measure *after* aggregating chunks → book. *Illustrative target: Recall@10 ≥ 0.85.*
- **MRR** — mean reciprocal rank of the first correct book; sensitive to whether rerank pushes the right title to position 1. *Illustrative target: MRR ≥ 0.55.*
- **nDCG@k** — needs the graded 0–3 judgments from §3; the right metric because the product is an *ordered* short list, not a set. *Illustrative target: nDCG@10 ≥ 0.70.*

**Ablation that matters:** measure all three *with and without* the cross-encoder to quantify what the reranker buys — the whole architecture rests on the claim that it improves precision over raw vector order.

**Recommendation / generation quality:**
- **LLM-as-judge relevance** — `gpt-4o` scores each returned recommendation's reason 0–5 for semantic fit (README). *Illustrative target: mean ≥ 4.0/5.*
- **Explanation faithfulness** — does the `reason` reflect the actual synopsis, not hallucinate plot? Judge against the candidate text the LLM was given.
- **JSON validity rate** — how often the LLM returns parseable JSON vs. triggers the fallback path; a direct, code-grounded operational metric. *Illustrative target: ≥ 98%.*
- **Latency** — track via the existing `X-Process-Time` response header (`main.py` middleware), split into embed / search / rerank / generate. *Illustrative target: p95 < 2.5s.*

## 8. Deployment architecture

**Ingestion (offline, `indexer.py` as a CLI):**
```
sample_books.csv → normalize cols → sentence_aware_chunking (512/64)
  → BookEmbedder.embed_chunks (ada-002, 1536-d) → upload_documents → Azure AI Search (HNSW index)
```

**Serving (online, FastAPI in `main.py`):**
```
POST /recommend {query, top_k, filters?}
  → embed query (ada-002, aembed_query)
  → hybrid_search(top_k*3)  [Azure AI Search: vector + keyword]
  → rerank_results(top_k)   [cross-encoder/ms-marco-MiniLM-L-6-v2]
  → gpt-4o explanation (temp 0.3) → parse/​fallback
  → RecommendationResponse {query, recommendations[]}
```

**Infra & operational details from the code/README:**
- FastAPI app, CORS open, `/health` probe, `X-Process-Time` timing header, port 8002 (`main.py`).
- Async hot path: `aembed_query` and async `SearchClient` (`search.py`) for concurrency; the cross-encoder is a sync singleton (`reranker.py`) lazily loaded once per process.
- Config via `pydantic-settings` from `.env` (`config.py`): Azure OpenAI endpoint/key/api-version (`2024-12-01-preview`), deployments (`gpt-4o`, `text-embedding-ada-002`), Azure AI Search endpoint/key/index (`books-index`).
- Target deploy is **Azure Container Apps** with infra as **Bicep** (`infra/*.bicep`), image built via ACR (README setup).
- Graceful degradation: malformed LLM JSON falls back to reranked results with rerank scores — search/rerank stay authoritative.

## 9. Business impact

*All figures illustrative — no production telemetry in the repo.*

- *Illustrative:* semantic discovery lifts click-through on recommended titles vs. keyword search by **+25–40%**, because results match tone/theme not just topic.
- *Illustrative:* LLM rationales increase add-to-list / conversion by **+10–15%** by giving users a reason to trust the pick.
- *Illustrative:* over-retrieve + rerank improves top-3 precision enough to cut "nothing relevant" sessions by **~30%**.
- **Operational lever (code-grounded, not a number):** because ranking is settled before generation, the `gpt-4o` call can be made optional / cached per (query, candidate-set) to control cost without degrading *which* books are shown.

## 10. Lessons learned

- **"Sentence-aware" is aspirational in the current code.** `sentence_aware_chunking` is a word-window splitter; for synopses with multiple themes, true sentence/semantic chunking (spaCy/NLTK, as the docstring admits) would improve retrieval granularity. Naming should match behavior.
- **Chunk-level docs need book-level aggregation.** One book → many index rows means recall@k and de-duplication must collapse chunks to titles, or metrics and the user-facing list show duplicates.
- **Reranking is the precision workhorse.** Vector search alone over-weights surface topic; the cross-encoder is what enforces tone/intent. Always A/B with-vs-without it.
- **Wire the threshold you configured.** `similarity_threshold=0.72` exists in config but isn't enforced in `hybrid_search`; configured-but-unused knobs are a trap — either enforce coverage filtering or remove the setting.
- **Make the LLM the swappable last stage.** The fallback path proves the design value: search + rerank produce a correct ordered list independently, so the LLM is for *explanation*, and degrading it never breaks recommendations.
- **Hybrid > pure vector for this domain.** Authors, exact titles, and genre words benefit from the keyword arm; `search_text` + `vector_queries` in one call is cheaper and better than running two retrievers and fusing yourself.

## Likely follow-up questions

1. **Your reranker scores `chunk_text`, but the LLM sees `description[:200]` — could rank and explanation disagree?** Yes; rerank operates on the embedded chunk while the prompt truncates the full description — align them or pass the reranked chunk to the LLM to avoid a rationale that doesn't match what won the ranking.
2. **One book becomes multiple chunk documents — how do you avoid duplicate or chunk-inflated results?** Aggregate to book-level (max/mean rerank score per title) before returning and before computing recall@k; the current code does not dedupe.
3. **`similarity_threshold=0.72` is set but never applied — what would you do with it?** Enforce it as a coverage filter in `hybrid_search`/rerank to drop weak matches and return fewer-but-confident results, or drop the setting; measure impact on precision vs. empty-result rate.
4. **Why ada-002 and not a newer/larger embedding model (e.g., text-embedding-3-large)?** It's the deployed choice; 3-large offers higher quality and dimension flexibility — I'd benchmark it on the golden set against latency/cost before swapping, since the index dim (1536) and store are model-coupled.
5. **The cross-encoder is a sync singleton on the async path — does it block the event loop?** Yes, `predict` is CPU-bound and synchronous; under load I'd offload it to a thread pool / `run_in_executor` or a separate inference service so it doesn't stall concurrent requests.
6. **How do you keep the index fresh as the catalog grows?** Re-run `indexer.py` for new/changed titles (upsert by `id`); no retraining needed since models are frozen — that's the payoff of pretrained-embeddings + index over fine-tuning.
7. **How would you evaluate this end-to-end before shipping?** Build the golden + graded eval set (§3), report Recall@k / MRR / nDCG@k with the chunk→book aggregation, ablate the reranker, and add LLM-as-judge + JSON-validity for the generation stage.
8. **What's your failure mode if Azure OpenAI generation is down or slow?** The code already falls back to reranked results with generic reasons; I'd also add a timeout on the `gpt-4o` call and serve the rerank-only response rather than block the request.

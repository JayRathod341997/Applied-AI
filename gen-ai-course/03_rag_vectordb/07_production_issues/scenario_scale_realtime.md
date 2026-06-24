# Scenario: Real-Time RAG at Scale (1M+ Documents)

## Introduction

The previous documents covered issues, debugging, and generic system design. This
document walks through **one concrete, end-to-end scenario** that ties those ideas
together: you are asked to ingest **1 million documents**, keep the knowledge base
**fresh in near real time**, serve **low-latency inference**, **tune the index** for
better recall, and use **metadata** to sharpen retrieval.

Use this as a reference design and an interview narrative — most "design a RAG system
at scale" questions are variations of the scenario below.

---

## 1. The Scenario

> **Company:** "AtlasDesk", a B2B customer-support platform.
> **Ask:** Build a RAG assistant over the full knowledge corpus of every tenant.
>
> | Dimension            | Number / Constraint                                  |
> |----------------------|------------------------------------------------------|
> | Initial corpus       | **1,000,000 documents** (≈ 8–12M chunks)             |
> | Document types       | PDFs, HTML help articles, Slack threads, tickets     |
> | Ingestion deadline   | Full backfill in **< 24 h**                          |
> | Freshness            | New/updated docs searchable in **< 60 s** (near RT)  |
> | Query volume         | 300 QPS peak, 50 QPS average                         |
> | Latency SLA          | **p95 end-to-end < 1.5 s**, retrieval < 150 ms       |
> | Multi-tenancy        | Strict tenant isolation, per-tenant filtering        |
> | Budget               | Cost-aware: embeddings + vector DB + LLM             |

These four requirements pull in different directions — **scale**, **freshness**,
**latency**, and **quality** — and the design is mostly about balancing them.

```
        QUALITY  ◄───────────────────►  LATENCY
            ▲                              ▲
            │      every knob you turn     │
            │      trades one axis for     │
            │            another           │
            ▼                              ▼
        FRESHNESS ◄──────────────────►  COST/SCALE
```

**How to read this diagram:** the four corners are the competing goals, and the arrows
mean "improving one usually costs you another." There is no single configuration that
maximizes all four — every design decision is a deliberate trade. A few concrete examples
of the tension:

- **Quality ↔ Latency:** adding a cross-encoder reranker raises answer quality but adds
  100+ ms per query. Raising `ef_search`/`nprobe` (see §3) improves recall but slows the
  search.
- **Freshness ↔ Cost/Scale:** updating the index within 60 s of every change means running
  a streaming pipeline 24/7; a cheaper nightly batch re-index would make answers stale.
- **Scale ↔ Quality:** to fit 10M vectors in memory you may compress them (quantization),
  which slightly lowers recall.
- **Latency ↔ Cost:** caching and bigger machines cut latency but raise the bill.

The job of a senior engineer is not to "win" all four — it is to know *which* axis the
business cares about most and spend the others to buy it. For AtlasDesk the hard
constraints are the **latency SLA** and **tenant isolation**; freshness and cost get
tuned around them.

---

## 2. Ingesting 1M Documents

### 2.1 Two ingestion paths

A common mistake is to build a single ingestion job and reuse it for everything. At scale
you actually need **two** pipelines because the two jobs have opposite priorities:

- The **backfill** is a *one-time, high-throughput* job. It cares about getting 1M documents
  in as fast and cheaply as possible. Latency per document is irrelevant — total wall-clock
  is what matters. This is a classic batch/MapReduce workload (Spark, Ray, or simple
  multiprocessing) optimized for throughput.
- The **streaming** path is a *continuous, low-latency* job. It cares that a single new or
  edited document becomes searchable within 60 s. Throughput is tiny (a trickle of events),
  but the per-event latency matters a lot.

Crucially, both share the **same core logic** — `chunk → embed → upsert`. Only the
*driver* differs (a bulk reader vs. a queue consumer). Sharing that core keeps results
identical no matter how a document arrived.

```
                 ┌──────────────────────────────────────────────┐
   1M docs ────► │  BATCH BACKFILL (one-time / periodic)         │
   (S3 dump)     │  Spark / Ray / multiprocessing → bulk upsert  │
                 └───────────────────────┬──────────────────────┘
                                         │  shared
                 ┌───────────────────────┴──────────────────────┐
   doc created ► │  STREAMING (continuous, near real time)       │
   /updated      │  CDC / queue → worker → upsert (< 60 s)       │
   (Kafka/SQS)   └──────────────────────────────────────────────┘
```

In the diagram, the top box is the bulk loader fed from a data dump (e.g. an S3 export),
and the bottom box is the live path fed from a change stream. The word *shared* between
them marks the common chunk→embed→upsert engine both call into.

### 2.2 The ingestion stages

Every document — whether it arrives via backfill or streaming — flows through the same
seven stages. The top row is the happy path; the labels under each stage name the one
thing that stage must get right at scale:

```
 Source ─► Load ─► Clean ─► Chunk ─► Embed (batch) ─► Upsert ─► Verify
   │         │       │        │          │              │         │
 dedup    parse   strip    semantic   batch API     bulk write  count +
 by hash  tables  boiler-  + overlap  (256/req)     w/ retries  sample
                  plate                                          recall
```

- **Source / Load:** pull the raw bytes and parse them into text. PDFs and HTML need real
  parsers (tables, layout), not naive text extraction — bad parsing here silently poisons
  everything downstream.
- **Clean:** strip boilerplate (nav bars, footers, signatures). Noise wastes tokens and
  dilutes embeddings, lowering retrieval precision.
- **Chunk:** split into retrievable units with overlap so a concept isn't cut in half. The
  chunk is the *atomic unit of retrieval*, so chunk quality caps retrieval quality.
- **Embed:** convert each chunk to a vector. Done in **batches** (see §2.3) because this is
  the throughput bottleneck of the whole pipeline.
- **Upsert:** write `(id, vector, metadata)` to the store in **bulk, with retries**.
- **Verify:** after the job, count what landed and sample-check recall on a few known
  queries — a silent 5% drop in ingested chunks is otherwise invisible.

The small labels (`dedup by hash`, `batch API`, `count + sample recall`) are the
reliability/throughput safeguards that turn a demo script into a production pipeline.

### 2.3 Make the backfill fast (and cheap)

The backfill is dominated by **embedding throughput**, not the vector DB. Key levers:

```python
import asyncio, hashlib
from itertools import islice

def batched(iterable, n):
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch

async def embed_corpus(chunks, embedder, store, concurrency=16):
    """Backfill 8-12M chunks. Bottleneck = embedding API throughput."""
    sem = asyncio.Semaphore(concurrency)

    async def handle(batch):
        async with sem:
            # 1) Batch the API call — 256-512 texts per request, not 1
            vectors = await embedder.aembed_batch([c.text for c in batch])
            # 2) Bulk upsert — never one-by-one
            await store.upsert([
                (c.id, v, c.metadata) for c, v in zip(batch, vectors)
            ])

    await asyncio.gather(*[handle(b) for b in batched(chunks, 256)])
```

| Lever                      | Why it matters at 1M docs                                  |
|----------------------------|------------------------------------------------------------|
| **Batch embeddings**       | 256–512 texts/request cuts API round-trips ~100×           |
| **Deduplicate by hash**    | `sha256(text)` skips re-embedding identical chunks         |
| **Bulk upsert**            | One call per N vectors; one-by-one writes kill throughput   |
| **Parallel workers**       | Spark/Ray/`multiprocessing`; embeddings are CPU/IO-bound    |
| **Idempotent IDs**         | `tenant:doc:chunk` so retries don't duplicate              |
| **Defer index build**      | Bulk-load first, build/optimize the index after (see §3.4) |
| **Checkpoint progress**    | Resume a failed 24 h job from the last committed offset     |

> **Rule of thumb:** 10M chunks at 256/request ≈ 40k requests. The vector store can
> absorb this easily; your embedding rate limit is the real ceiling — request a quota
> bump or run an embedding model on your own GPUs for the backfill.

---

## 3. Modifying the Index for Better Search

### Why an index at all?

Similarity search means "find the *k* vectors closest to my query vector." The naive way
— a **flat index** — compares the query against *every* stored vector and sorts. That is
mathematically exact but **O(N)** per query: at 10M vectors it means 10M distance
computations *per request*, which blows the latency budget instantly. Flat search is fine
for a few thousand vectors and a disaster at millions.

The fix is an **ANN (Approximate Nearest Neighbor)** index. The word *approximate* is the
key trade: ANN gives up the guarantee of finding the *exact* top-k in exchange for being
orders of magnitude faster. Instead of scanning everything, it pre-organizes the vectors
(into a graph or into clusters) so a query only has to look at a small, promising slice of
the data. You measure how much you gave up with **recall@k** — the fraction of the true
top-k that the approximate search actually returned. Good ANN configs hit 95–99% recall at
a fraction of the cost.

There are two dominant ANN families, and choosing between them is your first index
decision:

```
  HNSW (graph)                       IVF / IVF-PQ (clustering + quantization)
  ───────────────                    ────────────────────────────────────────
  • Best recall/latency              • Lower memory (PQ compresses vectors)
  • High RAM (full vectors)          • Great for very large / on-disk indexes
  • Default for < ~50M vectors       • Default for 100M+ or memory-constrained
```

- **HNSW (Hierarchical Navigable Small World)** builds a multi-layer *graph* where each
  vector links to its nearest neighbors. A query "walks" the graph greedily — hop to the
  closest neighbor, repeat — converging on the answer in a handful of hops instead of a
  full scan. It gives the **best recall-vs-latency** of any common index, but it must keep
  the full vectors in **RAM**, so memory is the limit. This is the right default for our
  10M-vector scenario.
- **IVF (Inverted File) / IVF-PQ** first *clusters* all vectors into `nlist` buckets
  (think k-means). A query only searches the few buckets nearest to it (`nprobe` of them),
  skipping the rest. **PQ (Product Quantization)** additionally *compresses* each vector
  into a few bytes, slashing memory. This family scales to **hundreds of millions** of
  vectors or fits memory-constrained hosts, at the cost of slightly lower recall.

The mental model: **HNSW navigates a graph; IVF narrows to a few clusters.** Both avoid
the full scan — they just take different routes there.

### 3.1 HNSW parameters — what each knob does

To tune HNSW you only need to understand three parameters. Two are set **once at build
time** (`m`, `ef_construction`) and bake the graph's quality into the structure; one is
set **per query** (`ef_search`) and can be changed live. Intuitively, `m` is *how densely
connected* the graph is, and the two `ef_*` values are *how widely you look around* while
building or searching it.

```python
# Pinecone / Qdrant / Weaviate / pgvector all expose these (names vary)
hnsw_config = {
    "m": 16,                 # edges per node. ↑ = better recall, ↑ memory
    "ef_construction": 200,  # build-time search breadth. ↑ = better graph, slower build
    "ef_search": 100,        # query-time breadth. ↑ = better recall, ↑ latency
}
```

| Param            | ↑ raises          | ↑ costs            | Tune when…                          |
|------------------|-------------------|--------------------|-------------------------------------|
| `m`              | recall            | memory, build time | recall too low after other tuning   |
| `ef_construction`| graph quality     | build time (once)  | building a fresh/optimized index    |
| `ef_search`      | recall            | **query latency**  | per-query recall vs. latency dial   |

> `ef_search` is the **live recall↔latency dial** — raise it for hard queries, lower it
> to defend the latency SLA under load. It needs no reindex.

### 3.2 IVF-PQ for very large / memory-bound indexes

```python
# FAISS-style: cluster into nlist buckets, search nprobe of them, compress with PQ
index = faiss.index_factory(dim, "IVF4096,PQ64")
index.train(sample_vectors)     # learn 4096 centroids from a representative sample
index.nprobe = 32               # query-time: search 32/4096 cells (recall↔latency dial)
```

- **`nlist`** ≈ `sqrt(N)`–`4*sqrt(N)` cells (e.g. ~4096 for ~10M vectors).
- **`nprobe`** is the live recall↔latency dial (like `ef_search`).
- **PQ** compresses each vector (e.g. 1536 floats → 64 bytes), trading a little recall
  for **~24× less memory** — the difference between fitting in RAM or not.

### 3.3 Sharding & multi-tenancy at scale

A single index has limits — RAM, write throughput, and blast radius (one corrupt index
takes everyone down). **Sharding** splits the vectors across several smaller indexes. Two
problems get solved at once: the system scales horizontally (add shards, add capacity),
and with multi-tenant data each tenant can live in its own shard/namespace for **hard
isolation**.

The query pattern is **scatter-gather**: a router decides which shard(s) a query touches,
the search runs there, and the partial top-k lists are merged into a final top-k. The
diagram below shows a query tagged `tenant=acme` being routed to the relevant shard(s),
then results gathered back:

```
        ┌──────────────────── Query (tenant=acme) ────────────────────┐
        ▼                                                              │
  ┌───────────┐   tenant routing / namespace                          │
  │  Router   │──────────────┬───────────────┬───────────────┐        │
  └───────────┘              ▼               ▼               ▼        │
                       ┌──────────┐    ┌──────────┐    ┌──────────┐    │
                       │ Shard 1  │    │ Shard 2  │    │ Shard N  │    │
                       │ (vectors │    │          │    │          │    │
                       │  + meta) │    │          │    │          │    │
                       └──────────┘    └──────────┘    └──────────┘    │
        scatter ──► search each shard ──► gather & merge top-k ────────┘
```

The big win of routing by tenant is that it **prunes the search space**: a query for
`acme` is sent only to acme's shard and never even looks at `globex` vectors. That makes
the search both *safer* (isolation) and *faster* (less data to scan) at the same time —
one of the rare moves that improves two axes of the §1 trade-off at once.

- **Namespaces/partitions** (Pinecone namespaces, Qdrant collections/shard keys) are the
  built-in mechanism for this in managed vector DBs — you usually don't hand-roll the
  router.
- **How to choose a shard key:** shard *by tenant* when tenants are large and few (each
  gets its own shard); shard *by hash* when you have many small tenants (spread them
  evenly so no shard becomes a hotspot).

### 3.4 Reindexing without downtime (blue-green)

Sooner or later you will change something fundamental: a better embedding model, a
different vector dimension, or new HNSW parameters. These changes are **incompatible with
the existing vectors** — you cannot mix vectors from two different embedding models in one
index, because their geometry is different and distances become meaningless. So you must
rebuild. The danger is doing it *in place* on the live index: during a rebuild the index
is half-old/half-new and serves garbage, or is offline entirely.

The safe pattern is **blue-green** (a.k.a. shadow indexing): keep the old index serving
while you build the new one beside it, validate the new one, then atomically switch
traffic by repointing an **alias** (a stable name that queries target). If the new index
underperforms, you flip the alias back — instant rollback.

```
  v1 index (serving)  ◄──── alias: "prod" ────  queries
        │
        │  build v2 in background (new model / new HNSW m / new dim)
        ▼
  v2 index (warming) ──► shadow-eval recall ──► repoint alias ──► drop v1
```

Reading the diagram top to bottom: `v1` keeps answering live queries via the `prod` alias;
meanwhile `v2` is built in the background; you **shadow-evaluate** its recall on a held-out
query set to confirm it's at least as good; only then do you repoint the alias to `v2` and
retire `v1`. Users never see downtime or degraded results.

---

## 4. Metadata Strategies for Better Retrieval

### What metadata is and why it matters

Pure vector search answers one question: *"which chunks are semantically closest to this
query?"* But real retrieval needs more: *which chunks is this user allowed to see, which
are still current, which belong to the product they asked about, which are most popular.*
That extra structured information — stored alongside each vector as key/value pairs — is
**metadata** (often called the *payload*). Each stored item is really a triple:
`(id, vector, metadata)`.

Metadata is the **cheapest, highest-leverage** way to improve retrieval because it doesn't
require a better embedding model or more compute — it just adds structure you already have.
It upgrades a single blunt "nearest vectors" lookup into a **filtered, ranked, and
contextual** search:

- **Filtered** — narrow the candidates *before* similarity even runs (only this tenant,
  only active docs).
- **Ranked** — break ties and reorder using signals embeddings don't capture (recency,
  popularity).
- **Contextual** — use positional metadata to reassemble surrounding text so the LLM gets
  a complete passage, not a fragment.

The catch: you can only filter and rank on metadata you **captured at ingestion time**.
Retrofitting a missing field means re-indexing 10M chunks. So design the schema **up
front**.

### 4.1 Design a metadata schema up front

The schema below groups fields by *purpose* — filtering, lifecycle, ranking, quality. Each
group maps directly to one of the retrieval strategies in §4.2, so think of the schema as
"the data I must store now to unlock those strategies later":

```python
chunk_metadata = {
    # ── Filtering (pre-filter the ANN search space) ──
    "tenant_id":   "acme",            # hard isolation — ALWAYS filtered
    "doc_type":    "help_article",    # pdf | ticket | slack | article
    "product":     "billing",
    "language":    "en",
    "acl_groups":  ["support", "admin"],   # security/row-level access

    # ── Recency / lifecycle ──
    "created_at":  1718900000,        # epoch — enables time decay & freshness
    "updated_at":  1718986400,
    "is_active":   True,              # soft-delete without re-indexing

    # ── Ranking / context signals ──
    "source_url":  "https://help.acme.com/billing/refunds",
    "title":       "How refunds work",
    "section":     "Refund timelines",   # heading path for context
    "chunk_index": 3,                    # rebuild neighbor context on read

    # ── Quality signals ──
    "view_count":  1820,              # popularity boost
    "confidence":  0.92,              # extraction quality
}
```

### 4.2 Five ways metadata improves retrieval

| Strategy                 | What it does                                              | Example                                              |
|--------------------------|----------------------------------------------------------|------------------------------------------------------|
| **1. Pre-filtering**     | Restrict ANN search to a subset → faster *and* more relevant | `tenant_id == "acme" AND is_active == True`          |
| **2. Security filtering**| Enforce row-level access at query time                   | `acl_groups CONTAINS user.group`                     |
| **3. Recency boosting**  | Blend similarity with freshness so stale docs sink       | `score = sim − λ·age` (time decay)                   |
| **4. Hybrid + payload**  | Combine vector score with metadata facets / popularity   | rerank by `0.7·sim + 0.2·views + 0.1·recency`        |
| **5. Context expansion** | Use `chunk_index`/`section` to refetch neighbors         | pull chunks `n−1, n, n+1` for a complete answer      |

### 4.3 Pre-filtering vs. post-filtering (a real trap)

There are two moments at which you can apply a metadata filter, and the difference is the
source of a classic production bug. **Pre-filtering** applies the filter *first*, so the
ANN search only ever considers matching vectors — it returns the true top-k *within that
subset*. **Post-filtering** does the opposite: it runs the search over *everything*, gets
the global top-k, and *then* discards the ones that don't match the filter in your
application code.

Post-filtering breaks at scale because the filter throws away results *after* the count is
fixed. If you ask for top-10 and 9 of them belong to other tenants, you're left with 1 —
even though the user's tenant had plenty of good matches that never made the global top-10.
That's the dreaded "it returns almost nothing for some tenants" bug.

```
  PRE-FILTER (filter THEN search)          POST-FILTER (search THEN filter)
  ──────────────────────────────           ─────────────────────────────────
  ✓ correct top-k within the subset        ✗ may return < k after filtering
  ✓ faster (smaller search space)          ✗ wasted compute on discarded hits
  ✓ what you almost always want            ✗ "empty results" bug at scale
  needs a filterable/indexed payload       happens when you filter in app code
```

> **Production lesson:** filter **inside** the vector DB on an **indexed** metadata field.
> Filtering in application code *after* retrieval is the #1 cause of "it returns nothing
> for some tenants" — you asked for top-10, got 10 global hits, then threw 9 away.

### 4.4 Index your metadata fields

Metadata filtering is only fast if the field is indexed. Most vector DBs need this
declared (it is not automatic):

```python
# Qdrant example — make tenant_id and doc_type fast to filter
client.create_payload_index("chunks", "tenant_id", field_schema="keyword")
client.create_payload_index("chunks", "created_at", field_schema="integer")
client.create_payload_index("chunks", "is_active", field_schema="bool")
```

Without a payload index, a `tenant_id` filter degrades to a full scan — fine at 10k
vectors, fatal at 10M.

---

## 5. The Real-Time Inference Path

Everything so far — ingestion, index tuning, metadata — exists to make *this* path fast and
correct: the live request a user is waiting on. "Real-time" here means the system answers
within an interactive latency budget while the knowledge base keeps changing underneath it.
Three techniques carry most of the weight: **budgeting** the latency so no stage blows the
SLA (§5.1), **caching** so repeated work is never redone (§5.2), and **streaming** so the
user perceives speed even when the LLM is slow (§5.3).

### 5.1 Latency budget (p95 < 1.5 s)

A query is a *chain* of stages, and the user waits for all of them in sequence, so the
end-to-end latency is the **sum** of the parts. The discipline of a **latency budget** is
to allocate a slice of the SLA to each stage up front, then engineer each stage to stay
under its slice. If one stage overruns, another must give — you cannot exceed the total.

> **Why p95, not average?** Averages hide pain. p95 ("95% of requests are faster than
> this") captures the slow tail that users actually complain about — a great average with
> a terrible p99 still means thousands of frustrated requests at 300 QPS. Always budget and
> alert on a percentile, not the mean.

The table reads as: each row is a stage, *Budget* is the time it's allowed, and *How to
defend it* is the lever that keeps it there. The rows sum to the 1.5 s SLA:

```
  ┌─────────────┬────────┬───────────────────────────────────────────┐
  │ Stage       │ Budget │ How to defend it                          │
  ├─────────────┼────────┼───────────────────────────────────────────┤
  │ Embed query │  40 ms │ small/fast model, cache hot queries       │
  │ Vector search│ 150 ms│ pre-filter, tuned ef_search/nprobe, shards│
  │ Rerank      │ 120 ms │ cross-encoder on top-20 → top-5 only      │
  │ LLM generate│ 900 ms │ stream tokens; smaller model when simple  │
  │ Overhead    │ 290 ms │ network, serialization, guardrails        │
  ├─────────────┼────────┼───────────────────────────────────────────┤
  │ TOTAL p95   │ 1.5 s  │                                           │
  └─────────────┴────────┴───────────────────────────────────────────┘
```

Notice the **LLM generation dominates** (900 of 1500 ms). That's typical — and it's why
§5.3 (streaming) matters so much: you can't make the LLM finish faster, but you can start
showing its output almost immediately.

### 5.2 Cache aggressively (3 layers)

The cheapest query is the one you never compute. In a support assistant the same handful
of questions ("how do I reset my password?") are asked thousands of times, so caching has a
huge payoff. The trick is that there are **three different things worth caching**, arranged
cheapest-first: the diagram is a *fall-through ladder* — try the fastest cache, and only on
a miss drop to the next, finally falling all the way to the full pipeline (which then
populates every layer above it).

```
  Query ─► [1] Exact-match cache (Redis, normalized query+filters)
              │ miss
              ▼
           [2] Semantic cache (embed query, ANN over past Q&A, sim > 0.95)
              │ miss
              ▼
           [3] Embedding cache (skip re-embedding identical queries)
              │ miss
              ▼
           Full RAG pipeline ─► populate all caches
```

- **[1] Exact-match** is a plain key→value lookup on the normalized query (+ its filters).
  Sub-millisecond, but only hits when the wording is *identical*. Filters must be part of
  the key, or you'll serve one tenant's answer to another.
- **[2] Semantic cache** catches *paraphrases* — "reset password" vs. "I forgot my
  password." It embeds the query and does a tiny ANN search over previously answered
  questions; a similarity above a high threshold (~0.95) is treated as the same question.
  Set the threshold too low and you'll return confidently wrong cached answers.
- **[3] Embedding cache** doesn't skip the whole pipeline — it just avoids re-embedding a
  query string you've embedded before, saving the §5.1 "embed query" budget.

A note of caution: caches and **freshness** (§6) are in tension. When a document changes,
stale cached answers must be invalidated — usually by a short TTL plus event-driven
eviction keyed on the affected docs.

### 5.3 Streaming response

Stream LLM tokens so **perceived** latency ≈ time-to-first-token (~300 ms), even when
full generation takes ~900 ms. This single change does more for UX than most retrieval
tuning.

```python
async def answer(query, ctx):
    docs = await retriever.retrieve(query, filters={"tenant_id": ctx.tenant})
    async for token in llm.astream(build_prompt(query, docs)):
        yield token          # first token in ~300 ms; user starts reading immediately
```

---

## 6. Keeping the Index Fresh (< 60 s)

The backfill (§2) gets you a snapshot, but the source data keeps changing — articles are
edited, tickets are closed, docs are deleted. **Freshness is forever.** The naive approach
is to periodically re-crawl and re-index everything, but at 1M documents a nightly crawl is
slow, expensive, and still leaves answers up to 24 h stale.

The production answer is **Change Data Capture (CDC)**: instead of polling for "what
changed?", you *subscribe to the change events themselves*. A tool like Debezium tails the
source database's transaction log and emits a message for every insert/update/delete onto a
queue (Kafka). An ingest worker consumes those events and updates *only the affected
chunks* — so a single edited document is re-embedded and searchable in seconds, not after a
full re-crawl.

```
  App DB ──CDC (Debezium)──► Kafka ──► Ingest worker ──► chunk+embed+UPSERT
   write                       │                              │
   /update/delete              │                              ▼
                               │                         Vector DB
                               └── delete event ──► soft-delete (is_active=False)
                                                    or hard delete by id
```

The diagram traces one write in the app database flowing as an event through Kafka to the
worker, which re-runs the shared chunk→embed→upsert core and writes to the vector DB.
Delete events branch off to remove (or soft-delete) the corresponding vectors. Each event
type needs slightly different handling:

| Event       | Action                                                                 |
|-------------|------------------------------------------------------------------------|
| **Create**  | chunk → embed → upsert with fresh metadata                             |
| **Update**  | re-chunk → re-embed → **upsert by deterministic id** (overwrites)      |
| **Delete**  | hard-delete by id, or `is_active=False` for instant, reversible hiding |

> **Why upsert, not delete+insert:** deterministic ids (`tenant:doc:chunk`) make updates
> idempotent and atomic — no window where the old and new versions both appear, and
> retries are safe.

---

## 7. Monitoring This System

| Metric                          | Why you watch it at scale                       |
|---------------------------------|-------------------------------------------------|
| Ingestion lag (event→searchable)| Is the < 60 s freshness SLA holding?            |
| Retrieval p95 latency           | Index degradation, hot shards, missing filters  |
| Recall@k (offline eval set)     | Did an index/model change quietly hurt quality? |
| Cache hit rate (per layer)      | Cost + latency; a drop signals a query-mix shift|
| Empty-result rate per tenant    | Classic post-filtering / ACL bug signal         |
| Cost / 1k queries               | Embedding + vector + LLM spend trending up?     |

---

## 8. Design Checklist & Interview Takeaways

When you get *"design a real-time RAG over 1M+ documents,"* hit these points in order:

- [ ] **Two pipelines:** batch backfill **and** streaming/CDC for freshness.
- [ ] **Backfill bottleneck is embeddings** — batch requests, dedup, bulk upsert, parallelize.
- [ ] **ANN index, not flat:** HNSW (≤ ~50M, best recall) or IVF-PQ (100M+ / memory-bound).
- [ ] **`ef_search`/`nprobe` is your live recall↔latency dial** — no reindex needed.
- [ ] **Namespaces/shards** for tenant isolation + search-space pruning.
- [ ] **Reindex blue-green** behind an alias; never mutate the live index in place.
- [ ] **Metadata is the cheapest quality win:** pre-filter, ACL-filter, recency-boost, hybrid-rank.
- [ ] **Pre-filter inside the DB on indexed payload fields**, never post-filter in app code.
- [ ] **Budget the latency** per stage; **cache** in 3 layers; **stream** tokens.
- [ ] **Upsert by deterministic id** for atomic, idempotent updates; soft-delete for instant hide.
- [ ] **Monitor** ingestion lag, recall@k, p95, cache hit rate, empty-result rate, $/query.

---

## Next Steps

- [Common Production Issues](./common_issues.md) — the failure modes this design avoids
- [System Design for Production](./system_design.md) — the generic architecture this specializes
- [Debugging Techniques](./debugging_techniques.md) — diagnosing the issues above
- [Advanced RAG Pipeline](../09_advanced_rag_pipeline/) — hybrid search & ingestion in code

# Module 3: RAG & Vector Databases — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level)
- [Intermediate Level](#intermediate-level)
- [Advanced Level](#advanced-level)

---

## Beginner Level

### Q1: What is Retrieval-Augmented Generation (RAG)?

**Answer:** RAG is an architecture pattern that enhances LLMs by retrieving relevant external knowledge before generating responses. Instead of relying solely on the model's training data, RAG dynamically fetches context from a knowledge base to ground the model's output in factual, up-to-date information.

**Core flow:**
```
User Query -> Embed Query -> Search Vector DB -> Retrieve Top-K Chunks -> Augment Prompt -> LLM Generates Answer
```

**Why RAG matters:**
- Eliminates knowledge cutoff limitations
- Reduces hallucinations by grounding responses in source documents
- Enables source attribution and citation
- Allows knowledge updates without model retraining

---

### Q2: What are the core components of a RAG pipeline?

**Answer:** A RAG pipeline consists of five core components:

1. **Document Ingestion:** Loading and preprocessing source documents (PDFs, web pages, databases)
2. **Chunking:** Splitting documents into smaller, manageable pieces
3. **Embedding:** Converting text chunks into dense vector representations
4. **Vector Store:** Indexing and storing embeddings for fast similarity search
5. **Retrieval + Generation:** Querying the vector store, retrieving relevant chunks, and passing them to the LLM as context

```python
# Simplified RAG pipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

# 1. Load and chunk documents
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(document_text)

# 2. Create embeddings and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_texts(chunks, embedding=embeddings)

# 3. Retrieve and generate
retrieved_docs = vectorstore.similarity_search("What is RAG?", k=3)
context = "\n".join([doc.page_content for doc in retrieved_docs])
response = ChatOpenAI().invoke(f"Context: {context}\nQuestion: What is RAG?")
```

---

### Q3: What are embeddings and why are they important for RAG?

**Answer:** Embeddings are dense vector representations of text that capture semantic meaning. Similar texts produce vectors that are close together in the embedding space, enabling semantic search beyond simple keyword matching.

**Key properties:**
- **Dimensionality:** Typically 384 to 3072 dimensions
- **Semantic capture:** "dog" and "puppy" are close; "dog" and "airplane" are far
- **Fixed-size:** Any text length maps to the same vector size

```python
from openai import OpenAI

client = OpenAI()
response = client.embeddings.create(
    input="Machine learning is a subset of artificial intelligence",
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding  # 1536-dimensional vector
```

**Why important:** Without embeddings, retrieval would rely on exact keyword matching, missing semantically relevant documents that use different wording.

---

### Q4: What is cosine similarity and how is it used in vector search?

**Answer:** Cosine similarity measures the cosine of the angle between two vectors, producing a score from -1 to 1. It is the most common distance metric for text embeddings because it captures directional similarity regardless of vector magnitude.

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Two similar sentences
vec1 = get_embedding("The cat sat on the mat")
vec2 = get_embedding("A feline rested on the rug")
similarity = cosine_similarity(vec1, vec2)  # High score (~0.85-0.95)

# Dissimilar sentences
vec3 = get_embedding("Python programming tutorial")
similarity2 = cosine_similarity(vec1, vec3)  # Low score (~0.1-0.3)
```

**Other distance metrics:**
- **L2 (Euclidean):** Straight-line distance between vectors
- **Dot product:** Similar to cosine but sensitive to magnitude
- **Manhattan:** Sum of absolute differences

---

### Q5: What is chunking and why is it necessary?

**Answer:** Chunking is the process of splitting large documents into smaller pieces before embedding and indexing. It is necessary because:

1. **Embedding model limits:** Models have max token limits (512-8192 tokens)
2. **Retrieval precision:** Smaller chunks provide more focused, relevant context
3. **Context window management:** LLMs have limited context windows; you need granular chunks to fit top-k results

**Common strategies:**
- **Fixed-size:** Split every N characters with overlap
- **Recursive:** Split on natural boundaries (paragraphs, sentences)
- **Semantic:** Split based on meaning changes

```python
# Fixed-size chunking
def chunk_text(text, size=500, overlap=50):
    return [text[i:i+size] for i in range(0, len(text), size - overlap)]

# Recursive chunking (LangChain)
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_text(document)
```

---

### Q6: What is a vector database and how does it differ from a traditional database?

**Answer:** A vector database is a specialized data store optimized for indexing, storing, and querying high-dimensional vector embeddings using similarity search.

| Aspect | Traditional DB | Vector DB |
|--------|---------------|-----------|
| **Data type** | Structured rows/columns | High-dimensional vectors |
| **Query** | Exact match (SQL) | Similarity search (nearest neighbors) |
| **Index** | B-tree, hash index | HNSW, IVF, PQ |
| **Use case** | CRUD operations | Semantic search, recommendations |

**Popular vector databases:**
- **Pinecone:** Managed cloud service, production-ready
- **Chroma:** Local-first, great for prototyping
- **Weaviate:** Open-source, hybrid search support
- **FAISS:** Meta's library for similarity search (not a full database)
- **Milvus:** Open-source, designed for billions of vectors

---

### Q7: What is the difference between dense and sparse retrieval?

**Answer:**

| Aspect | Dense Retrieval | Sparse Retrieval |
|--------|----------------|-----------------|
| **Representation** | Dense vectors (embeddings) | Sparse vectors (TF-IDF, BM25) |
| **Semantic understanding** | Yes (captures meaning) | No (keyword matching) |
| **Out-of-vocabulary** | Handles synonyms | Fails on unseen terms |
| **Speed** | Fast with ANN indexes | Very fast with inverted indexes |
| **Best for** | Semantic search | Exact keyword matching |

**Dense retrieval** uses embedding models to encode queries and documents into dense vectors, then finds nearest neighbors. It captures semantic meaning but misses exact keyword matches.

**Sparse retrieval** (BM25, TF-IDF) uses term frequency statistics. It excels at exact keyword matching but misses semantic similarity.

**Hybrid search** combines both using reciprocal rank fusion (RRF) for best results.

---

### Q8: What is the top-k parameter in retrieval?

**Answer:** The top-k parameter specifies how many of the most similar documents to return from the vector database. A query embedding is compared against all stored embeddings, and the k documents with the highest similarity scores are returned.

```python
# Retrieve top 5 most similar chunks
results = vectorstore.similarity_search(query, k=5)

# With scores for filtering
results = vectorstore.similarity_search_with_relevance_scores(query, k=5)
# Returns [(doc, score), ...] - filter by score threshold
filtered = [(doc, score) for doc, score in results if score > 0.7]
```

**Choosing k:**
- **k=3-5:** Focused, precise answers
- **k=10-20:** Broader context, risk of noise
- **Dynamic k:** Retrieve more, then re-rank to select best

---

### Q9: What is the difference between FAISS, Chroma, and Pinecone?

**Answer:**

| Feature | FAISS | Chroma | Pinecone |
|---------|-------|--------|----------|
| **Type** | Library | Database | Managed service |
| **Deployment** | Local (in-process) | Local/cloud | Cloud only |
| **Scalability** | RAM-limited | Millions | Billions |
| **Metadata filtering** | Limited | Yes | Yes |
| **Hybrid search** | No | Yes | Yes |
| **Setup complexity** | Medium | Low | Low |
| **Cost** | Free | Free | Paid |
| **Best for** | Research, large-scale local | Prototyping, small apps | Production |

```python
# FAISS
import faiss
index = faiss.IndexFlatL2(1536)
index.add(embeddings)

# Chroma
import chromadb
client = chromadb.PersistentClient(path="./db")
collection = client.create_collection("docs")
collection.add(documents=["text"], ids=["id1"])

# Pinecone
from pinecone import Pinecone
pc = Pinecone(api_key="...")
index = pc.Index("my-index")
index.upsert(vectors=[{"id": "1", "values": embedding}])
```

---

### Q10: How do you evaluate a basic RAG system?

**Answer:** RAG evaluation assesses both the retrieval and generation components:

**Retrieval metrics:**
- **Precision@k:** Fraction of retrieved documents that are relevant
- **Recall@k:** Fraction of all relevant documents that were retrieved
- **MRR:** Average reciprocal rank of the first relevant result
- **NDCG:** Normalized discounted cumulative gain (position-aware relevance)

**Generation metrics:**
- **Faithfulness:** Is the answer supported by retrieved context?
- **Answer relevance:** Does the answer address the question?
- **Context relevance:** Are the retrieved documents on-topic?

```python
# Simple evaluation with RAGAS
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

---

## Intermediate Level

### Q11: Explain the semantic chunking approach and its advantages.

**Answer:** Semantic chunking uses embeddings to determine natural split points based on meaning rather than arbitrary character counts. It computes embeddings for consecutive sentences and splits where semantic similarity drops below a threshold.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

def semantic_chunk(text: str) -> list[str]:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",  # or "standard_deviation", "interquartile"
        breakpoint_threshold_amount=95  # Split at 95th percentile of similarity drops
    )
    return splitter.split_text(text)
```

**Advantages:**
- Produces topically coherent chunks
- No arbitrary size constraints
- Better for question-answering tasks
- Preserves semantic context within chunks

**Disadvantages:**
- Slower (requires embedding computation for split decisions)
- Variable chunk sizes may complicate context window planning
- Higher cost (embedding API calls during ingestion)

**Breakpoint threshold types:**
- **Percentile:** Split at the Nth percentile of similarity drops
- **Standard deviation:** Split when similarity drops by N standard deviations
- **Interquartile:** Uses IQR to detect outliers in similarity scores

---

### Q12: How does HNSW indexing work and why is it popular?

**Answer:** HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest neighbor algorithm. It builds a multi-layer proximity graph where:

- **Layer 0** contains all vectors as nodes, connected to their nearest neighbors
- **Higher layers** contain progressively fewer nodes, acting as express highways
- **Search** starts at the top-layer entry point and greedily navigates toward the query, descending layers until reaching layer 0

```
Layer 2:  A ---------> D              (few nodes, long-range connections)
Layer 1:  A ---> C ---> D ---> F     (more nodes)
Layer 0:  A -> B -> C -> D -> E -> F -> G  (all vectors, local connections)
```

**Parameters:**
- **M:** Maximum connections per node (higher = better recall, more memory)
- **ef_construction:** Search width during index build (higher = better quality, slower build)
- **ef_search:** Search width during queries (higher = better recall, slower search)

**Why popular:**
- O(log n) search time
- High recall (>95%) with proper tuning
- Well-supported in FAISS, Weaviate, Qdrant, pgvector

```python
import faiss

# HNSW index in FAISS
dimension = 1536
index = faiss.IndexHNSWFlat(dimension, 32)  # M=32
index.hnsw.efConstruction = 200  # Build quality
index.hnsw.efSearch = 128  # Search quality
index.add(vectors)
```

---

### Q13: What is hybrid search and how do you implement it?

**Answer:** Hybrid search combines dense vector search (semantic similarity) with sparse keyword search (BM25) to capture both meaning and exact term matching. Results are merged using Reciprocal Rank Fusion (RRF).

**RRF formula:**
```
RRF_score(d) = 1 / (k + rank_i(d))
```
where k is a constant (typically 60) and rank_i(d) is the rank of document d in system i.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS

# Sparse retriever (BM25)
bm25_retriever = BM25Retriever.from_documents(documents, k=10)

# Dense retriever (vector similarity)
vectorstore = FAISS.from_documents(documents, embeddings)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Hybrid: combine with RRF
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, dense_retriever],
    weights=[0.4, 0.6]  # 40% BM25, 60% dense
)

results = hybrid_retriever.invoke("What is retrieval augmented generation?")
```

**When hybrid search excels:**
- Queries with specific entity names, IDs, or technical terms
- Documents with domain-specific jargon
- When both semantic understanding and exact matching matter

---

### Q14: What is re-ranking and when should you use it?

**Answer:** Re-ranking is a two-stage retrieval approach where an initial retrieval (fast, approximate) is followed by a more accurate scoring step using a cross-encoder model.

**Stage 1 — Bi-encoder (fast):** Encode query and documents independently, compute similarity.
**Stage 2 — Cross-encoder (accurate):** Process query-document pairs jointly for fine-grained relevance scoring.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

# Initial retrieval: get 20 candidates
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

# Re-rank to top 5
reranker = CohereRerank(model="rerank-english-v3.0", top_n=5)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=base_retriever
)

results = compression_retriever.invoke("How do vector databases scale?")
```

**When to use re-ranking:**
- High-stakes applications where precision matters
- When initial retrieval returns many candidates
- When compute budget allows for the extra latency (~100-300ms)

**Trade-off:** Cross-encoders are 10-100x slower than bi-encoders but significantly more accurate.

---

### Q15: Explain the "lost in the middle" problem and mitigation strategies.

**Answer:** Research (Liu et al., 2024) shows that LLMs perform best when relevant information is at the beginning or end of the context, with degraded performance when it is in the middle.

**Mitigation strategies:**

1. **Re-ranking:** Place the most relevant document first
2. **Reduce context:** Use fewer, higher-quality chunks
3. **Query decomposition:** Break complex queries into sub-queries
4. **Structured context:** Use XML tags to delineate documents

```python
# Mitigation: place best match first
def prepare_context(docs_with_scores):
    # Sort by relevance score descending
    sorted_docs = sorted(docs_with_scores, key=lambda x: x[1], reverse=True)
    # Most relevant doc goes first
    context_parts = []
    for i, (doc, score) in enumerate(sorted_docs):
        context_parts.append(f"<document id={i}>\n{doc.page_content}\n</document>")
    return "\n\n".join(context_parts)
```

---

### Q16: What is query transformation and what techniques exist?

**Answer:** Query transformation rewrites or expands the user's query to improve retrieval quality. Raw user queries are often vague, ambiguous, or poorly formatted for semantic search.

**Techniques:**

1. **Multi-query expansion:** Generate multiple reformulations
2. **HyDE (Hypothetical Document Embeddings):** Generate a hypothetical answer, embed it, and use it for retrieval
3. **Step-back prompting:** Ask a more general question first

```python
# Multi-query expansion
from langchain.retrievers import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=ChatOpenAI(model="gpt-4o-mini")
)

# HyDE implementation
def hyde_retrieve(query, vectorstore, llm):
    # Generate hypothetical answer
    hypothetical = llm.invoke(
        f"Write a passage that answers: {query}"
    ).content
    
    # Embed the hypothetical answer and search
    results = vectorstore.similarity_search_by_vector(
        embeddings.embed_query(hypothetical),
        k=5
    )
    return results
```

---

### Q17: How do you handle metadata filtering in vector databases?

**Answer:** Metadata filtering combines vector similarity search with structured attribute filters. This narrows results to documents matching specific criteria (source, date, author, category) while preserving semantic relevance.

```python
# Chroma with metadata filtering
results = collection.query(
    query_texts=["machine learning basics"],
    n_results=5,
    where={"source": "textbook.pdf"},  # Exact match
    where_document={"$contains": "neural network"}  # Content filter
)

# Pinecone with metadata filtering
results = index.query(
    vector=query_embedding,
    top_k=5,
    filter={
        "category": {"$eq": "machine-learning"},
        "date": {"$gte": "2024-01-01"},
        "source": {"$in": ["textbook.pdf", "lecture_notes.pdf"]}
    },
    include_metadata=True
)

# LangChain with self-query retriever (auto-generates filters from natural language)
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever

metadata_info = [
    AttributeInfo(name="source", description="Document source file", type="string"),
    AttributeInfo(name="date", description="Publication date", type="string"),
]
retriever = SelfQueryRetriever.from_llm(
    llm, vectorstore, "Document metadata", metadata_info
)
```

---

### Q18: What is contextual compression in RAG?

**Answer:** Contextual compression extracts only the most relevant portions from retrieved documents, reducing noise and fitting more information into the LLM's context window.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Compress retrieved docs to only relevant sentences
compressor = LLMChainExtractor.from_llm(ChatOpenAI(temperature=0))
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)

# Returns compressed, relevant excerpts instead of full chunks
results = compression_retriever.invoke("What are the types of neural networks?")
```

**Benefits:**
- Reduces token usage and cost
- Removes irrelevant content from retrieved chunks
- Allows more documents to fit in context

---

### Q19: How do you optimize chunk size for different use cases?

**Answer:** Chunk size significantly impacts retrieval quality and must be tuned per use case.

| Use Case | Chunk Size | Overlap | Rationale |
|----------|-----------|---------|-----------|
| **Q&A over articles** | 500 tokens | 50 tokens | Focused answers, minimal noise |
| **Code search** | Function-level | 0 | Code is self-contained |
| **Legal documents** | 1000 tokens | 200 tokens | Complex context dependencies |
| **Conversational** | 300 tokens | 50 tokens | Short, focused responses |
| **Summarization** | 2000 tokens | 300 tokens | Needs broader context |

```python
# Empirical chunk size evaluation
def evaluate_chunk_sizes(documents, query, ground_truth):
    results = {}
    for chunk_size in [200, 500, 1000, 2000]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=int(chunk_size * 0.1)
        )
        chunks = splitter.split_documents(documents)
        vs = Chroma.from_documents(chunks, embeddings)
        
        retrieved = vs.similarity_search(query, k=5)
        relevance = compute_relevance(retrieved, ground_truth)
        results[chunk_size] = relevance
    
    return results
```

**Key insight:** There is no universal best chunk size. Evaluate using your actual queries and ground truth data.

---

### Q20: What are the common failure modes in a RAG pipeline?

**Answer:**

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| **Missing content** | Answer not in the knowledge base | Better ingestion, coverage analysis |
| **Wrong retrieval** | Relevant docs exist but are not retrieved | Hybrid search, query transformation |
| **Lost in middle** | Relevant doc retrieved but ignored by LLM | Re-ranking, better context ordering |
| **Hallucination** | LLM adds info not in context | Faithfulness checking, strict prompts |
| **Stale data** | Outdated information retrieved | Incremental indexing, freshness metadata |
| **Chunk boundary** | Answer spans multiple chunks | Overlap, larger chunks, parent-child retrieval |
| **Embedding mismatch** | Query and doc embeddings are semantically distant | Query HyDE, domain-specific embeddings |

```python
# Diagnostic: check each stage
def diagnose_rag(query, pipeline):
    # 1. Check query embedding
    query_emb = embeddings.embed_query(query)
    
    # 2. Check retrieval
    retrieved = vectorstore.similarity_search_with_score(query, k=10)
    print(f"Top score: {retrieved[0][1]:.4f}")  # Low score = retrieval issue
    
    # 3. Check context quality
    context = "\n".join([doc.page_content for doc, _ in retrieved[:5]])
    
    # 4. Check generation with faithfulness
    answer = llm.invoke(f"Context: {context}\nQuestion: {query}")
    faithfulness = check_faithfulness(context, answer)
    print(f"Faithfulness: {faithfulness}")
```

---

## Advanced Level

### Q21: How would you design a production-grade RAG system?

**Answer:** A production RAG system requires careful architecture across ingestion, retrieval, generation, and monitoring.

```
+------------------------------------------------------------------+
|                   Production RAG Architecture                     |
+------------------------------------------------------------------+
|                                                                    |
|  Ingestion Pipeline          Retrieval Pipeline                    |
|  +----------+   +--------+   +----------+   +----------+          |
|  | Document |-->| Chunk  |   |  Query   |-->|  Query   |          |
|  | Loaders  |   | Engine |   |  Input   |   | Transform|          |
|  +----------+   +---+----+   +----------+   +----+-----+          |
|                     |                              |               |
|               +-----+-----+              +--------+-------+       |
|               | Embedding |              |  Hybrid Search  |       |
|               |  Models   |              |  Dense+Sparse   |       |
|               +-----+-----+              +--------+-------+       |
|                     |                              |               |
|               +-----+--------------+        +-----+------+        |
|               |   Vector Store     |        |  Re-ranker |        |
|               | (Pinecone/Milvus)  |        +-----+------+        |
|               +--------------------+              |               |
|                                              +----+-----+         |
|  Monitoring                                   |    LLM   |        |
|  +---------+  +----------+  +----------+     | Generator|        |
|  | Logging |  | Metrics  |  | Alerting |     +----+-----+        |
|  +---------+  +----------+  +----------+          |               |
|                                              +----+-----+         |
|                                              | Faithful |         |
|                                              | Checker  |         |
|                                              +----+-----+         |
|                                                   |               |
|                                              +----+-----+         |
|                                              | Response |         |
|                                              +----------+         |
+------------------------------------------------------------------+
```

**Key design decisions:**

```python
# Production RAG configuration
RAG_CONFIG = {
    # Ingestion
    "chunk_size": 512,
    "chunk_overlap": 64,
    "embedding_model": "text-embedding-3-small",
    
    # Retrieval
    "retrieval_strategy": "hybrid",  # dense + sparse
    "top_k_initial": 20,  # Over-retrieve
    "top_k_final": 5,     # After re-ranking
    "reranker": "cohere-rerank-v3",
    "min_relevance_score": 0.7,
    
    # Generation
    "llm": "gpt-4o",
    "temperature": 0.1,
    "max_tokens": 1000,
    "faithfulness_check": True,
    
    # Caching
    "semantic_cache": True,
    "cache_threshold": 0.95,
    
    # Monitoring
    "log_all_queries": True,
    "track_latency": True,
    "track_token_usage": True,
}
```

**Critical production concerns:**
- **Incremental indexing:** Update vector store when documents change
- **Access control:** Metadata filtering for document-level permissions
- **Rate limiting and fallbacks:** Handle API failures gracefully
- **Cost optimization:** Cache results, use smaller models for routing

---

### Q22: Explain advanced indexing strategies and when to use each.

**Answer:**

| Index Type | Algorithm | Search Time | Recall | Memory | Best For |
|-----------|-----------|-------------|--------|--------|----------|
| **Flat (brute-force)** | Exact search | O(n) | 100% | Low | <100K vectors, baselines |
| **IVF Flat** | Inverted file | O(n/k) | 95%+ | Low | 100K-10M vectors |
| **HNSW** | Graph navigation | O(log n) | 99%+ | High | General purpose |
| **IVF PQ** | Inverted + quantization | O(n/k) | 90%+ | Very low | Large scale, memory-constrained |
| **ScaNN** | Anisotropic vector quantization | O(sqrt(n)) | 95%+ | Medium | Google-scale |

```python
import faiss

# IVF: Inverted File Index (partition-based)
nlist = 100  # Number of clusters
quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
index.train(training_vectors)  # Requires training step
index.add(vectors)

# IVF with Product Quantization (memory-efficient)
m = 16  # Number of sub-quantizers
nbits = 8  # Bits per sub-quantizer
index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits)
index.train(training_vectors)
index.add(vectors)

# HNSW with tuned parameters
index = faiss.IndexHNSWFlat(dimension, 32)  # M=32 connections
index.hnsw.efConstruction = 200  # Build quality
index.hnsw.efSearch = 128  # Search quality vs speed
```

**Selection criteria:**
- **<100K vectors:** Flat index (exact, simple)
- **100K-10M, high recall needed:** HNSW
- **10M+ with memory constraints:** IVF-PQ
- **Google-scale:** ScaNN or custom solutions

---

### Q23: How do you implement a faithfulness evaluation pipeline for RAG?

**Answer:** Faithfulness evaluation verifies that generated answers are grounded in the retrieved context and do not contain hallucinations.

```python
from openai import OpenAI

client = OpenAI()

def evaluate_faithfulness(question: str, context: str, answer: str) -> dict:
    """
    Evaluate whether the answer is faithful to the retrieved context.
    Returns claims analysis and faithfulness score.
    """
    prompt = f"""You are a factual consistency evaluator. Analyze whether each claim 
in the answer is supported by the provided context.

Question: {question}

Context:
{context}

Answer:
{answer}

Instructions:
1. Extract each distinct claim from the answer
2. For each claim, determine if it is:
   - SUPPORTED: directly stated or logically inferred from context
   - UNSUPPORTED: not found in context (potential hallucination)
   - CONTRADICTED: contradicts the context
3. Compute a faithfulness score = supported_claims / total_claims

Return JSON:
{{
    "claims": [
        {{"claim": "...", "status": "SUPPORTED|UNSUPPORTED|CONTRADICTED", "evidence": "..."}}
    ],
    "faithfulness_score": 0.0-1.0,
    "verdict": "PASS|FAIL"
}}"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


# Batch evaluation
def evaluate_rag_pipeline(queries: list[dict]) -> dict:
    results = []
    for q in queries:
        # Retrieve
        docs = vectorstore.similarity_search(q["question"], k=5)
        context = "\n\n".join([d.page_content for d in docs])
        
        # Generate
        answer = generate_answer(q["question"], context)
        
        # Evaluate
        faith = evaluate_faithfulness(q["question"], context, answer)
        results.append(faith)
    
    avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)
    pass_rate = sum(1 for r in results if r["verdict"] == "PASS") / len(results)
    
    return {"avg_faithfulness": avg_faithfulness, "pass_rate": pass_rate}
```

**Integration with CI/CD:**
```yaml
# rag-eval.yaml
rag_evaluation:
  threshold:
    faithfulness: 0.90
    answer_relevance: 0.85
    context_precision: 0.80
  fail_on_regression: true
  dataset: eval/rag_test_set.jsonl
```

---

### Q24: How do you handle multi-tenant RAG with access control?

**Answer:** Multi-tenant RAG requires isolating document access per user/organization while sharing the same infrastructure.

```python
# Metadata-based access control
def ingest_with_access_control(documents, tenant_id, access_tags):
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["tenant_id"] = tenant_id
        chunk.metadata["access_tags"] = access_tags
        chunk.metadata["ingestion_time"] = datetime.utcnow().isoformat()
    
    vectorstore.add_documents(chunks)

# Filtered retrieval
def secure_retrieve(query, tenant_id, user_roles):
    results = vectorstore.similarity_search(
        query,
        k=10,
        filter={
            "tenant_id": tenant_id,
            "access_tags": {"$in": user_roles}
        }
    )
    return results

# Namespace isolation (Pinecone)
index = pc.Index("multi-tenant")
index.upsert(
    vectors=[...],
    namespace=f"tenant_{tenant_id}"
)
results = index.query(
    vector=query_embedding,
    top_k=5,
    namespace=f"tenant_{tenant_id}"
)
```

**Architecture patterns:**
1. **Shared index + metadata filtering:** Single index, filter by tenant_id (cost-effective)
2. **Namespace isolation:** Separate namespaces per tenant (Pinecone, Weaviate)
3. **Index per tenant:** Complete isolation (highest security, highest cost)

---

### Q25: How do you implement semantic caching for RAG and what are the trade-offs?

**Answer:** Semantic caching stores query-response pairs and returns cached responses when a new query is semantically similar to a cached query.

```python
import hashlib
from openai import OpenAI

class SemanticCache:
    def __init__(self, embeddings_client, threshold=0.95):
        self.embeddings = embeddings_client
        self.cache = {}  # {hash: {"query": str, "embedding": list, "response": str}}
        self.threshold = threshold
    
    def _cosine_similarity(self, a, b):
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get(self, query: str) -> str | None:
        if not self.cache:
            return None
        
        query_emb = self.embeddings.embed_query(query)
        
        best_score = -1
        best_response = None
        
        for entry in self.cache.values():
            score = self._cosine_similarity(query_emb, entry["embedding"])
            if score > best_score:
                best_score = score
                best_response = entry["response"]
        
        if best_score >= self.threshold:
            return best_response
        return None
    
    def set(self, query: str, response: str):
        key = hashlib.md5(query.encode()).hexdigest()
        embedding = self.embeddings.embed_query(query)
        self.cache[key] = {
            "query": query,
            "embedding": embedding,
            "response": response
        }

# Usage in RAG pipeline
cache = SemanticCache(embeddings, threshold=0.95)

def rag_with_cache(query):
    # Check cache first
    cached = cache.get(query)
    if cached:
        return cached, "cache_hit"
    
    # Full RAG pipeline
    docs = vectorstore.similarity_search(query, k=5)
    context = "\n".join([d.page_content for d in docs])
    response = llm.invoke(f"Context: {context}\nQuestion: {query}").content
    
    # Store in cache
    cache.set(query, response)
    return response, "cache_miss"
```

**Trade-offs:**

| Benefit | Drawback |
|---------|----------|
| 10-100x latency reduction | Cache invalidation complexity |
| Eliminates repeated LLM costs | Stale responses if documents update |
| Reduces API rate limit pressure | Semantic threshold tuning required |
| Simple to implement | Memory grows with unique queries |

---

## Quick Reference Table

| Topic | Key Concepts |
|-------|--------------|
| **RAG Architecture** | Retrieve -> Augment -> Generate, five core components |
| **Embeddings** | Dense vectors, cosine similarity, text-embedding-3-small, BGE, nomic |
| **Chunking** | Fixed-size, recursive, semantic, overlap for context preservation |
| **Vector Databases** | FAISS, Chroma, Pinecone, Weaviate, Milvus, HNSW, IVF |
| **Retrieval** | Dense, sparse, hybrid search, top-k, metadata filtering |
| **Advanced Techniques** | Re-ranking, query transformation, HyDE, contextual compression |
| **Evaluation** | Precision, recall, MRR, faithfulness, answer relevance, RAGAS |
| **Production** | Caching, incremental indexing, multi-tenancy, monitoring, cost control |

---

## Senior Deep Dive: pgvector on Azure Database for PostgreSQL

> *Targeted at roles that standardize on PostgreSQL/Azure as the system of record. Interviewers probe whether you can avoid a separate vector DB and keep vectors next to transactional data.*

### SQ1: When would you choose `pgvector` over a dedicated vector database like Pinecone or Weaviate?

**Answer:** Choose `pgvector` (the PostgreSQL extension that adds a `vector` column type plus ANN indexes) when:

- **You already run PostgreSQL** and want vectors co-located with relational/transactional data — one backup, one access-control model, one connection pool. Critical in regulated/risk domains where data residency and a single audit trail matter.
- **Transactional consistency** is required: an embedding and its source row commit in the same ACID transaction — no dual-write skew between a SQL store and an external index.
- **Scale is moderate** (~1–10M vectors per table comfortably; tens of millions with HNSW + partitioning and tuning).
- **You want to filter then search** using rich SQL `WHERE` clauses (joins, RBAC, tenant_id, date ranges) in the same query.

Choose a dedicated vector DB when you need >100M vectors, sub-10ms p99 at very high QPS, managed sharding/replication for vectors, or built-in hybrid/re-ranking features without building them yourself.

**On Azure:** *Azure Database for PostgreSQL – Flexible Server* supports `pgvector` natively (enable via the `azure.extensions` server parameter). This is the common "no new infra" choice cited in Azure-centric JDs — pair it with Azure OpenAI embeddings.

### SQ2: Walk through setting up and querying pgvector on Azure PostgreSQL.

**Answer:**

```sql
-- 1. Enable the extension (must also be allow-listed in Azure server parameter azure.extensions)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Table with an embedding column (dim must match the embedding model, e.g. 1536 for text-embedding-3-small)
CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL,
    content     TEXT,
    metadata    JSONB,
    embedding   VECTOR(1536)
);

-- 3. Approximate index — HNSW for best recall/latency (preferred over IVFFlat for most workloads)
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 4. Filtered ANN query: metadata filter + vector similarity in ONE statement
SELECT id, content, 1 - (embedding <=> $1) AS cosine_similarity
FROM documents
WHERE tenant_id = $2
  AND metadata->>'doc_type' = 'policy'
ORDER BY embedding <=> $1      -- <=> cosine distance; <-> L2; <#> inner product
LIMIT 5;
```

**Key operators:** `<=>` cosine distance, `<->` Euclidean (L2), `<#>` negative inner product. Match the operator class on the index (`vector_cosine_ops`) to the distance you query with, or the index won't be used.

### SQ3: HNSW vs IVFFlat in pgvector — how do you choose and tune?

**Answer:**

| Aspect | HNSW | IVFFlat |
|--------|------|---------|
| Recall/latency | Higher recall, faster queries | Lower memory, faster build |
| Build cost | Slower, more memory | Fast to build |
| Tuning knobs | `m`, `ef_construction` (build); `ef_search` (query) | `lists` (build); `probes` (query) |
| Best for | Most production RAG | Very large tables where build time/RAM dominates |

- **HNSW query tuning:** `SET hnsw.ef_search = 100;` — higher = better recall, slower. Start ~40–100.
- **IVFFlat:** set `lists ≈ rows / 1000` (up to ~sqrt(rows)); raise `ivfflat.probes` for recall. **Build the IVF index only after data is loaded** — it clusters existing rows.
- Both are *approximate* — validate recall against a brute-force baseline on a sample before committing index params.

### SQ4: How do you implement hybrid (keyword + vector) search in PostgreSQL?

**Answer:** Combine `pgvector` similarity with PostgreSQL full-text search (`tsvector`/`ts_rank`) and fuse the scores — typically Reciprocal Rank Fusion (RRF):

```sql
WITH semantic AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> $1) AS rank
    FROM documents WHERE tenant_id = $2 ORDER BY embedding <=> $1 LIMIT 50
),
keyword AS (
    SELECT id, ROW_NUMBER() OVER (
        ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery($3)) DESC) AS rank
    FROM documents
    WHERE tenant_id = $2 AND to_tsvector('english', content) @@ plainto_tsquery($3)
    LIMIT 50
)
SELECT COALESCE(s.id, k.id) AS id,
       COALESCE(1.0/(60 + s.rank), 0) + COALESCE(1.0/(60 + k.rank), 0) AS rrf_score
FROM semantic s FULL OUTER JOIN keyword k USING (id)
ORDER BY rrf_score DESC LIMIT 10;
```

This catches exact-match terms (IDs, ticker symbols, regulation codes) that pure embeddings miss — valuable in finance/risk where precise terminology matters. For richer BM25, the `pg_search`/ParadeDB extension is an alternative where available.

### SQ5: Production concerns for pgvector at scale (the senior-level answer).

**Answer:**
- **Index memory:** HNSW graphs live in memory for fast search. Size the Azure SKU (memory-optimized tiers) for roughly `rows × dim × 4 bytes × overhead`. Monitor cache hit ratio.
- **Write amplification:** Inserts update the HNSW graph — bulk-load first, then index; or use partitioned tables and reindex partitions.
- **Multi-tenancy:** Filter by `tenant_id`; for hard isolation use partitioning or row-level security (RLS). Note: heavy `WHERE` filtering can degrade ANN recall (post-filtering drops candidates) — over-fetch (`LIMIT 50` then filter to 5) or use partitioned indexes per tenant.
- **Dimensionality:** pgvector indexes support up to 2000 dims; for larger, truncate (Matryoshka) embeddings or use `halfvec` (fp16, ~50% space).
- **HA/DR on Azure:** Flexible Server zone-redundant HA + read replicas; embeddings replicate with the row — no separate vector-store DR plan.
- **Cost vs dedicated DB:** No extra service, but you pay in DB CPU/RAM and operational tuning — the trade-off the interviewer wants articulated.

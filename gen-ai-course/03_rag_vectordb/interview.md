# RAG & Vector Databases - Interview Questions

This document contains interview questions and answers covering all topics from Module 3: RAG & Vector Databases.

---

## 1. RAG Overview

### Q1: What is RAG (Retrieval-Augmented Generation)?

**Answer:** RAG is an architectural pattern that combines the strengths of retrieval systems with generative AI. It works by:

1. **Retrieving** relevant information from a knowledge base
2. **Augmenting** the prompt with retrieved context
3. **Generating** responses using an LLM informed by the retrieved content

This approach reduces hallucinations, provides grounding for responses, and enables LLMs to access up-to-date or domain-specific information without retraining.

---

### Q2: What are the core components of RAG?

**Answer:** Core components include:

- **Document Loader:** Reads documents from various sources (PDF, HTML, databases)
- **Text Splitter:** Divides documents into manageable chunks
- **Embedding Model:** Converts text into vector representations
- **Vector Database:** Stores and indexes embeddings for fast retrieval
- **Retriever:** Finds relevant documents based on query
- **Generator:** Produces final output using retrieved context

---

### Q3: What are common use cases for RAG?

**Answer:** Common use cases include:

- **Enterprise Knowledge Base:** Q&A over internal documents
- **Customer Support:** Answering product-related questions
- **Legal Research:** Searching case law and regulations
- **Healthcare:** Medical literature and guidelines
- **Financial Analysis:** Reports and market data
- **Codebase Assistance:** Documentation and code search

---

### Q4: Explain the RAG architecture flow.

**Answer:** RAG architecture flow:

1. **Ingestion Phase:**
   - Load documents → Split into chunks → Generate embeddings → Store in vector DB

2. **Query Phase:**
   - Receive user query → Generate query embedding → Retrieve similar chunks → Combine with prompt → Generate response

---

## 2. Embeddings and Chunking

### Q5: What are embeddings in the context of RAG?

**Answer:** Embeddings are dense vector representations of text that capture semantic meaning. They transform textual data into numerical vectors where similar concepts are positioned close together in vector space. Popular embedding models include:

- **Dense:** BERT-based (sentence-transformers), OpenAI text-embedding-ada-002
- **Sparse:** BM25, TF-IDF (for hybrid search)

---

### Q6: What is semantic search and how does it work?

**Answer:** Semantic search understands meaning rather than just keyword matching. It works by:

1. Converting query into an embedding vector
2. Finding vectors in the database with highest similarity (cosine, dot product)
3. Returning results based on semantic similarity rather than exact matches

---

### Q7: What are different chunking strategies?

**Answer:** Chunking strategies include:

- **Fixed Size:** Simple but may break semantic units
- **By Sentences:** Preserves complete sentences
- **By Paragraphs:** Maintains topical coherence
- **Recursive Splitting:** Multiple levels of granularity
- **Semantic:** Split at natural topic boundaries
- **Markdown/HTML Aware:** Respects document structure

---

### Q8: How do you determine optimal chunk size?

**Answer:** Considerations include:

- **Context Window:** Must fit with query and prompt
- **Overlap:** Some overlap helps maintain context
- **Content Type:** Code vs prose vs mixed
- **Retrieval Quality:** Test different sizes
- **Balance:** Smaller = more precise, larger = more context

---

### Q9: What is the difference between dense and sparse embeddings?

**Answer:**

| Feature | Dense | Sparse |
|---------|-------|--------|
| Dimensions | Few (768-4096) | Many (50k+ vocab) |
| Storage | More efficient | Larger |
| Semantic | Excellent | Limited |
| Keyword | Moderate | Excellent |
| Use Case | Semantic search | Exact matching |

---

## 3. Vector Databases

### Q10: What is a vector database?

**Answer:** A vector database is specialized for storing and querying high-dimensional vector embeddings. Key features:

- **Indexing:** Enables fast similarity search (HNSW, IVF, PQ)
- **Metadata Filtering:** Filter by non-vector attributes
- **Scalability:** Handles millions/billions of vectors
- **Distance Metrics:** Cosine, euclidean, dot product

Popular options: Pinecone, Weaviate, Chroma, pgvector, Milvus

---

### Q11: What are the different types of vector database indexes?

**Answer:** Common indexing algorithms:

- **HNSW (Hierarchical Navigable Small World):** Graph-based, high recall, memory-intensive
- **IVF (Inverted File):** Clustering-based, good balance
- **PQ (Product Quantization):** Compressed storage, faster search
- **LSH (Locality-Sensitive Hashing):** Hash-based, approximate

---

### Q12: How do you upload data into a vector database?

**Answer:** Upload process:

1. **Prepare Documents:** Load and clean source data
2. **Generate Chunks:** Split into appropriate sizes
3. **Create Embeddings:** Run through embedding model
4. **Add Metadata:** Include source, timestamp, etc.
5. **Upsert to Database:** Insert/update vectors with IDs
6. **Verify:** Query to confirm successful indexing

---

### Q13: What are distance metrics used in vector search?

**Answer:** Common metrics:

- **Cosine Similarity:** Angle between vectors (recommended for text)
- **Euclidean Distance:** Straight-line distance
- **Dot Product:** Raw product (for normalized vectors)

---

### Q14: How do you visualize embedding spaces for debugging?

**Answer:** Visualization techniques:

- **PCA:** Reduce to 2-3 dimensions for plotting
- **t-SNE:** Better cluster preservation
- **UMAP:** Faster, preserves global structure
- **TensorFlow Projector:** Interactive visualization tool
- **Scatter Plots:** Color by category, examine clusters

---

## 4. RAG Implementation

### Q15: How do you query a vector database and generate answers?

**Answer:** Query process:

1. **Generate Query Embedding:** Transform user question to vector
2. **Search Vector DB:** Find top-k similar chunks
3. **Fetch Context:** Retrieve original text chunks
4. **Construct Prompt:** Add context to system prompt
5. **Generate Response:** Call LLM with augmented prompt

---

### Q16: What is the Retrieval & Generation Loop?

**Answer:** The loop involves:

1. **Query** → Embed → Retrieve
2. **Evaluate** retrieved context quality
3. **If poor:** Reformulate query, expand context, or use hybrid search
4. **Generate** initial response
5. **If hallucinations:** Add citations, rerank, or refine prompt
6. **Return** final response to user

---

### Q17: What are hybrid search techniques?

**Answer:** Hybrid search combines:

- **Dense Retrieval:** Semantic similarity (embeddings)
- **Sparse Retrieval:** Keyword matching (BM25)

Implementation:
- **Reciprocal Rank Fusion (RRF):** Combine ranked lists
- **Learning to Rank:** Train a model to combine scores
- **Query Expansion:** Use LLM to expand queries

---

## 5. Retrieval Techniques

### Q18: What is Top-k retrieval and filtering?

**Answer:** Top-k retrieves the k most similar results. Filtering applies before or after:

- **Pre-filtering:** Apply metadata filters before vector search
- **Post-filtering:** Filter after retrieving results

Best practice: Use pre-filtering for efficiency

---

### Q19: What is Metadata Filtering?

**Answer:** Metadata filtering restricts results based on non-vector attributes:

- Date ranges
- Document type
- Author/source
- Tags or categories
- Access levels

Example: "Find similar to X but only from 2024"

---

### Q20: What are retrieval challenges and mitigation techniques?

**Answer:** Challenges and solutions:

| Challenge | Mitigation |
|-----------|------------|
| Semantic mismatch | Query expansion, re-ranking |
| Missing context | Increase chunk overlap |
| Irrelevant results | Metadata filtering |
| Too much context | Chunk size tuning |
| Slow retrieval | Index optimization |

---

## 6. RAG Evaluation

### Q21: How do you evaluate retrieval quality?

**Answer:** Intrinsic evaluation metrics:

- **Recall@k:** What % of relevant docs retrieved
- **Precision@k:** What % of retrieved docs are relevant
- **MAP (Mean Average Precision):** Ranking quality
- **MRR (Mean Reciprocal Rank):** First relevant result position
- **NDCG:** Normalized discounted cumulative gain

---

### Q22: How do you evaluate end-to-end QA quality?

**Answer:** Extrinsic evaluation methods:

- **Exact Match:** Does response exactly match reference?
- **F1 Score:** Precision and recall of answer components
- **ROUGE:** Overlap with reference summaries
- **BLEU:** N-gram overlap with references
- **LLM-as-Judge:** Use LLM to rate quality

---

### Q23: What is LLM-as-a-Judge technique?

**Answer:** LLM-as-a-Judge uses an LLM to evaluate responses:

1. Define evaluation criteria (helpfulness, accuracy, relevance)
2. Prompt LLM to score responses
3. Aggregate scores across test cases
4. Use for A/B testing and improvement

Benefits: Scalable, captures nuanced quality
Limitations: Potential bias, expensive

---

## 7. Production Issues

### Q24: What are common production issues in RAG systems?

**Answer:** Common issues:

- **Retrieval Failures:** No relevant results returned
- **Context Overflow:** Too much context exceeds token limits
- **Latency:** Slow retrieval or generation
- **Quality Degradation:** Declining answer quality over time
- **Index Staleness:** Outdated knowledge base
- **Hallucinations:** Grounding failures

---

### Q25: How do you debug RAG retrieval issues?

**Answer:** Debugging approach:

1. **Inspect Retrieved Chunks:** Are they relevant?
2. **Check Similarity Scores:** Are matches strong enough?
3. **Test Query Embedding:** Is query well-formed?
4. **Review Chunking:** Are chunks coherent?
5. **Verify Index:** Is data properly indexed?
6. **Analyze Failure Cases:** Look for patterns

---

### Q26: How do you handle index updates and data refresh?

**Answer:** Update strategies:

- **Full Re-index:** Rebuild entire index (simpler, expensive)
- **Incremental Updates:** Add new documents, update changed
- **Embedding Versioning:** Track which embedding model used
- **Version Switching:** A/B test new vs old indexes
- **Refresh Scheduling:** Regular updates based on data change rate

---

## Technical Deep-Dive Questions

### Q27: What is the difference between exact match and semantic search?

**Answer:**

| Aspect | Exact Match | Semantic Search |
|--------|-------------|-----------------|
| Understanding | Keyword literal | Meaning |
| Synonyms | No | Yes |
| Typos | Sensitive | Tolerant |
| Speed | Fast | Slower |
| Use Case | Code, exact terms | Natural language |

---

### Q28: How does RAG help reduce hallucinations?

**Answer:** RAG reduces hallucinations by:

1. **Grounding:** Providing factual context to LLM
2. **Attribution:** Citing sources for claims
3. **Verification:** Can check retrieved context
4. **Limited Scope:** Constrained to provided context
5. **Confidence Scoring:** Based on retrieval quality

---

### Q29: What is reranking and when would you use it?

**Answer:** Reranking improves initial retrieval results:

1. **Initial Retrieve:** Fast vector search (top-100)
2. **Rerank:** More expensive model (cross-encoder) on smaller set
3. **Final Output:** Return top-10 after reranking

Use when:
- Initial recall is good but precision needs improvement
- Need better relevance scoring
- Combining multiple retrieval sources

---

### Q30: How do you handle multi-hop reasoning in RAG?

**Answer:** Multi-hop strategies:

- **Iterative RAG:** Multiple retrieval-generation cycles
- **Graph-based:** Track entity relationships
- **Decomposition:** Break complex questions into sub-questions
- **Chain-of-Thought:** Prompt LLM to reason step-by-step

---

## Production-Level Questions

### Q31: How would you optimize RAG for low latency?

**Answer:** Optimization strategies:

- **Caching:** Cache frequent queries and embeddings
- **Async Operations:** Parallelize retrieval and generation
- **Smaller Embeddings:** Use compact models
- **Index Optimization:** Tune HNSW parameters
- **Streaming:** Start responding before full generation
- **Warm Requests:** Pre-compute common embeddings

---

### Q32: How do you implement role-based access in RAG?

**Answer:** RBAC implementation:

1. **Document Level:** Filter by user permissions during retrieval
2. **Chunk Level:** Tag chunks with access levels
3. **Query Level:** Restrict what users can query
4. **Response Level:** Filter sensitive info from outputs

---

### Q33: What monitoring metrics are important for RAG?

**Answer:** Key metrics:

- **Retrieval:** Recall, precision, latency
- **Generation:** Token usage, latency, quality scores
- **System:** Uptime, error rates
- **Business:** User satisfaction, task completion
- **Cost:** Per-query cost, daily spend

---

### Q34: How do you handle embedding drift?

**Answer:** Embedding drift solutions:

1. **Version Tracking:** Record embedding model version
2. **Re-indexing:** Rebuild when model updates
3. **A/B Testing:** Compare old vs new
4. **Backward Compatibility:** Don't change without migration
5. **Monitoring:** Watch for quality degradation

---

## Scenario-Based Questions

### Q35: Your RAG system returns irrelevant results. How would you diagnose and fix it?

**Answer:** Diagnostic steps:

1. **Check Query:** Is the question well-formed?
2. **Inspect Chunks:** Are they semantically relevant?
3. **Review Embeddings:** Is embedding model appropriate?
4. **Analyze Chunking:** Are chunks too large/small?
5. **Test Search:** Try different similarity thresholds

Fixes:
- Adjust chunk size and overlap
- Use better embedding model
- Implement query rewriting
- Add hybrid search
- Apply reranking

---

### Q36: How would you build a QA system over a policy document PDF?

**Answer:** Implementation steps:

1. **Load PDF:** Use PyMuPDF or LangChain loaders
2. **Extract Text:** Get clean text from pages
3. **Chunk:** Use appropriate strategy (page-based with overlap)
4. **Embed:** Generate embeddings with embedding model
5. **Store:** Upsert to vector database with metadata
6. **Query:** Implement RAG pipeline with citations

---

### Q37: How do you handle a vector database with billions of vectors?

**Answer:** Scaling strategies:

- **Sharding:** Distribute across multiple machines
- **Compression:** Use product quantization (PQ)
- **Tiered Storage:** Hot (SSD) vs cold (HDD) storage
- **Index Tuning:** Optimize HNSW parameters
- **Batch Processing:** Bulk uploads with parallel processing
- **Cloud Solutions:** Managed vector DBs (Pinecone, etc.)

---

## Follow-up Questions

### Q38: What is the difference between RAG and Fine-tuning?

**Answer:**

| Aspect | RAG | Fine-tuning |
|--------|-----|--------------|
| Data Needs | No training | Training data required |
| Latency | Higher (retrieval) | Lower (no retrieval) |
| Update | Easy (swap index) | Hard (retrain) |
| Hallucinations | Lower | Can still occur |
| Cost | Query + embedding | Training + inference |
| Use Case | Dynamic knowledge | Specific style/tasks |

---

### Q39: How would you implement citation generation in RAG?

**Answer:** Citation implementation:

1. **Track Sources:** Store document IDs with chunks
2. **Retrieve with IDs:** Get source metadata alongside content
3. **Format Citations:** Add footnotes or links in response
4. **Verify:** Check that citations support claims
5. **Allow Click-through:** Link to source documents

---

### Q40: What are the limitations of RAG?

**Answer:** Limitations include:

- **Retrieval Quality Dependent:** Garbage in, garbage out
- **Latency:** Added overhead from retrieval step
- **Complexity:** More components to maintain
- **Context Limits:** Still bounded by LLM context window
- **Cost:** Both retrieval and generation costs
- **No Learning:** Doesn't improve from user interactions

---

## Summary

Key topics covered:

1. **RAG Fundamentals:** Architecture, components, use cases
2. **Embeddings & Chunking:** Strategies, optimization
3. **Vector Databases:** Indexes, querying, visualization
4. **Retrieval Techniques:** Filtering, hybrid search
5. **Evaluation:** Metrics, LLM-as-Judge
6. **Production:** Debugging, monitoring, optimization

---

## References

- [RAG Implementation Best Practices](references.md)
- [Vector Database Comparisons](references.md)
- [Retrieval Evaluation Metrics](references.md)

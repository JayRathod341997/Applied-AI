# Module 3: RAG & Vector Databases — Quiz

## Instructions
- 25 multiple choice questions
- Each question has one correct answer
- Answers with explanations are provided at the end

---

## Questions

### Q1. What is the primary purpose of Retrieval-Augmented Generation (RAG)?

A) To train LLMs on larger datasets  
B) To reduce model size by removing parameters  
C) To ground LLM responses in external, up-to-date knowledge  
D) To replace fine-tuning entirely  

---

### Q2. Which component of a RAG pipeline converts text into dense vector representations?

A) Tokenizer  
B) Embedding model  
C) Vector database  
D) LLM generator  

---

### Q3. What is the dimensionality of OpenAI's `text-embedding-3-small` output vectors?

A) 512  
B) 768  
C) 1024  
D) 1536  

---

### Q4. Which similarity metric measures the cosine of the angle between two vectors?

A) Euclidean (L2) distance  
B) Dot product  
C) Cosine similarity  
D) Manhattan distance  

---

### Q5. What is the primary purpose of chunk overlap in text splitting?

A) To reduce the total number of chunks  
B) To maintain context across chunk boundaries  
C) To increase embedding quality  
D) To speed up vector search  

---

### Q6. Which chunking strategy splits text based on semantic similarity between sentences?

A) Fixed-size chunking  
B) Recursive character chunking  
C) Semantic chunking  
D) Token-based chunking  

---

### Q7. What type of index does FAISS `IndexFlatL2` use?

A) Approximate nearest neighbor with IVF  
B) Exact brute-force search using L2 distance  
C) Hierarchical navigable small world graphs  
D) Product quantization index  

---

### Q8. Which vector database is best suited for rapid prototyping and local development?

A) Pinecone  
B) Weaviate  
C) Chroma  
D) Milvus  

---

### Q9. In a RAG pipeline, what does the "retrieve" step typically return?

A) The full document corpus  
B) The top-k most similar document chunks  
C) A summary of all documents  
D) The embedding vectors of all documents  

---

### Q10. What is the hybrid search approach in RAG?

A) Combining embeddings with fine-tuning  
B) Combining dense vector search with sparse keyword search (e.g., BM25)  
C) Using multiple LLMs simultaneously  
D) Searching both images and text  

---

### Q11. What is the purpose of re-ranking in a RAG pipeline?

A) To sort documents by date  
B) To re-score and reorder retrieved documents using a cross-encoder for higher relevance  
C) To remove duplicate documents  
D) To compress the document corpus  

---

### Q12. Which metric measures how many of the retrieved documents are actually relevant?

A) Recall  
B) Precision  
C) F1 Score  
D) Latency  

---

### Q13. What does MRR (Mean Reciprocal Rank) evaluate in a retrieval system?

A) The average position of the first relevant result  
B) The total number of relevant results retrieved  
C) The speed of retrieval  
D) The size of the embedding vectors  

---

### Q14. What is the "lost in the middle" problem in RAG?

A) Documents stored in the middle of the vector index are slower to retrieve  
B) LLMs tend to ignore context placed in the middle of long prompts  
C) Chunking loses information from the middle of documents  
D) Vector search returns middle-ranked results as most relevant  

---

### Q15. Which technique helps prevent hallucinations in RAG outputs?

A) Increasing the embedding dimensions  
B) Adding a "groundedness" check that verifies claims against retrieved context  
C) Using smaller chunk sizes  
D) Increasing the number of retrieved documents  

---

### Q16. What is query transformation in the context of advanced RAG?

A) Converting the query to SQL  
B) Rewriting or expanding the user query to improve retrieval quality  
C) Translating the query to another language  
D) Compressing the query to fewer tokens  

---

### Q17. What is the purpose of metadata filtering in vector databases?

A) To increase embedding accuracy  
B) To narrow search results using structured attributes alongside vector similarity  
C) To reduce storage costs  
D) To speed up embedding generation  

---

### Q18. Which embedding model is open-source and optimized for long documents up to 8192 tokens?

A) text-embedding-3-small  
B) BGE-large-en-v1.5  
C) nomic-embed-text  
D) E5-large-v2  

---

### Q19. What is a vector database index type that uses graph-based navigation for approximate nearest neighbor search?

A) IndexFlatL2  
B) IVFFlat  
C) HNSW (Hierarchical Navigable Small World)  
D) PQ (Product Quantization)  

---

### Q20. In RAG evaluation, what does the faithfulness metric measure?

A) How fast the system responds  
B) Whether the generated answer is supported by the retrieved context  
C) Whether all relevant documents were retrieved  
D) The grammatical correctness of the output  

---

### Q21. What is the primary challenge of using cosine similarity with non-normalized embeddings?

A) It produces negative values  
B) It becomes equivalent to dot product and loses direction sensitivity  
C) It requires more compute  
D) It only works with integer vectors  

---

### Q22. Which production challenge is addressed by implementing caching in a RAG system?

A) Embedding model accuracy  
B) High latency and cost for repeated or similar queries  
C) Document chunking quality  
D) Vector index corruption  

---

### Q23. What is the role of a cross-encoder in a RAG pipeline?

A) Generating embeddings for documents  
B) Scoring query-document pairs jointly for more accurate relevance ranking  
C) Encoding the user query only  
D) Compressing vector dimensions  

---

### Q24. Which chunking strategy is most appropriate for documents with mixed content (headings, paragraphs, code)?

A) Fixed-size chunking  
B) Recursive character splitting with format-aware separators  
C) Sentence-level splitting  
D) Character-level splitting  

---

### Q25. What is the recommended approach when your RAG system retrieves relevant documents but the LLM still generates incorrect answers?

A) Increase the number of retrieved documents  
B) Improve the chunking strategy and add prompt engineering with explicit instructions to use only the provided context  
C) Switch to a larger embedding model  
D) Use a different vector database  

---

## Answers and Explanations

### Q1. Answer: C
**Explanation:** RAG grounds LLM responses in external, up-to-date knowledge by retrieving relevant documents before generation. This reduces hallucination, enables source attribution, and keeps responses current without retraining the model.

### Q2. Answer: B
**Explanation:** The embedding model (e.g., OpenAI's text-embedding-3-small, BGE, E5) converts text into dense vector representations that capture semantic meaning. These vectors are then stored in the vector database for similarity search.

### Q3. Answer: D
**Explanation:** OpenAI's `text-embedding-3-small` produces 1536-dimensional vectors. The larger variant `text-embedding-3-large` produces 3072-dimensional vectors. These dimensions are fixed by the model architecture.

### Q4. Answer: C
**Explanation:** Cosine similarity measures the cosine of the angle between two vectors, ranging from -1 (opposite) to 1 (identical direction). It is the most common similarity metric for text embeddings because it focuses on vector direction rather than magnitude.

### Q5. Answer: B
**Explanation:** Chunk overlap ensures that context spanning chunk boundaries is not lost. For example, with a 500-character chunk and 50-character overlap, the last 50 characters of one chunk repeat at the start of the next, preserving continuity.

### Q6. Answer: C
**Explanation:** Semantic chunking uses embeddings to measure similarity between consecutive sentences and splits at points where semantic similarity drops below a threshold. This produces chunks that are topically coherent rather than arbitrarily sized.

### Q7. Answer: B
**Explanation:** `IndexFlatL2` performs exact brute-force search using L2 (Euclidean) distance. It compares the query against every stored vector, guaranteeing exact results but with O(n) search complexity. It is best for small datasets or as a baseline.

### Q8. Answer: C
**Explanation:** Chroma is designed for local development and prototyping. It runs in-process with Python, requires no server setup, and stores data on disk. Pinecone and Weaviate are better suited for production cloud deployments.

### Q9. Answer: B
**Explanation:** The retrieve step uses the query embedding to search the vector database and returns the top-k most similar document chunks (typically k=3 to 10). These chunks are then passed to the LLM as context for answer generation.

### Q10. Answer: B
**Explanation:** Hybrid search combines dense vector search (semantic similarity) with sparse keyword search (BM25, TF-IDF). This captures both semantic meaning and exact keyword matches, improving retrieval quality. Results are typically merged using reciprocal rank fusion (RRF).

### Q11. Answer: B
**Explanation:** Re-ranking uses a cross-encoder model to jointly process each query-document pair and produce a more accurate relevance score than bi-encoder embeddings alone. This reorders the initially retrieved documents to surface the most relevant ones first.

### Q12. Answer: B
**Explanation:** Precision measures the fraction of retrieved documents that are relevant (relevant retrieved / total retrieved). Recall measures the fraction of all relevant documents that were retrieved. Both are important for evaluating retrieval quality.

### Q13. Answer: A
**Explanation:** MRR computes the average of 1/rank across queries, where rank is the position of the first relevant result. Higher MRR means relevant results appear closer to the top. MRR = 1/N x 1/rank_i.

### Q14. Answer: B
**Explanation:** Research shows that LLMs pay more attention to information at the beginning and end of the context window, often ignoring content in the middle. This affects RAG when multiple documents are concatenated — important information in the middle may be overlooked.

### Q15. Answer: B
**Explanation:** A groundedness (or faithfulness) checker verifies that each claim in the generated answer can be traced back to the retrieved context. This post-generation step catches hallucinations where the LLM adds information not present in the source documents.

### Q16. Answer: B
**Explanation:** Query transformation rewrites, expands, or decomposes the user's original query to improve retrieval. Techniques include HyDE (Hypothetical Document Embeddings), multi-query expansion, and step-back prompting. A vague query like "ML stuff" might be transformed into "machine learning algorithms, applications, and best practices."

### Q17. Answer: B
**Explanation:** Metadata filtering combines vector similarity search with structured filters (e.g., `source = "policy.pdf" AND date > "2024-01-01"`). This narrows the search space before or after vector search, improving precision and enabling access control.

### Q18. Answer: C
**Explanation:** Nomic-embed-text supports 8192-token sequences with 768 dimensions, making it suitable for long documents. BGE-large-en-v1.5 and E5-large-v2 are limited to 512 tokens, while text-embedding-3-small supports 8191 tokens but is proprietary.

### Q19. Answer: C
**Explanation:** HNSW builds a multi-layer graph where nodes are connected to their nearest neighbors. Search navigates the graph from a top-layer entry point, progressively moving to finer layers. It offers O(log n) search time with high recall, making it the most popular ANN index.

### Q20. Answer: B
**Explanation:** Faithfulness measures whether the generated answer's claims are supported by the retrieved context. A faithful answer does not add information beyond what the documents contain. This is distinct from answer relevance (whether the answer addresses the question) and context relevance (whether retrieved documents are on-topic).

### Q21. Answer: B
**Explanation:** For normalized vectors (unit length), cosine similarity equals the dot product. If embeddings are not normalized, the dot product conflates magnitude with direction, making cosine similarity less meaningful. Most embedding models output normalized vectors, but it is best practice to verify.

### Q22. Answer: B
**Explanation:** Semantic caching stores responses for previously answered queries (or semantically similar queries). When a new query matches a cached entry above a similarity threshold, the cached response is returned, eliminating embedding and LLM costs and reducing latency from seconds to milliseconds.

### Q23. Answer: B
**Explanation:** A cross-encoder takes the query and document as a single input and outputs a relevance score. Unlike bi-encoders (which encode query and document independently), cross-encoders model fine-grained interactions between query and document tokens, producing more accurate but slower scoring.

### Q24. Answer: B
**Explanation:** Recursive character splitting with format-aware separators (e.g., `"\n\n"`, `"\n"`, `". "`) preserves document structure. It first splits on paragraph boundaries, then sentences, then words, maintaining semantic coherence across mixed content types like headings, paragraphs, and code blocks.

### Q25. Answer: B
**Explanation:** If retrieval is correct but generation is wrong, the issue is in the LLM's use of context. Solutions include: improving prompt instructions ("Answer ONLY based on the provided context"), adding explicit grounding instructions, using chain-of-thought within the context, and potentially switching to a stronger LLM for generation.

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 22-25 | Excellent | Ready for Module 4 |
| 17-21 | Good | Review weak areas before proceeding |
| 12-16 | Fair | Re-read concepts.md and retry |
| Below 12 | Needs Work | Study the module thoroughly before advancing |

---

## Bonus: Senior / JD-Aligned Questions (pgvector on Azure PostgreSQL)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. You already run Azure Database for PostgreSQL and need vector search for ~2M documents co-located with relational metadata. What is the most appropriate choice?

A) Stand up a separate Pinecone cluster and dual-write  
B) Enable the `pgvector` extension and add a `VECTOR` column with an HNSW index  
C) Store embeddings as JSON arrays and compute cosine in application code  
D) Migrate everything to a graph database  

**Answer: B** — `pgvector` keeps vectors next to transactional data with one ACID transaction, one backup, and one access-control model — ideal at this scale and for regulated audit trails. A dedicated DB is justified only at much larger scale / QPS.

### BQ2. In pgvector, which index type generally gives the best recall/latency for production RAG, and which query-time knob trades recall for speed?

A) IVFFlat; `lists`  
B) HNSW; `hnsw.ef_search`  
C) B-tree; `work_mem`  
D) GiST; `probes`  

**Answer: B** — HNSW is preferred for most production RAG; raising `hnsw.ef_search` increases recall at the cost of latency. (IVFFlat uses `lists`/`probes` and must be built after data is loaded.)

### BQ3. Which pgvector operator corresponds to cosine distance, and what must match for the index to be used?

A) `<->`; nothing needs to match  
B) `<#>`; the table must be unlogged  
C) `<=>`; the index operator class (`vector_cosine_ops`) must match the query distance  
D) `=`; the column must be `NOT NULL`  

**Answer: C** — `<=>` is cosine distance; the index's operator class must match the distance you query with or PostgreSQL falls back to a sequential scan.

### BQ4. Heavy `WHERE tenant_id = ...` filtering on an HNSW query returns too few results. What is the standard fix?

A) Drop the HNSW index  
B) Over-fetch (e.g. `LIMIT 50`) then filter to the final top-k, or use per-tenant partitioned indexes  
C) Lower `ef_construction` to 1  
D) Switch the distance metric to Euclidean  

**Answer: B** — post-filtering an approximate search can drop candidates, hurting recall; over-fetch then filter, or isolate tenants with partitioned indexes / RLS.

### BQ5. Which is a genuine trade-off of pgvector vs a dedicated vector database?

A) pgvector cannot do similarity search at all  
B) pgvector adds no operational cost  
C) You avoid a new service, but pay in DB CPU/RAM and tuning, and it's less suited to >100M vectors at very high QPS  
D) Dedicated vector DBs are always cheaper  

**Answer: C** — the senior trade-off: simplicity and consistency vs raw scale/throughput ceilings and added DB resource pressure.

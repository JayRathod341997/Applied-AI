# Module 14: Production AI Projects — Quiz

## Instructions
Choose the best answer for each question. Answers and explanations are provided below each question.

---

## Questions

### Q1: In the Book Recommender architecture, what is the primary advantage of hybrid search over pure vector search?

A) It requires less storage  
B) It combines BM25 keyword matching with vector similarity for better recall  
C) It eliminates the need for embeddings  
D) It is faster for all query types  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Hybrid search combines BM25 (keyword-based) retrieval with vector similarity search. BM25 excels at exact term matching (e.g., specific book titles, author names), while vector search captures semantic similarity. Together they provide better recall than either approach alone.</details>

---

### Q2: Which Azure service provides both vector search and semantic ranking in a single managed service?

A) Azure Cosmos DB  
B) Azure Blob Storage  
C) Azure AI Search  
D) Azure Cache for Redis  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** Azure AI Search (formerly Azure Cognitive Search) provides hybrid search combining vector similarity, BM25 keyword search, and semantic ranking with a single managed service. It supports HNSW vector indexing and semantic configuration for re-ranking.</details>

---

### Q3: In the Customer Support Engine, what LangGraph construct enables conditional routing based on intent classification?

A) `add_edge()`  
B) `add_conditional_edges()`  
C) `interrupt_before()`  
D) `Send()`  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** `add_conditional_edges()` allows dynamic routing based on a function that examines the current state and returns the next node name. This is essential for intent-based routing where the classifier output determines which handler (KB retrieval, account lookup, escalation) executes next.</details>

---

### Q4: What is the primary benefit of using WebSockets over REST with SSE for the Customer Support Engine?

A) Simpler implementation  
B) Bidirectional communication enabling client signals during generation  
C) Better browser compatibility  
D) Lower latency for all requests  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** WebSockets provide persistent bidirectional connections, allowing the client to send signals during generation (e.g., stop, regenerate, update context). REST with SSE only supports server-to-client streaming. For interactive chat applications, bidirectional communication is essential.</details>

---

### Q5: In the Market Intelligence Agent, what pattern is used to handle documents larger than the LLM context window?

A) Prompt compression  
B) Map-reduce summarization  
C) Model routing  
D) Semantic caching  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Map-reduce summarization splits large documents into chunks, generates summaries for each chunk (map phase), then combines those summaries into a final summary (reduce phase). This handles documents of any size by processing them in smaller pieces.</details>

---

### Q6: Which tool is used for JavaScript-rendered page scraping in the Market Intelligence Agent?

A) BeautifulSoup  
B) Scrapy  
C) Playwright  
D) Selenium  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** Playwright is used because it can render JavaScript-heavy pages, wait for network idle, and extract content after dynamic content loads. BeautifulSoup alone cannot execute JavaScript, and while Selenium works, Playwright provides better async support and performance.</details>

---

### Q7: In the Multi-Agent Researcher using CrewAI, what process type ensures sequential execution of Researcher → Critic → Writer?

A) `Process.hierarchical`  
B) `Process.sequential`  
C) `Process.parallel`  
D) `Process.consensus`  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** `Process.sequential` executes tasks in order, with each task receiving the output of the previous task as context. This matches the Researcher → Critic → Writer pipeline where each agent builds on the previous agent's work.</details>

---

### Q8: What role does Cosmos DB play in the Multi-Agent Researcher architecture?

A) Vector search for document retrieval  
B) Persistent shared memory across agent executions  
C) Real-time WebSocket connections  
D) Container orchestration  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Cosmos DB serves as persistent shared memory, storing research findings, critique notes, draft versions, and conversation history. This enables resuming research sessions and building knowledge over time across multiple crew executions.</details>

---

### Q9: Which Bicep resource type is used to provision Azure OpenAI?

A) `Microsoft.OpenAI/accounts`  
B) `Microsoft.CognitiveServices/accounts`  
C) `Microsoft.AI/services`  
D) `Microsoft.MachineLearning/workspaces`  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Azure OpenAI is provisioned as a Cognitive Services account with `kind: 'OpenAI'`. The resource type is `Microsoft.CognitiveServices/accounts@2024-06-01-preview`. Deployments within the account use the sub-resource type `Microsoft.CognitiveServices/accounts/deployments`.</details>

---

### Q10: What is the purpose of re-ranking in the Book Recommender pipeline?

A) Generate embeddings for new books  
B) Improve result relevance by combining search scores with personalization signals  
C) Filter out inappropriate content  
D) Compress the search index  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Re-ranking takes the initial search results and re-scores them using additional signals like user genre preferences, book ratings, and diversity constraints. This personalizes results beyond what the initial hybrid search can achieve.</details>

---

### Q11: In the Customer Support Engine, what does the PostgreSQL checkpointer in LangGraph provide?

A) Faster inference  
B) Durable session state that persists across conversations  
C) Vector storage for KB documents  
D) Real-time streaming  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** The PostgreSQL checkpointer saves the graph state at each step, enabling durable session persistence. This means conversations survive server restarts, and users can resume sessions. `MemorySaver` is in-memory only and loses state on restart.</details>

---

### Q12: Which evaluation framework is recommended for testing RAG system quality before production deployment?

A) pytest  
B) Locust  
C) RAGAS  
D) OWASP ZAP  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** RAGAS (RAG Assessment) specifically evaluates RAG systems on metrics like faithfulness (does the answer follow from context), answer relevance, context precision, and context recall. pytest tests code logic, Locust tests load, and OWASP ZAP tests security.</details>

---

### Q13: What is the primary purpose of the validation agent in the Market Intelligence Agent?

A) Generate the final report  
B) Scrape web sources  
C) Fact-check claims and assign confidence scores  
D) Manage Azure infrastructure  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** The validation agent reviews the reasoning agent's analysis, verifies claims against source material, identifies unsupported assertions, flags potential biases, and assigns confidence scores. This quality gate prevents hallucinated or biased insights from reaching the final report.</details>

---

### Q14: In the Book Recommender Bicep template, what scaling configuration is used for the Container App?

A) Fixed replica count of 3  
B) HTTP-based autoscaling with min 1, max 10 replicas  
C) GPU-based scaling  
D) Cron-based scaling  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** The Bicep template configures HTTP-based autoscaling with `minReplicas: 1` and `maxReplicas: 10`, using a concurrent requests threshold of 50. This allows the API to scale up under load and scale down during idle periods.</details>

---

### Q15: What streaming mode in LangGraph's `astream_events` is used to deliver token-by-token responses?

A) `"values"`  
B) `"updates"`  
C) `"messages"`  
D) Event type `"on_chat_model_stream"`  

<details><summary><strong>Answer: D</strong></summary>**Explanation:** The `astream_events` method with version="v2" emits events including `"on_chat_model_stream"` events that contain individual token chunks. The WebSocket handler checks for this event type and forwards each token to the client for real-time streaming display.</details>

---

### Q16: Which CrewAI tool enables the Researcher agent to search the web?

A) `ScrapeWebsiteTool`  
B) `SerperDevTool`  
C) `FileReadTool`  
D) `CodeDocsSearchTool`  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** `SerperDevTool` provides web search capabilities through the Serper API (Google Search API). `ScrapeWebsiteTool` extracts content from specific URLs, but `SerperDevTool` is used for discovering relevant sources in the first place.</details>

---

### Q17: What is the primary risk of not having a validation layer in a multi-agent research pipeline?

A) Increased latency  
B) Higher infrastructure costs  
C) Hallucinated or biased insights reaching the final report  
D) Reduced web scraping throughput  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** Without validation, the reasoning agent's analysis goes unchecked. LLMs can hallucinate facts, overstate confidence, or exhibit bias. The validation agent acts as a quality gate, catching these issues before they appear in the final deliverable.</details>

---

### Q18: In the production readiness checklist, what is the recommended minimum test coverage for unit tests?

A) 50%  
B) 60%  
C) 80%  
D) 100%  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** The checklist recommends >80% code coverage for unit tests. This is a practical balance between thoroughness and development velocity. 100% coverage is often impractical and can lead to testing implementation details rather than behavior.</details>

---

### Q19: Which Azure service is used for caching popular queries and trending books in the Book Recommender?

A) Azure Cosmos DB  
B) Azure AI Search  
C) Azure Cache for Redis  
D) Azure Blob Storage  

<details><summary><strong>Answer: C</strong></summary>**Explanation:** Azure Cache for Redis provides low-latency caching for frequently accessed data like popular search queries and trending book lists. This reduces load on the vector search and LLM services for common requests.</details>

---

### Q20: What deployment strategy is recommended for zero-downtime releases in the production readiness checklist?

A) Rolling restart  
B) Canary or blue-green deployment  
C) Direct replacement  
D) Manual deployment  

<details><summary><strong>Answer: B</strong></summary>**Explanation:** Canary (gradual traffic shift) or blue-green (atomic environment switch) deployments ensure the system remains available during updates. Canary allows monitoring with a small traffic percentage before full rollout, while blue-green enables instant rollback by switching back.</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 18-20 | Expert | Ready to architect production AI systems |
| 15-17 | Proficient | Strong understanding, review weak areas |
| 11-14 | Competent | Good foundation, revisit specific project architectures |
| 7-10 | Developing | Re-read concepts.md and study architecture diagrams |
| 0-6 | Beginner | Review all module materials and prerequisite modules |


---

## Bonus: Senior / JD-Aligned Questions (Risk-Management Capstone)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the best architecture for a credit-risk analyst copilot?

A) An LLM as the primary classifier for the risk score  
B) A calibrated gradient-boosted model for the score, plus RAG/LLM for policy Q&A and narratives  
C) A single prompt with no retrieval  
D) A rules engine only  

**Answer: B** — use classic ML for the calibrated, explainable decision and GenAI for reasoning/explanation.

### BQ2. Which capstone deliverable maps to the JD metric "reduced AI deployment timelines"?

A) A bigger model  
B) MLOps automation and paved-path CI/CD with eval gates  
C) More prompts  
D) A larger context window  

**Answer: B** — automation and paved paths are what compress idea-to-production time.

### BQ3. What makes a capstone "production-ready" versus a notebook demo?

A) A nicer chart  
B) Eval/CI gates, monitoring, rollback, audit trail, and security/cost controls  
C) More training epochs  
D) A public GitHub star count  

**Answer: B** — production readiness is operational scaffolding, not model size.

### BQ4. For predicting default probability from tabular features, the right model family is:

A) A large language model  
B) Gradient-boosted trees — calibrated, explainable, and fast  
C) A diffusion model  
D) A k-means cluster  

**Answer: B** — tabular risk prediction is GBM territory; an LLM is the wrong primary classifier.

### BQ5. What is the best way to present the capstone's impact to executives?

A) Walk through the model architecture in detail  
B) Lead with the business outcome and a quantified metric, then tie tech choices to that value  
C) Show the training loss curve  
D) List every library used  

**Answer: B** — executives buy outcomes; anchor on the metric and the value, not the architecture.

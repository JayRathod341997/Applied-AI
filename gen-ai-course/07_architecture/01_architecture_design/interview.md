# GenAI Architecture - Interview Questions

This document contains interview questions and answers covering Module 7: Designing MLOps-Ready GenAI Architectures.

---

## 1. Architecture & Lifecycle Design

### Q1: What are MLOps touchpoints in RAG systems?

**Answer:** MLOps touchpoints in RAG include:

- **Data Pipeline:** Document loading, chunking, embedding generation
- **Index Management:** Vector database updates, versioning
- **Model Management:** Embedding models, LLM versions
- **Prompt Management:** Template versioning, A/B testing
- **Retrieval Tuning:** Testing different retrieval strategies
- **Monitoring:** Quality metrics, latency tracking

---

### Q2: Explain the separation of training vs inference vs orchestration layers.

**Answer:** Layer separation:

- **Training Layer:** Fine-tuning models, embedding training, RLHF
- **Inference Layer:** LLM API calls, embedding generation, vector search
- **Orchestration Layer:** Workflow management, agent coordination, routing

Each layer has different scaling needs, monitoring requirements, and cost structures.

---

### Q3: What are batch vs real-time vs agent-driven inference patterns?

**Answer:**

| Pattern | Use Case | Latency | Cost |
|---------|----------|---------|------|
| Batch | Scheduled reports, bulk processing | Hours | Lower |
| Real-time | User-facing Q&A, chatbots | Seconds | Higher |
| Agent-driven | Multi-step tasks, complex reasoning | Variable | Variable |

---

### Q4: How do you design embedding refresh and data ingestion workflows?

**Answer:** Workflow design:

1. **Change Detection:** Monitor source for updates (webhooks, polling)
2. **Incremental Processing:** Only process changed documents
3. **Version Control:** Track embedding versions with timestamps
4. **Backfill Strategy:** Handle bulk updates during off-hours
5. **Health Checks:** Verify index integrity after updates

---

### Q5: How do you map agent workflows to deployment and monitoring pipelines?

**Answer:** Mapping approach:

- **Workflow Definition:** Store agent graphs as code (LangGraph, etc.)
- **Deployment Pipeline:** Deploy graph updates with CI/CD
- **Monitoring Pipeline:** Track agent step execution, success rates
- **Feedback Loop:** Log agent actions for continuous improvement
- **Rollback:** Version control for agent logic

---

## Architecture Design Questions

### Q6: What is a typical enterprise GenAI reference architecture?

**Answer:** Enterprise architecture includes:

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│    (Web, Mobile, API Gateway)               │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Orchestration Layer                │
│   (Agent Framework, Workflow Engine)        │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│           Inference Layer                   │
│  (LLM APIs, Embedding Services, Tools)      │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│           Knowledge Layer                   │
│    (Vector DB, Document Store, Cache)        │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Data & Training Layer               │
│   (Data Pipeline, Fine-tuning, Monitoring)  │
└─────────────────────────────────────────────┘
```

---

### Q7: What are key architectural decisions for RAG systems?

**Answer:** Key decisions:

1. **Vector DB Selection:** Managed vs self-hosted, scalability needs
2. **Embedding Strategy:** Single vs multi-model, update frequency
3. **Chunking Strategy:** Fixed vs semantic vs recursive
4. **Retrieval Strategy:** Single-hop vs multi-hop, reranking
5. **Caching Strategy:** Full response vs embeddings vs prompts
6. **LLM Selection:** Cost vs quality vs latency tradeoffs

---

### Q8: How do you design for high availability in GenAI systems?

**Answer:** HA design considerations:

- **Redundancy:** Multiple LLM providers as fallbacks
- **Circuit Breakers:** Handle provider outages gracefully
- **Rate Limiting:** Protect against provider throttling
- **Graceful Degradation:** Answer from cache if services fail
- **Health Checks:** Monitor all system components
- **Auto-scaling:** Handle traffic spikes

---

### Q9: What are the differences between monolithic vs microservices architecture for GenAI?

**Answer:**

| Aspect | Monolithic | Microservices |
|--------|-------------|---------------|
| Deployment | Single unit | Independent services |
| Scaling | Vertical | Horizontal per service |
| Complexity | Lower | Higher |
| Failure Isolation | Lower | Higher |
| Latency | Lower (no network) | Higher (network calls |
| Use Case | PoC, small scale | Enterprise, complex |

---

### Q10: How do you handle cost optimization in GenAI architecture?

**Answer:** Optimization strategies:

- **Tiered LLM Usage:** Cheap models for simple tasks, expensive for complex
- **Caching:** Cache embeddings and responses
- **Batch Processing:** Group requests where possible
- **Prompt Optimization:** Minimize token usage
- **Right-sizing:** Match model to use case
- **Usage Monitoring:** Track and alert on spend

---

## Production Architecture Questions

### Q11: What components are needed for a production-ready RAG system?

**Answer:** Required components:

- **Document Processing:** Loaders, converters, chunkers
- **Vector Storage:** Database, indexing, backup
- **Embedding Service:** Model management, scaling
- **LLM Gateway:** Provider abstraction, fallback, caching
- **API Layer:** REST/GraphQL interface, auth, rate limiting
- **Monitoring:** Metrics, logging, alerting
- **CI/CD:** Automated testing and deployment

---

### Q12: How do you design for security in GenAI systems?

**Answer:** Security design:

- **Authentication:** API keys, OAuth, JWT tokens
- **Authorization:** RBAC for data access
- **Encryption:** TLS in transit, encryption at rest
- **PII Handling:** Redaction, masking, access controls
- **Audit Logging:** Track all requests and actions
- **Input Validation:** Sanitize prompts, prevent injection

---

### Q13: What is the role of caching in GenAI architecture?

**Answer:** Caching roles:

- **Semantic Cache:** Store LLM responses for similar queries
- **Embedding Cache:** Cache computed embeddings
- **Document Cache:** Cache retrieved documents
- **Config Cache:** Store prompt templates

Benefits: Cost reduction, latency improvement, consistency

---

### Q14: How do you design for scalability?

**Answer:** Scalability design:

1. **Horizontal Scaling:** Add more instances of stateless services
2. **Database Scaling:** Sharding, read replicas for vector DB
3. **Async Processing:** Queue-based architecture for heavy tasks
4. **Connection Pooling:** Efficient database connections
5. **CDN:** Serve static content from edge
6. **Auto-scaling:** React to traffic patterns

---

## System Design Scenarios

### Q15: Design a customer support chatbot system.

**Answer:** Design components:

1. **User Interface:** Web widget, mobile SDK
2. **API Gateway:** Auth, rate limiting, routing
3. **Intent Router:** Classify user intent
4. **RAG Engine:** Knowledge base retrieval
5. **Response Generator:** LLM with context
6. **Human Handoff:** Escalation to agents
7. **Analytics:** Track satisfaction, topics
8. **Admin Portal:** Knowledge base management

---

### Q16: Design a code assistant system.

**Answer:** Design components:

1. **Code Indexer:** Parse repositories, generate embeddings
2. **Vector DB:** Store code embeddings with metadata
3. **Context Retriever:** Find relevant code snippets
4. **LLM Generator:** Generate code with context
5. **Sandbox Executor:** Run generated code safely
6. **Test Generator:** Create unit tests
7. **Documentation Generator:** Generate code docs

---

### Q17: Design a multi-tenant SaaS AI platform.

**Answer:** Design considerations:

- **Tenant Isolation:** Separate vector DBs or namespaces
- **Rate Limiting:** Per-tenant quotas
- **Data Residency:** Regional data storage options
- **Customization:** Tenant-specific prompts, models
- **Billing:** Usage-based metering
- **SSO:** Integration with tenant identity providers

---

## Follow-up Architecture Questions

### Q18: How do you choose between different embedding models?

**Answer:** Selection criteria:

- **Quality:** Semantic understanding for your domain
- **Dimensions:** Smaller = faster, larger = more precise
- **Latency:** Model size affects generation time
- **Cost:** API cost per 1K tokens
- **Language Support:** Multilingual requirements
- **Hosting:** Cloud API vs local deployment

---

### Q19: What are the tradeoffs between different LLM providers?

**Answer:** Provider comparison:

| Provider | Strengths | Weaknesses |
|----------|-----------|------------|
| OpenAI | Quality, ecosystem | Cost, limited control |
| Anthropic | Safety, long context | Newer, fewer features |
| Azure | Enterprise, compliance | Setup complexity |
| AWS | Integration, scale | Less optimized |
| Self-hosted | Control, customization | Operational burden |

---

### Q20: How do you handle model deprecation or provider changes?

**Answer:** Handling strategy:

1. **Abstraction Layer:** Don't hardcode provider calls
2. **Interface Contracts:** Standardize LLM interactions
3. **Testing:** Validate outputs across models
4. **Gradual Migration:** A/B test new models
5. **Fallback Chains:** Define backup providers
6. **Version Control:** Track model versions in use

---

## Summary

Key architectural topics:

1. **Layered Architecture:** Training, inference, orchestration separation
2. **Inference Patterns:** Batch, real-time, agent-driven
3. **Data Workflows:** Ingestion, embedding refresh
4. **Production Readiness:** HA, security, scalability
5. **Cost Optimization:** Caching, tiered usage

---

## References

- [MLOps Best Practices](references.md)
- [Cloud Architecture Patterns](references.md)
- [RAG System Design](references.md)

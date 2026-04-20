# Deployment Guide

## Containerized Deployment

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  rag-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/trulens
    depends_on:
      - db
    volumes:
      - ./chroma_db:/app/chroma_db

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=trulens
    volumes:
      - postgres_data:/var/lib/postgresql/data

  trulens-dashboard:
    image: trulens/dashboard:latest
    ports:
      - "8501:8501"
    environment:
      - TRUERA_API_KEY=${TRUERA_API_KEY}

volumes:
  postgres_data:
```

## Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-guardrails
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-guardrails
  template:
    metadata:
      labels:
        app: rag-guardrails
    spec:
      containers:
      - name: api
        image: rag-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

## API Implementation

### FastAPI with Guardrails

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from guardrails import GuardedRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG with Guardrails API")

# Initialize RAG with guardrails
rag = GuardedRAG(
    retriever=vector_store.as_retriever(),
    llm=ChatOpenAI(temperature=0)
)

class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    groundedness: float
    is_fallback: bool
    latency_ms: int

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    import time
    start = time.time()
    
    try:
        result = rag.query(request.question)
        
        return QueryResponse(
            answer=result.answer,
            groundedness=result.evaluation.groundedness,
            is_fallback=result.is_fallback,
            latency_ms=int((time.time() - start) * 1000)
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    return rag.get_metrics()
```

## Scaling Considerations

### Horizontal Scaling

```python
# For high volume, use multiple replicas behind load balancer
# Update docker-compose for scaling:
# docker-compose up --scale rag-api=3
```

### Caching Strategy

```python
# Implement Redis caching for evaluations
from redis import Redis
import json

cache = Redis(host='redis', port=6379)

def cached_evaluate(query: str, response: str, contexts: list):
    cache_key = f"eval:{hash((query, response, tuple(contexts)))}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Evaluate
    result = evaluate(query, response, contexts)
    
    # Cache result (1 hour TTL)
    cache.setex(cache_key, 3600, json.dumps(result))
    
    return result
```

## Monitoring with Prometheus

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

queries_total = Counter('rag_queries_total', 'Total queries')
queries_fallback = Counter('rag_queries_fallback', 'Queries using fallback')
query_latency = Histogram('rag_query_latency', 'Query latency')
groundedness_gauge = Gauge('rag_groundedness', 'Average groundedness')

# In API
queries_total.inc()
if result.is_fallback:
    queries_fallback.inc()
query_latency.observe(latency_ms)
groundedness_gauge.set(evaluation.groundedness)
```

## Environment Configuration

```bash
# .env.production
OPENAI_API_KEY=sk-prod-xxx
DATABASE_URL=postgresql://prod-db:5432/trulens
REDIS_URL=redis://prod-redis:6379
LOG_LEVEL=INFO
GUARDIAN_THRESHOLD=0.7
```

## Health Checks

```python
# Health check with deeper verification
@app.get("/health")
def health():
    checks = {
        "api": True,
        "vector_store": False,
        "llm": False
    }
    
    # Check vector store
    try:
        vector_store.similarity_search("test", k=1)
        checks["vector_store"] = True
    except Exception as e:
        logger.error(f"Vector store check failed: {e}")
    
    # Check LLM
    try:
        llm.invoke("test")
        checks["llm"] = True
    except Exception as e:
        logger.error(f"LLM check failed: {e}")
    
    all_healthy = all(checks.values())
    return {"status": "healthy" if all_healthy else "degraded", "checks": checks}
```

## CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Run RAGAS evaluation
        run: python -m pytest tests/test_ragas.py -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker
        run: docker build -t rag-api:${{ github.sha }} .
      - name: Push to registry
        run: docker push registry.io/rag-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/rag-api \
          api=registry.io/rag-api:${{ github.sha }}
```

## Rollback Procedures

```bash
# Rollback to previous version
kubectl rollout undo deployment/rag-guardrails

# Or rollback to specific version
kubectl rollout undo deployment/rag-guardrails --to-revision=2
```

## Performance Tuning

### Async Processing

```python
# Use async for non-blocking operations
async def async_query(request: QueryRequest):
    # Run retrieval and generation concurrently
    docs_task = asyncio.create_task(retriever.ainvoke(request.question))
    eval_task = asyncio.create_task(evaluate_async(...))
    
    docs = await docs_task
    evaluation = await eval_task
    
    return {"docs": docs, "evaluation": evaluation}
```

### Batching

```python
# Batch evaluation calls for efficiency
async def batch_evaluate(queries: List[Query]):
    # Group similar evaluations
    results = await asyncio.gather(
        *[evaluate(q) for q in queries]
    )
    return results
```
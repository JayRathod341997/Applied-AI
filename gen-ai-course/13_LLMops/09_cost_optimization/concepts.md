# Cost Optimization - Concepts

## Table of Contents
1. [Understanding LLM Costs](#understanding-llm-costs)
2. [Token Optimization](#token-optimization)
3. [Caching Strategies](#caching-strategies)
4. [Provider-Native Prompt Caching](#provider-native-prompt-caching)
5. [Output Length Control](#output-length-control)
6. [Request Batching](#request-batching)
7. [Model Selection](#model-selection)
8. [Fine-Tuning vs. Prompting Trade-offs](#fine-tuning-vs-prompting-trade-offs)
9. [Infrastructure Cost](#infrastructure-cost)
10. [Budget Management](#budget-management)
11. [Cost Monitoring](#cost-monitoring)
12. [Cost Optimization Decision Tree](#cost-optimization-decision-tree)
13. [Implementation](#implementation)

---

## Understanding LLM Costs

### Cost Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Cost Components                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Total Cost = API Costs + Infrastructure Costs + OpEx           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  API Costs (Typically 70-90% of total)                   │  │
│   │  ├── Input Tokens × Price per 1K tokens                 │  │
│   │  └── Output Tokens × Price per 1K tokens                │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Infrastructure Costs (10-20% of total)                  │  │
│   │  ├── GPU instances (for self-hosted)                     │  │
│   │  ├── Cloud compute (API servers)                         │  │
│   │  ├── Storage (models, vector DB)                         │  │
│   │  └── Network bandwidth                                   │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Operational Costs (5-10% of total)                      │  │
│   │  ├── Monitoring & logging                                │  │
│   │  ├── Engineering time                                   │  │
│   │  └── Compliance & security                               │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Provider Pricing Comparison

| Provider | Model | Input ($/1K) | Output ($/1K) | Context |
|----------|-------|--------------|---------------|---------|
| **OpenAI** | GPT-4 | $0.03 | $0.06 | 128K |
| **OpenAI** | GPT-4 Turbo | $0.01 | $0.03 | 128K |
| **OpenAI** | GPT-3.5 Turbo | $0.001 | $0.002 | 16K |
| **Anthropic** | Claude 3 Opus | $0.015 | $0.075 | 200K |
| **Anthropic** | Claude 3 Sonnet | $0.003 | $0.015 | 200K |
| **Anthropic** | Claude 3 Haiku | $0.00025 | $0.00125 | 200K |
| **Google** | Gemini Pro | $0.00125 | $0.005 | 32K |
| **Google** | Gemini Ultra | $0.0075 | $0.03 | 32K |

---

## Token Optimization

### Prompt Compression

```python
# prompt_optimizer.py
from typing import List, Dict, Optional
import re

class PromptOptimizer:
    """
    Optimize prompts to reduce token count
    """
    
    def __init__(self):
        self.compression_patterns = [
            # Remove extra whitespace
            (r'\s+', ' '),
            # Remove redundant newlines
            (r'\n\n+', '\n'),
            # Remove common filler words
            (r'\bplease\b', ''),
            (r'\bkindly\b', ''),
            (r'\bbasically\b', ''),
        ]
    
    def compress(self, prompt: str) -> str:
        """Compress prompt by removing unnecessary tokens"""
        compressed = prompt
        
        for pattern, replacement in self.compression_patterns:
            compressed = re.sub(pattern, replacement, compressed)
        
        # Remove leading/trailing whitespace
        compressed = compressed.strip()
        
        return compressed
    
    def extract_essentials(self, prompt: str) -> str:
        """Extract only essential parts of the prompt"""
        # Remove greetings and pleasantries
        essential = prompt
        
        # Remove common patterns
        patterns_to_remove = [
            r'^hi(,| |\.|$)',
            r'^hello(,| |\.|$)',
            r'^hey(,| |\.|$)',
            r'^good morning(,| |\.|$)',
            r'^good afternoon(,| |\.|$)',
            r'^thank you(,| |\.|$)',
            r'^thanks(,| |\.|$)',
        ]
        
        for pattern in patterns_to_remove:
            essential = re.sub(pattern, '', essential, flags=re.IGNORECASE)
        
        return essential.strip()
    
    def optimize_few_shot(self, examples: List[Dict]) -> List[Dict]:
        """Optimize few-shot examples to use fewer tokens"""
        optimized = []
        
        for example in examples:
            # Simplify inputs/outputs while maintaining clarity
            optimized_example = {
                "input": self.compress(example.get("input", "")),
                "output": self.compress(example.get("output", ""))
            }
            optimized.append(optimized_example)
        
        return optimized
    
    def use_abbreviations(self, text: str) -> str:
        """Replace common phrases with abbreviations"""
        abbreviations = {
            "information": "info",
            "example": "ex",
            "question": "Q",
            "answer": "A",
            "description": "desc",
            "approximately": "approx",
        }
        
        for full, abbr in abbreviations.items():
            text = re.sub(r'\b' + full + r'\b', abbr, text, flags=re.IGNORECASE)
        
        return text

# Token counting
def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text"""
    import tiktoken
    
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    
    return len(tokens)

def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4"
) -> float:
    """Estimate cost for a request"""
    
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    p = pricing.get(model, {"input": 0, "output": 0})
    
    return (input_tokens / 1000) * p["input"] + (output_tokens / 1000) * p["output"]
```

### Context Window Management

```python
# context_manager.py
from typing import List, Dict, Optional

class ContextManager:
    """
    Manage context window efficiently
    """
    
    def __init__(self, max_tokens: int = 8000, reserved_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens
        self.available_tokens = max_tokens - reserved_tokens
    
    def truncate_history(
        self,
        messages: List[Dict],
        keep_system: bool = True
    ) -> List[Dict]:
        """Truncate message history to fit within context"""
        truncated = []
        
        if keep_system and messages and messages[0].get("role") == "system":
            truncated.append(messages[0])
        
        total_tokens = 0
        
        # Process messages in reverse (keep most recent)
        for message in reversed(messages):
            if message.get("role") == "system" and keep_system:
                continue
            
            # Estimate tokens
            msg_tokens = self._estimate_tokens(message)
            
            if total_tokens + msg_tokens <= self.available_tokens:
                truncated.insert(0 if not truncated or truncated[0].get("role") != "system" else 1, message)
                total_tokens += msg_tokens
            else:
                break
        
        return truncated
    
    def summarize_older_messages(
        self,
        messages: List[Dict],
        summarize_fn
    ) -> List[Dict]:
        """Summarize older messages to save tokens"""
        if len(messages) <= 3:
            return messages
        
        # Keep recent messages
        recent = messages[-3:]
        
        # Summarize older ones
        older = messages[:-3]
        summary = summarize_fn(older)
        
        return [{"role": "system", "content": f"Previous conversation summary: {summary}"}] + recent
    
    def _estimate_tokens(self, message: Dict) -> int:
        """Rough estimate of tokens in a message"""
        content = message.get("content", "")
        # Rough estimate: 1 token ≈ 4 characters
        return len(content) // 4

# Streaming to reduce perceived latency
async def stream_response(prompt: str, model: str = "gpt-4"):
    """Stream response to reduce perceived latency"""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

## Caching Strategies

### Multi-Level Caching

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Level Caching Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request                                                         │
│      │                                                            │
│      ▼                                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L1: Exact Match Cache (In-Memory)                       │   │
│   │  - Redis                                                  │   │
│   │  - TTL: 1-5 minutes                                      │   │
│   │  - Hit Rate Target: 30-50%                               │   │
│   │  - Latency: <1ms                                         │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L2: Semantic Cache (Vector Store)                      │   │
│   │  - Store embeddings of prompts                          │   │
│   │  - Similarity threshold: 0.85-0.95                      │   │
│   │  - TTL: 1-24 hours                                      │   │
│   │  - Hit Rate Target: 20-40%                               │   │
│   │  - Latency: 10-50ms                                      │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L3: Provider Cache                                     │   │
│   │  - OpenAI/Anthropic built-in cache                      │   │
│   │  - Automatic for identical prompts                      │   │
│   │  - Varies by provider                                   │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│                     LLM Call                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Semantic Cache Implementation

```python
# semantic_cache.py
from typing import Optional, Dict
import hashlib
import time

class SemanticCache:
    """
    Semantic cache for LLM responses using vector similarity
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
        embedding_model: str = "text-embedding-ada-002"
    ):
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.embedding_model = embedding_model
        
        # In production, use a proper vector store
        self._cache: Dict = {}
        self._embeddings: Dict = {}
    
    async def get(self, prompt: str) -> Optional[Dict]:
        """Get cached response for similar prompts"""
        # Get embedding for prompt
        embedding = await self._get_embedding(prompt)
        
        # Find similar cached prompts
        best_match = None
        best_similarity = 0
        
        for cached_prompt, cached_data in self._embeddings.items():
            similarity = self._cosine_similarity(embedding, cached_data["embedding"])
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_prompt
        
        # Check if similarity is above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            cached_entry = self._cache[best_match]
            
            # Check TTL
            if time.time() - cached_entry["timestamp"] < self.ttl_seconds:
                # Update access time
                cached_entry["last_access"] = time.time()
                cached_entry["hit_count"] = cached_entry.get("hit_count", 0) + 1
                
                return {
                    "response": cached_entry["response"],
                    "similarity": best_similarity,
                    "cached_prompt": best_match
                }
        
        return None
    
    async def set(self, prompt: str, response: str, metadata: Dict = None):
        """Cache a response"""
        embedding = await self._get_embedding(prompt)
        
        # Store with hashed key
        key = hashlib.md5(prompt.encode()).hexdigest()
        
        self._cache[prompt] = {
            "response": response,
            "timestamp": time.time(),
            "last_access": time.time(),
            "hit_count": 0,
            "metadata": metadata or {}
        }
        
        self._embeddings[prompt] = {
            "embedding": embedding
        }
    
    async def _get_embedding(self, text: str) -> list:
        """Get embedding for text"""
        # Use OpenAI embeddings API in production
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        
        response = await client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        
        return response.data[0].embedding
    
    def _cosine_similarity(self, a: list, b: list) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        a = np.array(a)
        b = np.array(b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        return dot_product / (norm_a * norm_b)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_hits = sum(e.get("hit_count", 0) for e in self._cache.values())
        
        return {
            "total_entries": len(self._cache),
            "total_hits": total_hits,
            "cache_size_bytes": sum(
                len(str(v)) for v in self._cache.values()
            )
        }
```

---

## Model Selection

### Intelligent Model Routing

```python
# model_router.py
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class ModelConfig:
    name: str
    strength: str
    latency_ms: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    max_output_tokens: int

class ModelRouter:
    """
    Route requests to appropriate models based on task
    """
    
    MODEL_CONFIGS = {
        "gpt-4": ModelConfig(
            name="gpt-4",
            strength="complex reasoning, analysis",
            latency_ms=2000,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            context_window=128000,
            max_output_tokens=4096
        ),
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            strength="simple tasks, high volume",
            latency_ms=500,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
            context_window=16385,
            max_output_tokens=4096
        ),
        "claude-3-sonnet": ModelConfig(
            name="claude-3-sonnet",
            strength="balanced, long context",
            latency_ms=1000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            context_window=200000,
            max_output_tokens=4096
        )
    }
    
    # Task classification patterns
    TASK_PATTERNS = {
        "simple": [
            r"^(what is|who is|when did|where is)",
            r"^(translate|convert|calculate)",
            r"^summarize",
            r"^list"
        ],
        "moderate": [
            r"explain",
            r"compare",
            r"describe",
            r"write (code|email|letter)"
        ],
        "complex": [
            r"analyze",
            r"design",
            r"architect",
            r"evaluate",
            r"create a comprehensive"
        ]
    }
    
    def classify_task(self, prompt: str) -> str:
        """Classify task complexity"""
        prompt_lower = prompt.lower()
        
        for complexity, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return complexity
        
        return "moderate"  # Default
    
    def select_model(
        self,
        prompt: str,
        user_tier: str = "free",
        context_length: int = None
    ) -> str:
        """Select the best model for the task"""
        
        complexity = self.classify_task(prompt)
        
        # Check context length requirements
        if context_length and context_length > 16000:
            # Need long context model
            if context_length > 128000:
                return "claude-3-sonnet"
        
        # Route based on complexity and tier
        if user_tier == "free":
            # Free tier gets smaller model
            return "gpt-3.5-turbo"
        
        if complexity == "simple":
            return "gpt-3.5-turbo"
        
        if complexity == "moderate":
            return "claude-3-sonnet"
        
        if complexity == "complex":
            return "gpt-4"
        
        return "gpt-3.5-turbo"  # Default
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for model usage"""
        config = self.MODEL_CONFIGS.get(model)
        
        if not config:
            return 0
        
        input_cost = (input_tokens / 1000) * config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * config.cost_per_1k_output
        
        return input_cost + output_cost
    
    def get_cheapest_alternative(self, model: str) -> str:
        """Get cheaper alternative model"""
        alternatives = {
            "gpt-4": "gpt-3.5-turbo",
            "claude-3-opus": "claude-3-sonnet",
            "claude-3-sonnet": "gpt-3.5-turbo"
        }
        
        return alternatives.get(model, model)
```

---

## Budget Management

### Budget Implementation

```python
# budget_manager.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

@dataclass
class Budget:
    limit: float
    spent: float = 0
    period_start: datetime = None
    
    def reset_if_needed(self, period: str):
        """Reset budget for new period"""
        now = datetime.now()
        
        if self.period_start is None:
            self.period_start = now
            return
        
        should_reset = False
        
        if period == "daily":
            should_reset = (now - self.period_start).days >= 1
        elif period == "weekly":
            should_reset = (now - self.period_start).days >= 7
        elif period == "monthly":
            should_reset = (now - self.period_start).month != self.period_start.month
        
        if should_reset:
            self.spent = 0
            self.period_start = now

class BudgetManager:
    """
    Manage LLM usage budgets
    """
    
    def __init__(self, daily_limit: float, monthly_limit: float):
        self.daily_budget = Budget(limit=daily_limit)
        self.monthly_budget = Budget(limit=monthly_limit)
        self.cost_per_user: Dict[str, float] = {}
    
    def check_budget(
        self,
        user_id: str,
        estimated_cost: float
    ) -> tuple[bool, str]:
        """Check if request is within budget"""
        
        # Reset budgets if needed
        self.daily_budget.reset_if_needed("daily")
        self.monthly_budget.reset_if_needed("monthly")
        
        # Check daily budget
        if self.daily_budget.spent + estimated_cost > self.daily_budget.limit:
            return False, f"Daily budget exceeded. Limit: ${self.daily_budget.limit}"
        
        # Check monthly budget
        if self.monthly_budget.spent + estimated_cost > self.monthly_budget.limit:
            return False, f"Monthly budget exceeded. Limit: ${self.monthly_budget.limit}"
        
        # Check user-specific budget
        user_spent = self.cost_per_user.get(user_id, 0)
        user_limit = self._get_user_limit(user_id)
        
        if user_spent + estimated_cost > user_limit:
            return False, f"User budget exceeded. Limit: ${user_limit}"
        
        return True, "Budget check passed"
    
    def record_cost(
        self,
        user_id: str,
        cost: float,
        metadata: Dict = None
    ):
        """Record actual cost"""
        self.daily_budget.spent += cost
        self.monthly_budget.spent += cost
        
        if user_id not in self.cost_per_user:
            self.cost_per_user[user_id] = 0
        
        self.cost_per_user[user_id] += cost
        
        # Log for analytics
        self._log_cost(user_id, cost, metadata)
    
    def _get_user_limit(self, user_id: str) -> float:
        """Get user-specific limit (could be dynamic)"""
        # Simple implementation: 10% of monthly budget per user
        return self.monthly_budget.limit * 0.1
    
    def _log_cost(self, user_id: str, cost: float, metadata: Dict):
        """Log cost for analytics"""
        # Implementation: send to logging/analytics system
        pass
    
    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        return {
            "daily": {
                "limit": self.daily_budget.limit,
                "spent": self.daily_budget.spent,
                "remaining": self.daily_budget.limit - self.daily_budget.spent,
                "utilization": (self.daily_budget.spent / self.daily_budget.limit) * 100
            },
            "monthly": {
                "limit": self.monthly_budget.limit,
                "spent": self.monthly_budget.spent,
                "remaining": self.monthly_budget.limit - self.monthly_budget.spent,
                "utilization": (self.monthly_budget.spent / self.monthly_budget.limit) * 100
            }
        }
```

---

## Cost Monitoring

### Cost Dashboard

```python
# cost_monitoring.py
from typing import Dict, List
from datetime import datetime, timedelta
import time

class CostMonitor:
    """
    Monitor and track LLM costs
    """
    
    def __init__(self):
        self.cost_by_model: Dict[str, float] = {}
        self.cost_by_user: Dict[str, float] = {}
        self.cost_by_endpoint: Dict[str, float] = {}
        self.cost_by_hour: Dict[int, float] = {}  # Hour of day
        
        self.total_tokens_by_model: Dict[str, Dict] = {}
    
    def record_request(
        self,
        model: str,
        user_id: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """Record a request's cost"""
        
        # By model
        self.cost_by_model[model] = self.cost_by_model.get(model, 0) + cost
        
        # By user
        self.cost_by_user[user_id] = self.cost_by_user.get(user_id, 0) + cost
        
        # By endpoint
        self.cost_by_endpoint[endpoint] = self.cost_by_endpoint.get(endpoint, 0) + cost
        
        # By hour
        hour = datetime.now().hour
        self.cost_by_hour[hour] = self.cost_by_hour.get(hour, 0) + cost
        
        # Track tokens
        if model not in self.total_tokens_by_model:
            self.total_tokens_by_model[model] = {
                "input": 0,
                "output": 0
            }
        
        self.total_tokens_by_model[model]["input"] += input_tokens
        self.total_tokens_by_model[model]["output"] += output_tokens
    
    def get_summary(self, period: str = "daily") -> Dict:
        """Get cost summary"""
        
        total_cost = sum(self.cost_by_model.values())
        
        # Calculate projections
        if period == "daily":
            hours_elapsed = datetime.now().hour + 1
        else:
            hours_elapsed = 24
        
        projected_daily = (total_cost / hours_elapsed) * 24
        
        return {
            "total_cost": total_cost,
            "by_model": self.cost_by_model,
            "by_user": dict(sorted(
                self.cost_by_user.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 users
            "by_endpoint": self.cost_by_endpoint,
            "total_tokens": self.total_tokens_by_model,
            "projected_daily": projected_daily
        }
    
    def get_anomalies(self) -> List[Dict]:
        """Detect cost anomalies"""
        anomalies = []
        
        # Check for unusually high user costs
        if self.cost_by_user:
            avg_cost = sum(self.cost_by_user.values()) / len(self.cost_by_user)
            
            for user_id, cost in self.cost_by_user.items():
                if cost > avg_cost * 10:
                    anomalies.append({
                        "type": "high_user_cost",
                        "user_id": user_id,
                        "cost": cost,
                        "avg_cost": avg_cost,
                        "multiplier": cost / avg_cost
                    })
        
        return anomalies
    
    def send_alert(self, message: str, severity: str = "warning"):
        """Send cost alert"""
        # Implementation: integrate with alerting system
        print(f"[{severity.upper()}] Cost Alert: {message}")
```

---

## Implementation

### Complete Cost Optimization Implementation

```python
# cost_optimization_service.py
from typing import Dict, Optional
import asyncio

class LLMServiceWithCostOptimization:
    """
    Complete LLM service with built-in cost optimization
    """
    
    def __init__(self):
        self.cache = SemanticCache(similarity_threshold=0.95)
        self.router = ModelRouter()
        self.budget_manager = BudgetManager(
            daily_limit=100.0,
            monthly_limit=2000.0
        )
        self.cost_monitor = CostMonitor()
        self.prompt_optimizer = PromptOptimizer()
    
    async def chat(
        self,
        prompt: str,
        user_id: str,
        endpoint: str = "chat",
        model_preference: Optional[str] = None
    ) -> Dict:
        """Chat with cost optimization"""
        
        # 1. Optimize prompt
        optimized_prompt = self.prompt_optimizer.compress(prompt)
        
        # 2. Check semantic cache
        cached = await self.cache.get(optimized_prompt)
        
        if cached:
            return {
                "response": cached["response"],
                "cached": True,
                "similarity": cached["similarity"]
            }
        
        # 3. Select model
        model = model_preference or self.router.select_model(optimized_prompt)
        
        # 4. Estimate tokens and cost
        input_tokens = count_tokens(optimized_prompt)
        estimated_output = 500  # Estimate
        estimated_cost = self.router.estimate_cost(model, input_tokens, estimated_output)
        
        # 5. Check budget
        allowed, message = self.budget_manager.check_budget(user_id, estimated_cost)
        
        if not allowed:
            # Try cheaper model
            cheaper_model = self.router.get_cheapest_alternative(model)
            estimated_cost = self.router.estimate_cost(
                cheaper_model, input_tokens, estimated_output
            )
            
            allowed, message = self.budget_manager.check_budget(user_id, estimated_cost)
            
            if not allowed:
                raise ValueError(message)
            
            model = cheaper_model
        
        # 6. Make request
        response = await self._call_model(model, optimized_prompt)
        
        # 7. Calculate actual cost
        output_tokens = count_tokens(response)
        actual_cost = self.router.estimate_cost(model, input_tokens, output_tokens)
        
        # 8. Record costs
        self.budget_manager.record_cost(user_id, actual_cost)
        self.cost_monitor.record_request(
            model=model,
            user_id=user_id,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=actual_cost
        )
        
        # 9. Cache response
        await self.cache.set(optimized_prompt, response)
        
        return {
            "response": response,
            "model": model,
            "cost": actual_cost,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens
            }
        }
    
    async def _call_model(self, model: str, prompt: str) -> str:
        """Make actual LLM call"""
        # Implementation: call OpenAI/Anthropic API
        pass

# Helper functions
def count_tokens(text: str) -> int:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
```

---

## Provider-Native Prompt Caching

Modern providers (Anthropic, OpenAI) offer **server-side prompt caching** that reuses the KV cache for repeated prompt prefixes. This is the highest-leverage, zero-effort optimization available — no application-level changes required beyond structuring prompts correctly.

### How It Works

When you send a request, the provider checks if the **prefix** of the prompt was recently processed. If yes, it skips recomputing those tokens and charges a discounted rate (typically 10–25% of full input price).

```
First Request  → Full computation → Full price
Second Request → Cache HIT on prefix → ~10% of input price
```

### Anthropic Cache Control (Claude)

Anthropic uses explicit `cache_control` markers to define what to cache:

```python
from anthropic import Anthropic

client = Anthropic()

# Mark large, stable content with cache_control
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a senior software engineer...",
        },
        {
            "type": "text",
            "text": open("large_codebase_context.txt").read(),  # 50K tokens
            "cache_control": {"type": "ephemeral"}             # Cache this!
        }
    ],
    messages=[{"role": "user", "content": user_question}]
)

# Usage shows cache savings
print(response.usage)
# cache_creation_input_tokens: 50000  (first call — writing cache)
# cache_read_input_tokens: 50000      (subsequent calls — reading cache)
# input_tokens: 25                    (only the question was charged)
```

**Pricing impact (Claude Sonnet)**:
| Token type | Price |
|-----------|-------|
| Regular input | $3.00 / 1M tokens |
| Cache write | $3.75 / 1M tokens (one-time) |
| Cache read | $0.30 / 1M tokens (90% savings) |

### What to Cache

```
✅ Good candidates for caching (stable, large, reused across requests):
   - System prompts with detailed instructions
   - Large reference documents, codebases, or knowledge bases
   - Few-shot examples
   - Tool/function definitions

❌ Bad candidates (changes every request):
   - User messages
   - Dynamic date/time context
   - Per-user personalization data
```

### Structuring Prompts for Maximum Cache Hits

The cache key is the **exact prefix** of the prompt. Always put stable content first, dynamic content last:

```
[CACHED]  System prompt (instructions, persona)
[CACHED]  Background documents / reference material
[CACHED]  Few-shot examples
──────────────────────────────────────
[DYNAMIC] Conversation history
[DYNAMIC] Current user message         ← changes every turn
```

---

## Output Length Control

Output tokens cost 3–5× more per token than input tokens on most models. Controlling output length directly cuts the largest variable cost.

### Strategies

#### 1. Set `max_tokens` Explicitly
Never leave `max_tokens` at the model default. Estimate what you need and cap it.

```python
# Bad: model may generate 4096 tokens when you only need ~100
response = client.chat.completions.create(model="gpt-4", messages=messages)

# Good: cap based on expected output size
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=150   # You know the answer is short
)
```

#### 2. Instruct for Brevity in the Prompt

The single cheapest optimization: tell the model to be concise.

```python
CONCISE_SUFFIX = "\n\nRespond in 2-3 sentences maximum. Be direct and specific."

# For structured extraction: force a schema
STRUCTURED_SUFFIX = "\n\nRespond with JSON only, no explanation: {\"field\": \"value\"}"
```

#### 3. Use Structured Output (JSON Mode)

Structured outputs eliminate conversational filler ("Sure! Here's the analysis...", "Great question!"). JSON-only responses can be 30–50% shorter.

```python
from openai import OpenAI
from pydantic import BaseModel

class SentimentResult(BaseModel):
    label: str      # "positive" | "negative" | "neutral"
    score: float    # 0.0 - 1.0
    reason: str

client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": f"Classify sentiment: {text}"}],
    response_format=SentimentResult,
)
# Output: {"label": "positive", "score": 0.92, "reason": "enthusiastic tone"}
# NOT: "Sure! I'd be happy to analyze this text for sentiment..."
```

#### 4. Output Length by Task Type

| Task | Recommended Strategy |
|------|---------------------|
| Classification | JSON mode, `max_tokens=20` |
| Summarization | Set `max_tokens` to 20% of input length |
| Code generation | `max_tokens` = estimated lines × 15 |
| Q&A / factual | Instruct "answer in 1–2 sentences" |
| Open-ended writing | Let model run; set generous but bounded limit |

---

## Request Batching

Many LLM providers offer **batch APIs** that process requests asynchronously at 50% lower cost in exchange for higher latency (results within 24 hours). Ideal for offline workloads.

### When to Use Batch Processing

```
✅ Use batch API for:
   - Dataset annotation / labeling
   - Bulk content generation (product descriptions, SEO copy)
   - Nightly report generation
   - Embedding generation for large document sets
   - Evaluation pipelines

❌ Don't use batch API for:
   - Real-time user-facing chat
   - Any flow requiring <5s latency
```

### OpenAI Batch API

```python
from openai import OpenAI
import jsonl, json

client = OpenAI()

# Prepare batch requests as a JSONL file
requests = [
    {
        "custom_id": f"request-{i}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": f"Summarize: {doc}"}],
            "max_tokens": 200
        }
    }
    for i, doc in enumerate(documents)
]

# Write to JSONL
with open("batch_input.jsonl", "w") as f:
    for req in requests:
        f.write(json.dumps(req) + "\n")

# Upload and submit
batch_file = client.files.create(
    file=open("batch_input.jsonl", "rb"),
    purpose="batch"
)

batch = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch ID: {batch.id}, Status: {batch.status}")
# Cost: 50% less than synchronous API
```

### Anthropic Message Batches API

```python
from anthropic import Anthropic
import anthropic

client = Anthropic()

batch = client.messages.batches.create(
    requests=[
        anthropic.types.message_create_params.Request(
            custom_id=f"doc-{i}",
            params=anthropic.types.MessageCreateParamsNonStreaming(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": f"Classify topic: {doc}"}]
            )
        )
        for i, doc in enumerate(documents)
    ]
)

print(f"Batch: {batch.id}")

# Poll for completion (or use webhooks)
import time
while True:
    status = client.messages.batches.retrieve(batch.id)
    if status.processing_status == "ended":
        break
    time.sleep(60)

# Retrieve results
for result in client.messages.batches.results(batch.id):
    print(result.custom_id, result.result.message.content[0].text)
```

### Micro-Batching for Real-Time Systems

Even in low-latency systems, you can batch requests that arrive within a short window:

```python
import asyncio
from collections import defaultdict

class MicroBatcher:
    def __init__(self, window_ms: int = 50, max_batch_size: int = 20):
        self.window_ms = window_ms
        self.max_batch_size = max_batch_size
        self._queue: list = []
        self._futures: list = []
        self._lock = asyncio.Lock()
        self._flush_task = None

    async def submit(self, prompt: str) -> str:
        future = asyncio.get_event_loop().create_future()
        async with self._lock:
            self._queue.append(prompt)
            self._futures.append(future)
            if len(self._queue) == 1:
                self._flush_task = asyncio.create_task(self._delayed_flush())
            elif len(self._queue) >= self.max_batch_size:
                self._flush_task.cancel()
                await self._flush()
        return await future

    async def _delayed_flush(self):
        await asyncio.sleep(self.window_ms / 1000)
        await self._flush()

    async def _flush(self):
        async with self._lock:
            if not self._queue:
                return
            batch, futures = self._queue[:], self._futures[:]
            self._queue.clear()
            self._futures.clear()
        results = await self._call_model_batch(batch)
        for future, result in zip(futures, results):
            future.set_result(result)

    async def _call_model_batch(self, prompts: list) -> list:
        # Implement actual parallel API calls here
        pass
```

---

## Fine-Tuning vs. Prompting Trade-offs

Fine-tuning a smaller model can dramatically cut costs for high-volume, narrow-scope tasks — but it comes with upfront investment and maintenance overhead.

### Cost Comparison

```
Scenario: 10M requests/month, sentiment classification

Option A: GPT-4o with few-shot prompting
  Input:  ~500 tokens × 10M = 5B tokens → $15,000/month
  Output: ~50 tokens × 10M  = 500M tokens → $6,000/month
  Total: ~$21,000/month

Option B: Fine-tuned GPT-4o-mini
  Fine-tuning cost (one-time): ~$500
  Input:  ~50 tokens × 10M = 500M tokens → $200/month
  Output: ~10 tokens × 10M = 100M tokens → $120/month
  Total: ~$320/month + $500 one-time

Savings: $20,680/month after break-even (~day 1)
```

### Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│            Fine-Tune or Prompt?                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Task is well-defined and narrow?          ──Yes──►  Fine-tune  │
│  Volume > 100K requests/month?             ──Yes──►  Fine-tune  │
│  Task requires specialized style/format?   ──Yes──►  Fine-tune  │
│  Have 500+ labeled examples?               ──Yes──►  Fine-tune  │
│                                                                  │
│  Task changes frequently?                  ──Yes──►  Prompt     │
│  Low volume (<10K/month)?                  ──Yes──►  Prompt     │
│  Need general reasoning capability?        ──Yes──►  Prompt     │
│  No labeled data available?                ──Yes──►  Prompt     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fine-Tuning with OpenAI

```python
from openai import OpenAI
import json

client = OpenAI()

# Prepare training data
training_data = [
    {"messages": [
        {"role": "system", "content": "Classify sentiment as positive/negative/neutral."},
        {"role": "user", "content": "This product is amazing!"},
        {"role": "assistant", "content": "positive"}
    ]},
    # ... hundreds more examples
]

with open("train.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")

# Upload training file
train_file = client.files.create(file=open("train.jsonl", "rb"), purpose="fine-tune")

# Start fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=train_file.id,
    model="gpt-4o-mini",
    hyperparameters={"n_epochs": 3}
)

print(f"Fine-tune job: {job.id}")
# Once complete, use: model="ft:gpt-4o-mini:org:name:id"
```

### Distillation: Use a Large Model to Train a Small One

```python
# Step 1: Generate high-quality outputs with a large model
teacher_outputs = []
for prompt in training_prompts:
    response = client.chat.completions.create(
        model="gpt-4o",           # Expensive teacher model
        messages=[{"role": "user", "content": prompt}]
    )
    teacher_outputs.append({
        "prompt": prompt,
        "output": response.choices[0].message.content
    })

# Step 2: Fine-tune a small model on these outputs
# The small model learns to mimic the large model's behavior
# at 10-100x lower inference cost
```

---

## Cost Optimization Decision Tree

Use this when deciding which optimization to apply first:

```
Start: Are costs too high?
│
├─► Is cache hit rate < 30%?
│      YES → Implement semantic cache or restructure prompts for provider caching
│      NO  → Continue
│
├─► Are prompts longer than 500 tokens on average?
│      YES → Compress prompts; move stable content to cached prefix
│      NO  → Continue
│
├─► Are output tokens > 3× input tokens?
│      YES → Add brevity instructions; use structured output (JSON mode)
│      NO  → Continue
│
├─► Is one model used for ALL tasks?
│      YES → Implement model routing (small model for simple tasks)
│      NO  → Continue
│
├─► Is this a batch/offline workload?
│      YES → Switch to Batch API (50% cost reduction instantly)
│      NO  → Continue
│
├─► Volume > 1M requests/month on a narrow task?
│      YES → Fine-tune a smaller model; consider self-hosting
│      NO  → Continue
│
└─► Have you set per-user and daily budget limits?
       NO  → Implement BudgetManager immediately
       YES → Audit top-cost users/endpoints; optimize those first
```

### Quick Wins vs. Strategic Investments

| Optimization | Effort | Impact | Time to Value |
|-------------|--------|--------|---------------|
| Set `max_tokens` explicitly | Minutes | Medium | Immediate |
| Add brevity instructions | Minutes | Medium | Immediate |
| Provider prompt caching | Hours | High | Same day |
| Semantic cache | Days | High | Same day |
| Model routing | Days | High | Same day |
| Switch to Batch API | Hours | 50% cost cut | Same day |
| Fine-tune small model | Weeks | Very High | After break-even |
| Self-host open-source model | Months | Very High | Long-term |

---

## Best Practices

1. **Start with Caching**: Biggest ROI for minimal effort — semantic cache + provider-native prompt caching together can cut 40–70% of costs
2. **Control Output Length**: Output tokens cost 3–5× more; add brevity instructions and set `max_tokens` on every call
3. **Use Structured Outputs**: JSON mode eliminates conversational filler, reducing output tokens by 30–50%
4. **Enable Provider Prompt Caching**: Structure prompts with stable content first; cache large system prompts and reference documents
5. **Route to the Right Model**: Don't use a flagship model for classification or simple Q&A — use model routing
6. **Batch Offline Workloads**: Any non-real-time processing (labeling, bulk generation, evals) should use the Batch API for 50% savings
7. **Set Budgets Early**: Implement per-user and daily/monthly limits before production traffic hits — not after a surprise bill
8. **Monitor Continuously**: Track cost by model, endpoint, and user — anomalies are invisible without observability
9. **Fine-Tune at Scale**: If a single narrow task exceeds 500K requests/month, fine-tuning a small model almost always pays off within days
10. **Consider Self-Hosting**: At very high volume (>100M tokens/month), open-source models (LLaMA, Mistral) on your own GPU fleet can cut costs by 80–90%
11. **Audit Regularly**: Run monthly cost reviews — prompt patterns drift over time, and yesterday's optimized prompt may be today's bloat

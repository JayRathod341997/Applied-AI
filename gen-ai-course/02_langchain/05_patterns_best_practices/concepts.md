# Patterns and Best Practices Concepts

## Error Handling

### Retry Logic
```python
from langchain.callbacks import RetryHandler
from langchain.schema import HumanMessage

retry_handler = RetryHandler(max_attempts=3)
```

### Fallback Chains
```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

fallback_prompt = PromptTemplate(template="{input}")
fallback_chain = LLMChain(llm=fallback_llm, prompt=fallback_prompt)
```

## Caching

### LLM Cache
```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

### Semantic Cache
```python
from langchain.cache import SemanticCache
set_llm_cache(SemanticCache())
```

## Production Patterns

1. **Circuit Breaker**: Prevent cascade failures
2. **Rate Limiting**: Control API usage
3. **Timeout Handling**: Prevent hanging requests
4. **Logging and Monitoring**: Track performance
5. **Graceful Degradation**: Continue on failures

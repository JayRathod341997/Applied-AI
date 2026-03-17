# Building Blocks Concepts

## Overview

LangChain provides several fundamental building blocks that form the foundation of any LLM application.

## 1. Chat Models

Chat models are the core of LangChain applications:

### Types of Chat Models

```python
# OpenAI Chat
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Anthropic Chat
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-opus")

# Azure OpenAI
from langchain_openai import AzureChatOpenAI
llm = AzureChatOpenAI()
```

### Key Parameters

- **temperature**: Controls randomness (0-2)
- **max_tokens**: Maximum tokens in response
- **model_name**: Which model to use
- **streaming**: Enable streaming responses

## 2. Prompt Templates

Prompt templates create reusable, parameterized prompts:

### String Prompt Template

```python
from langchain.prompts import PromptTemplate

template = PromptTemplate.from_template(
    "Tell me a {adjective} joke about {topic}"
)
```

### Chat Prompt Template

```python
from langchain.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "You are a {role} assistant."),
    ("human", "{user_input}")
])
```

## 3. Output Parsers

Output parsers transform LLM responses into usable formats:

### String Output Parser

```python
from langchain.schema import StrOutputParser
parser = StrOutputParser()
```

### JSON Parser

```python
from langchain.output_parsers import JsonOutputParser
parser = JsonOutputParser()
```

### Pydantic Parser

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    confidence: float

parser = PydanticOutputParser(pydantic_object=Response)
```

## 4. Chains

Chains combine components together:

### LCEL (LangChain Expression Language)

```python
chain = prompt | llm | parser
```

### Common Chain Types

- **LLMChain**: Basic prompt + LLM
- **SequentialChain**: Multiple chains in sequence
- **RouterChain**: Route to different chains
- **RetrievalQA**: RAG chain

## 5. Working with Messages

### Message Types

```python
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is AI?"),
    AIMessage(content="AI is...")
]
```

## 6. Caching

Reduce costs and improve speed:

```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

## 7. Streaming

Real-time response streaming:

```python
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="")
```

## Summary

These building blocks can be combined in countless ways to create powerful LLM applications:
- Chat models as the engine
- Prompt templates for reusability
- Output parsers for structured data
- Chains for workflow orchestration

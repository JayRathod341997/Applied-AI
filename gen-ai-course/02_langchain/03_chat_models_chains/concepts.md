# Chat Models and Chains Concepts

## Chat Models

### Supported Providers

```python
# OpenAI
from langchain_openai import ChatOpenAI

# Anthropic
from langchain_anthropic import ChatAnthropic

# Azure OpenAI
from langchain_openai import AzureChatOpenAI

# Google Vertex AI
from langchain_google_vertexai import ChatVertexAI

# HuggingFace
from langchain_huggingface import ChatHuggingFace
```

### Configuration Options

```python
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
    streaming=True,
    callbacks=[callback_handler]
)
```

## Chain Types

### 1. LLMChain

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate.from_template("{topic} summary")
chain = LLMChain(llm=llm, prompt=prompt)
```

### 2. SequentialChain

```python
from langchain.chains import SequentialChain

chain = SequentialChain(
    chains=[chain1, chain2, chain3],
    input_variables=["input"],
    output_variables=["final_output"]
)
```

### 3. RouterChain

```python
from langchain.chains import RouterChain
from langchain.chains.llm import LLMChain

# Define destination chains
physics_chain = LLMChain(llm=llm, prompt=physics_prompt)
math_chain = LLMChain(llm=llm, prompt=math_prompt)

# Create router
router_chain = RouterChain(
    default_chain=default_chain,
    destination_chains={"physics": physics_chain, "math": math_chain}
)
```

### 4. Transformation Chain

```python
from langchain.chains import TransformChain

def transform_func(inputs):
    return {"output": inputs["input"].upper()}

transform_chain = TransformChain(
    input_variables=["input"],
    output_variables=["output"],
    transform=transform_func
)
```

## Chain Composition with LCEL

```python
# Simple chain
chain = prompt | llm | parser

# With transformation
chain = (
    {"topic": lambda x: x["topic"]}
    | prompt
    | llm
    | parser
)
```

## Best Practices

1. Use LCEL for new code
2. Add error handling
3. Implement caching for expensive operations
4. Use streaming for better UX
5. Monitor token usage

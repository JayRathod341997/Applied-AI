# Concepts: Agentic AI Design Patterns

## 1. Reactive vs Planning Agents

### Reactive Agents
Reactive agents respond directly to stimuli without maintaining internal state or planning ahead. They follow simple stimulus-response rules.

**Characteristics:**
- Fast response times
- Simple implementation
- No long-term planning
- Limited to well-defined scenarios

**Example:**
```
IF user asks about hours THEN respond with store hours
IF user asks about location THEN respond with address
```

### Planning Agents
Planning agents maintain internal models, consider future states, and develop step-by-step plans to achieve goals.

**Characteristics:**
- Can handle complex, multi-step tasks
- Maintains goal state
- Can replan when conditions change
- More sophisticated decision making

**Example:**
```
Goal: Book flight to NYC
1. Check available flights
2. Compare prices
3. Select best option
4. Book ticket
5. Send confirmation
```

### When to Use Each

| Scenario | Agent Type |
|----------|------------|
| Simple FAQ | Reactive |
| Customer support triage | Reactive |
| Complex research task | Planning |
| Multi-step workflows | Planning |
| Real-time monitoring | Reactive |

## 2. Reflection Patterns

Reflection allows agents to evaluate their own outputs and improve over time.

### Types of Reflection

1. **Self-Correction**: Identify and fix errors in reasoning
2. **Quality Assessment**: Evaluate output quality
3. **Strategy Adjustment**: Modify approach based on results

### Implementation

```python
class ReflectiveAgent:
    def reflect(self, output, context):
        # Check for errors
        if self.has_errors(output):
            return self.correct(output)
        
        # Assess quality
        quality = self.assess_quality(output)
        if quality < threshold:
            return self.improve(output)
        
        return output
```

## 3. Tools and Tool Integration

Tools extend agent capabilities beyond text generation.

### Tool Design Principles

1. **Single Responsibility**: Each tool does one thing well
2. **Clear Inputs/Outputs**: Well-defined interfaces
3. **Error Handling**: Graceful failure modes

### Tool Types

- **Information Retrieval**: Search, Database queries
- **Computation**: Calculator, Code execution
- **External APIs**: Weather, Stocks, News
- **File Operations**: Read, Write, List

## 4. Memory Patterns

### Buffer Memory
Stores the most recent interactions verbatim.

```python
BufferMemory(capacity=10)  # Last 10 messages
```

### Sliding Window Memory
Maintains a fixed-size window of recent context.

```python
SlidingWindowMemory(window_size=5)
```

### Summary Memory
Compresses older interactions into summaries.

```python
SummaryMemory(
    initial_summary="User preferences: ...",
    max_tokens=500
)
```

### Vector Memory
Uses embeddings to retrieve relevant past context.

```python
VectorMemory(
    embedding_function=embed_fn,
    search_top_k=3
)
```

### Scratchpad
Temporary working memory for intermediate calculations.

### Shared Memory
Allows multiple agents to share context.

## 5. Planning-ReAct Pattern

ReAct (Reasoning + Acting) combines reasoning traces with actions.

### ReAct Loop

1. **Thought**: Reason about the current situation
2. **Action**: Execute an action
3. **Observation**: Observe the result
4. **Repeat**: Continue until goal is achieved

### Example

```
Thought: I need to find the current weather in London
Action: call_weather_api(city="London")
Observation: 18°C, partly cloudy
Thought: The weather is nice, I should suggest outdoor activities
Action: generate_suggestions(weather="good")
...
```

# Module 2: LangChain Framework — Quiz

## Instructions
Choose the best answer for each question. Answers and explanations are provided at the end of each section.

---

## Questions 1-5: LangChain Basics

### Q1. What is the primary purpose of LangChain?
- A) To train custom LLMs from scratch
- B) To provide a framework for building LLM-powered applications
- C) To replace LLM APIs with local models
- D) To fine-tune existing language models

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** LangChain is a framework that provides abstractions and tools for building applications powered by Large Language Models. It does not train models but helps compose them into workflows with memory, tools, and data sources.
</details>

---

### Q2. Which of the following is NOT a core component of LangChain?
- A) Prompts
- B) Chains
- C) Database ORM
- D) Memory

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** Database ORM is not a core component of LangChain. The core components include Models, Prompts, Output Parsers, Indexes, Chains, Memory, Agents, and Callbacks.
</details>

---

### Q3. What does LCEL stand for in LangChain?
- A) LangChain Execution Layer
- B) LangChain Expression Language
- C) Large Chain Element Library
- D) Language Chain Extension Layer

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** LCEL stands for LangChain Expression Language. It is the declarative syntax using the pipe (`|`) operator for composing chains with built-in streaming, async, and parallel execution support.
</details>

---

### Q4. Which operator is used to compose chains in LCEL?
- A) `>>`
- B) `->`
- C) `|`
- D) `&&`

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** The pipe operator (`|`) is used to compose chains in LCEL. For example: `chain = prompt | model | parser`.
</details>

---

### Q5. What is the correct way to install LangChain with OpenAI support?
- A) `pip install langchain-openai`
- B) `pip install langchain langchain-openai`
- C) `pip install langchain[openai]`
- D) Both A and B

<details>
<summary><strong>Answer: D</strong></summary>

**Explanation:** You can install `langchain-openai` directly (which pulls in `langchain-core` as a dependency), or install both `langchain` and `langchain-openai` together for full functionality.
</details>

---

## Questions 6-10: Prompts and Parsers

### Q6. Which class is used to create a chat-based prompt template?
- A) `PromptTemplate`
- B) `ChatPromptTemplate`
- C) `MessagePromptTemplate`
- D) `LLMPromptTemplate`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `ChatPromptTemplate` is used for chat models and accepts a list of message tuples like `("system", "...")` and `("human", "...")`. `PromptTemplate` is for text completion models.
</details>

---

### Q7. What does `JsonOutputParser` do?
- A) Converts JSON to natural language
- B) Parses LLM output into JSON format
- C) Validates JSON schemas
- D) Compresses JSON responses

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `JsonOutputParser` extracts and parses JSON-structured output from LLM responses. It can be configured with a Pydantic model to enforce a specific output schema.
</details>

---

### Q8. Which method is used to get format instructions for a `JsonOutputParser`?
- A) `get_instructions()`
- B) `get_format_instructions()`
- C) `format_schema()`
- D) `get_schema()`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `parser.get_format_instructions()` returns a string that should be included in the prompt to instruct the LLM on how to format its output as valid JSON matching the specified schema.
</details>

---

### Q9. What is the purpose of few-shot prompting in LangChain?
- A) To reduce the number of API calls
- B) To provide examples that guide the model's behavior
- C) To cache previous responses
- D) To validate model outputs

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Few-shot prompting provides input-output examples to the model, helping it understand the expected pattern or format. In LangChain, this is done using `FewShotChatMessagePromptTemplate`.
</details>

---

### Q10. Which output parser returns a Python list from comma-separated text?
- A) `StrOutputParser`
- B) `JsonOutputParser`
- C) `ListOutputParser`
- D) `CommaSeparatedListOutputParser`

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** `ListOutputParser` (or `CommaSeparatedListOutputParser`) parses comma-separated values from LLM output into a Python list.
</details>

---

## Questions 11-15: Chains and Models

### Q11. What is the key advantage of using LCEL over legacy `LLMChain`?
- A) It requires fewer imports
- B) It has built-in streaming, async, and parallel execution
- C) It supports more model providers
- D) It is faster at token generation

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** LCEL provides built-in support for streaming (`stream()`), async execution (`ainvoke()`), parallel execution (`RunnableParallel`), fallbacks, and retries — features that legacy `LLMChain` lacks.
</details>

---

### Q12. Which method enables streaming with an LCEL chain?
- A) `chain.invoke()`
- B) `chain.stream()`
- C) `chain.generate()`
- D) `chain.async()`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `chain.stream()` returns an iterator that yields chunks of the response as they are generated, enabling real-time output display.
</details>

---

### Q13. What is the difference between `ChatOpenAI` and `OpenAI` in LangChain?
- A) `ChatOpenAI` is for chat models, `OpenAI` is for text completion models
- B) `ChatOpenAI` is faster
- C) `OpenAI` is deprecated
- D) There is no difference

<details>
<summary><strong>Answer: A</strong></summary>

**Explanation:** `ChatOpenAI` wraps chat-based models (like GPT-4) that accept message lists, while `OpenAI` wraps text completion models (like text-davinci-003) that accept plain text strings.
</details>

---

### Q14. What does the `temperature` parameter control in an LLM?
- A) The speed of response generation
- B) The creativity/randomness of the output
- C) The maximum token count
- D) The number of retries

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Temperature controls the randomness of the output. Lower values (near 0) produce deterministic, focused responses. Higher values (near 1) produce more creative, varied responses.
</details>

---

### Q15. How do you run multiple chains in parallel using LCEL?
- A) `chain.run_parallel()`
- B) `RunnableParallel({...})`
- C) `asyncio.run(chain)`
- D) `chain.parallel_invoke()`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `RunnableParallel` executes multiple runnables concurrently and combines their results into a single dictionary. Example: `RunnableParallel({"a": chain_a, "b": chain_b})`.
</details>

---

## Questions 16-20: Memory, Tools, and Agents

### Q16. Which memory type summarizes the conversation to save tokens?
- A) `ConversationBufferMemory`
- B) `ConversationBufferWindowMemory`
- C) `ConversationSummaryMemory`
- D) `VectorStoreRetrieverMemory`

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** `ConversationSummaryMemory` uses an LLM to generate a running summary of the conversation, reducing token consumption compared to storing all raw messages.
</details>

---

### Q17. What does the `k` parameter in `ConversationBufferWindowMemory` control?
- A) The number of tokens to store
- B) The number of recent conversation exchanges to keep
- C) The number of tools available
- D) The number of retries

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** The `k` parameter specifies how many recent conversation exchanges (turns) to retain in memory. Older exchanges are discarded.
</details>

---

### Q18. How do you define a tool in LangChain?
- A) By creating a class that inherits from `BaseTool`
- B) By using the `@tool` decorator on a function
- C) Both A and B
- D) By registering it in a config file

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** Tools can be defined either by decorating a function with `@tool` (simpler) or by creating a class that inherits from `BaseTool` (more control, supports async).
</details>

---

### Q19. What is the role of `AgentExecutor`?
- A) It trains the agent
- B) It runs the agent loop: decide action → execute tool → repeat
- C) It stores agent memory
- D) It validates tool outputs

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `AgentExecutor` is the runtime that orchestrates the agent loop: it passes input to the agent, executes chosen tools, feeds results back, and repeats until a final answer is produced.
</details>

---

### Q20. Which agent type uses the Reasoning + Acting pattern?
- A) Tool Calling Agent
- B) ReAct Agent
- C) Plan-and-Execute Agent
- D) Self-Ask Agent

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** The ReAct (Reasoning + Acting) agent alternates between thinking about what to do (Thought) and taking actions (Action/Observation) until it reaches a final answer.
</details>

---

## Questions 21-25: Best Practices and Advanced Topics

### Q21. What is the purpose of `.with_fallbacks()` in LCEL?
- A) To retry failed requests
- B) To try alternative chains if the primary one fails
- C) To cache responses
- D) To parallelize execution

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `.with_fallbacks()` specifies alternative chains to try if the primary chain fails. This enables graceful degradation in production applications.
</details>

---

### Q22. Which callback method fires when an LLM finishes generating a response?
- A) `on_llm_start()`
- B) `on_llm_end()`
- C) `on_llm_error()`
- D) `on_chain_end()`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `on_llm_end()` is called when the LLM completes generation. It receives the full response including token usage information.
</details>

---

### Q23. What is the recommended way to handle API keys in a LangChain application?
- A) Hardcode them in the source code
- B) Store them in environment variables or `.env` files
- C) Pass them as command-line arguments
- D) Store them in a public config file

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** API keys should be stored in environment variables or `.env` files (loaded with `python-dotenv`) to prevent accidental exposure in source code or version control.
</details>

---

### Q24. What does `RecursiveCharacterTextSplitter` do?
- A) Splits text by character count only
- B) Splits text recursively using a list of separators
- C) Removes special characters from text
- D) Converts text to lowercase

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `RecursiveCharacterTextSplitter` splits text by trying separators in order (e.g., `\n\n`, `\n`, ` `, ``), keeping chunks under the specified size while preserving semantic boundaries.
</details>

---

### Q25. What is `VectorStoreRetrieverMemory` used for?
- A) Storing conversation in a SQL database
- B) Retrieving relevant past conversations using semantic search
- C) Caching LLM responses
- D) Summarizing long conversations

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `VectorStoreRetrieverMemory` stores conversation history as embeddings in a vector store and retrieves the most semantically relevant past exchanges for the current query.
</details>

---

## Questions 26-30: Practical Scenarios

### Q26. You need to build a chatbot that remembers the last 10 exchanges. Which memory type should you use?
- A) `ConversationBufferMemory`
- B) `ConversationBufferWindowMemory` with `k=10`
- C) `ConversationSummaryMemory`
- D) `VectorStoreRetrieverMemory`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `ConversationBufferWindowMemory` with `k=10` keeps exactly the last 10 conversation exchanges, providing bounded memory that prevents token overflow.
</details>

---

### Q27. Your LLM chain occasionally fails due to rate limiting. What is the best solution?
- A) Increase the temperature
- B) Use `.with_retry()` with exponential backoff
- C) Switch to a different model provider
- D) Reduce the prompt length

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `.with_retry()` with exponential backoff automatically retries failed requests with increasing delays, which is the standard approach for handling rate limits.
</details>

---

### Q28. You want to extract structured data (name, age, email) from unstructured text. Which approach is best?
- A) Use `StrOutputParser`
- B) Use `JsonOutputParser` with a Pydantic model
- C) Use regex on the LLM output
- D) Use `ListOutputParser`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `JsonOutputParser` with a Pydantic model provides the most reliable structured extraction, as it instructs the LLM to output valid JSON matching your schema and parses it automatically.
</details>

---

### Q29. Which component would you use to process a 50-page document that exceeds the LLM's context window?
- A) `ConversationBufferMemory`
- B) `RecursiveCharacterTextSplitter` + Map-Reduce chain
- C) `StrOutputParser`
- D) `AgentExecutor`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Split the document using `RecursiveCharacterTextSplitter`, process each chunk with a map step (summarize/extract), then combine results with a reduce step.
</details>

---

### Q30. You want to run sentiment analysis, keyword extraction, and summarization on the same text. What is the most efficient approach?
- A) Run three separate chains sequentially
- B) Use `RunnableParallel` to run all three simultaneously
- C) Use a single prompt for all three tasks
- D) Use an agent with three tools

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `RunnableParallel` executes independent chains concurrently, reducing total latency compared to sequential execution. Each task runs in parallel and results are combined at the end.
</details>

---

## Score Reference

| Score | Level |
|-------|-------|
| 27-30 | Expert — Ready for advanced LangChain and LangGraph |
| 22-26 | Proficient — Solid understanding of core concepts |
| 16-21 | Intermediate — Review weak areas and practice |
| 0-15 | Beginner — Revisit the concepts material |

---

## Bonus: Senior / JD-Aligned Questions (LlamaIndex vs LangChain)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. Your core problem is ingesting, indexing, and retrieving over a large private document set with minimal orchestration glue. Which framework is the most natural fit?

A) LangChain — for its agent abstractions  
B) LlamaIndex — a data/retrieval-first framework  
C) Neither; you must use raw SDK calls  
D) A general web framework like FastAPI  

**Answer: B** — LlamaIndex is built around ingest→index→retrieve; LangChain shines when you also need general agent/tool orchestration.

### BQ2. What is the strongest reason to drop a framework and use the provider SDK directly?

A) Frameworks can never stream responses  
B) A latency/cost-critical hot path where abstraction overhead and opacity hurt control and auditability  
C) The SDK is always fewer lines of code  
D) Frameworks cannot call external tools  

**Answer: B** — on hot paths you often want full control of prompts, tokens, retries, and streaming, and transparent behavior for audit.

### BQ3. What does LangChain's LCEL primarily provide?

A) A vector database  
B) Declarative composition with streaming, async, batching, and fallbacks  
C) A fine-tuning service  
D) A replacement for Python itself  

**Answer: B** — LCEL composes pipeline steps declaratively and adds cross-cutting features for free.

### BQ4. Which ordering correctly describes a LlamaIndex RAG pipeline?

A) Index → Documents → Query engine → Nodes  
B) Documents → Nodes → Index → Retriever → Postprocessor → Response synthesizer  
C) Retriever → Documents → Index → Nodes  
D) Query engine → Index → Documents  

**Answer: B** — documents are parsed into nodes, indexed, retrieved, post-processed (e.g. re-ranked), then synthesized into a response.

### BQ5. What is the best practice for limiting framework lock-in?

A) Never pin versions so you always get the latest  
B) Wrap the framework behind your own interface, pin versions, and evaluate upgrades against your own benchmarks  
C) Fork the framework and maintain it yourself  
D) Avoid frameworks entirely in all cases  

**Answer: B** — an adapter layer plus pinned versions keeps you able to upgrade, swap, or drop the framework on your terms.

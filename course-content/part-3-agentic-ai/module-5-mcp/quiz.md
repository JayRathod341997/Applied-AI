# Module 5: Model Context Protocol (MCP) — Quiz

## Instructions
Select the best answer for each question. Answers and explanations are provided at the end.

---

## Questions

### Q1: What protocol does MCP use for communication between clients and servers?

A) gRPC
B) JSON-RPC 2.0
C) GraphQL
D) REST

---

### Q2: Which of the following is NOT one of the three core MCP primitives?

A) Resources
B) Tools
C) Prompts
D) Agents

---

### Q3: Which transport mechanism is best suited for local process communication in MCP?

A) HTTP/SSE
B) WebSocket
C) stdio
D) TCP

---

### Q4: During the MCP initialization handshake, what does the client send first?

A) `tools/list` request
B) `initialize` request with capabilities
C) `initialized` notification
D) `tools/call` request

---

### Q5: What is the purpose of the `listChanged` capability in MCP?

A) To enable real-time streaming of tool outputs
B) To allow servers to notify clients when tools/resources/prompts change
C) To enable bidirectional RPC calls
D) To compress data during transmission

---

### Q6: In an MCP server, how is tool input validated?

A) Through manual validation in the tool handler
B) Through JSON Schema defined in the tool's `inputSchema`
C) Through external validation middleware only
D) MCP does not support input validation

---

### Q7: Which MCP primitive represents read-only data sources?

A) Tools
B) Prompts
C) Resources
D) Streams

---

### Q8: What happens when a client subscribes to a resource in MCP?

A) The client can modify the resource
B) The server sends notifications when the resource content changes
C) The resource is cached on the client side
D) The client gains write access to the resource

---

### Q9: Which of the following is a security best practice for MCP servers?

A) Expose all tools without authentication
B) Allow unrestricted SQL queries through tools
C) Enforce read-only defaults and validate all inputs
D) Store API keys in tool output responses

---

### Q10: What is the primary advantage of MCP over custom tool integrations?

A) Faster execution speed
B) Standardized protocol enabling interoperability across vendors
C) Built-in LLM inference capabilities
D) Automatic code generation

---

### Q11: In TypeScript MCP server implementation, what library is commonly used for schema validation?

A) Joi
B) Yup
C) Zod
D) Ajv

---

### Q12: Can an MCP client connect to multiple servers simultaneously?

A) No, only one server connection is allowed
B) Yes, but only with stdio transport
C) Yes, each connection has its own transport and session
D) Only if all servers are on the same host

---

### Q13: Which integration pattern involves an MCP server running alongside the main application?

A) Gateway
B) Mesh
C) Sidecar
D) Proxy

---

### Q14: What type of content can an MCP tool return?

A) Only text
B) Text, images, and resource references
C) Only JSON objects
D) Only binary data

---

### Q15: In an enterprise MCP architecture, what component routes client requests to appropriate backend servers?

A) MCP Host
B) MCP Gateway
C) MCP Registry
D) MCP Proxy

---

## Answers and Explanations

### Q1: Answer — B) JSON-RPC 2.0
**Explanation:** MCP uses JSON-RPC 2.0 as its messaging protocol. All requests, responses, and notifications follow the JSON-RPC 2.0 specification with standard fields like `jsonrpc`, `id`, `method`, and `params`.

---

### Q2: Answer — D) Agents
**Explanation:** The three core MCP primitives are Resources (read-only data), Tools (executable functions), and Prompts (reusable templates). Agents are not a primitive in the MCP protocol.

---

### Q3: Answer — C) stdio
**Explanation:** stdio (standard input/output) is designed for local process communication where the MCP server runs as a child process of the client. It provides the lowest latency for local integrations.

---

### Q4: Answer — B) `initialize` request with capabilities
**Explanation:** The handshake begins with the client sending an `initialize` request containing its protocol version, capabilities, and client info. The server responds with its own capabilities, and then the client sends an `initialized` notification to complete the handshake.

---

### Q5: Answer — B) To allow servers to notify clients when tools/resources/prompts change
**Explanation:** When a server declares `listChanged: true` for a capability, it can send notifications (e.g., `notifications/tools/list_changed`) to inform connected clients that the available list has been updated, prompting clients to re-fetch the list.

---

### Q6: Answer — B) Through JSON Schema defined in the tool's `inputSchema`
**Explanation:** MCP tools define their expected input structure using JSON Schema in the `inputSchema` field. The MCP SDK automatically validates incoming arguments against this schema before passing them to the tool handler.

---

### Q7: Answer — C) Resources
**Explanation:** Resources represent read-only data sources that clients can discover and read. They are identified by URIs and can represent files, database tables, API endpoints, or any other data source.

---

### Q8: Answer — B) The server sends notifications when the resource content changes
**Explanation:** Resource subscriptions enable a publish-subscribe pattern where the server notifies subscribed clients when a resource's content changes. Clients can then re-read the updated resource.

---

### Q9: Answer — C) Enforce read-only defaults and validate all inputs
**Explanation:** Security best practices for MCP servers include enforcing read-only operations by default, validating all tool inputs against schemas, implementing authentication/authorization, rate limiting, and never exposing secrets in tool outputs.

---

### Q10: Answer — B) Standardized protocol enabling interoperability across vendors
**Explanation:** MCP's primary advantage is providing a universal standard so that tools built for one MCP-compatible client work with any other MCP-compatible client, eliminating the need for custom integrations per platform.

---

### Q11: Answer — C) Zod
**Explanation:** The TypeScript MCP SDK uses Zod for schema validation. Zod schemas provide type-safe validation and inference, ensuring tool arguments match expected types at both compile-time and runtime.

---

### Q12: Answer — C) Yes, each connection has its own transport and session
**Explanation:** An MCP client can maintain independent connections to multiple servers. Each connection has its own transport layer (stdio, SSE, etc.) and ClientSession, allowing the client to discover and use tools from different servers simultaneously.

---

### Q13: Answer — C) Sidecar
**Explanation:** The sidecar pattern involves running an MCP server alongside the main application process, providing local tool access. This is common in desktop applications and local agent setups where low latency is important.

---

### Q14: Answer — B) Text, images, and resource references
**Explanation:** MCP tools can return multiple content types: text content (most common), image content (with MIME type), and resource references (pointing to data accessible through the resources API).

---

### Q15: Answer — B) MCP Gateway
**Explanation:** In enterprise architectures, an MCP Gateway acts as a central routing layer that receives client requests and routes them to the appropriate backend MCP servers based on tool names, resource URIs, or other routing logic. It also handles authentication, rate limiting, and audit logging.

---

## Score Reference

| Score | Level |
|-------|-------|
| 13-15 | Excellent — Strong MCP understanding |
| 10-12 | Good — Solid knowledge with minor gaps |
| 7-9 | Fair — Review concepts.md for details |
| 0-6 | Needs Improvement — Re-read the full module |


---

## Bonus: Senior / JD-Aligned Questions (MCP for Enterprise Integration)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the primary value of MCP?

A) It fine-tunes models  
B) A standard protocol that decouples LLM hosts from tool/data integrations — build a server once, reuse across clients  
C) It is a vector database  
D) It replaces Python  

**Answer: B** — MCP avoids N×M bespoke integrations by standardizing how hosts talk to tools and data.

### BQ2. Which three primitives does an MCP server expose?

A) Tables, rows, columns  
B) Resources, tools, and prompts  
C) GET, POST, DELETE  
D) Train, validate, test  

**Answer: B** — resources (data/context), tools (actions), and prompts (templates).

### BQ3. What is the biggest security concern when MCP tool results are fed back to the model?

A) Slow networking  
B) Prompt injection via tool output — so sanitize results, use least privilege, and require human approval  
C) Excessive logging  
D) Tool results are always safe  

**Answer: B** — a tool can return attacker-controlled text that hijacks the model; treat tool output as untrusted input.

### BQ4. When should you choose MCP over plain in-app function calling?

A) When you never use tools  
B) When integrations should be reusable and shareable across multiple AI clients or teams  
C) Only for local scripts  
D) Only when using a vector DB  

**Answer: B** — MCP's decoupling pays off when the same integration must serve many hosts.

### BQ5. Who originated MCP, and what is its portability benefit?

A) A database vendor; it locks you in  
B) Anthropic; an open standard so one server works across Claude and other MCP-capable hosts  
C) It has no defined origin  
D) A single closed-source IDE  

**Answer: B** — MCP is Anthropic's open standard, giving cross-host portability rather than single-vendor lock-in.

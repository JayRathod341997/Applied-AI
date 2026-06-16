# Module 5: Model Context Protocol (MCP) — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level)
- [Intermediate Level](#intermediate-level)
- [Advanced Level](#advanced-level)

---

## Beginner Level

### Q1: What is the Model Context Protocol (MCP)?

**Answer:** MCP is an open standard protocol developed by Anthropic that provides a unified interface for AI models and applications to interact with external tools, data sources, and services. It standardizes how LLMs discover, describe, and invoke external capabilities through a client-server architecture using JSON-RPC 2.0.

### Q2: What are the three core primitives in MCP?

**Answer:**
- **Resources** - Read-only data sources that clients can access (files, databases, API responses)
- **Tools** - Executable functions that perform actions (queries, computations, API calls)
- **Prompts** - Reusable prompt templates with parameterized arguments

### Q3: What transport mechanisms does MCP support?

**Answer:** MCP supports three transport mechanisms:
- **stdio** - Standard input/output for local process communication
- **HTTP/SSE** - HTTP with Server-Sent Events for remote connections
- **WebSocket** - Real-time bidirectional communication

### Q4: What RPC framework does MCP use?

**Answer:** MCP uses JSON-RPC 2.0 as its messaging protocol. All requests, responses, and notifications between clients and servers follow the JSON-RPC 2.0 specification with fields like `jsonrpc`, `id`, `method`, and `params`.

### Q5: What is the difference between an MCP client and an MCP server?

**Answer:**
- **MCP Server** - Exposes resources, tools, and prompts. It implements the capabilities that clients can discover and use.
- **MCP Client** - Connects to servers, discovers available capabilities, and invokes tools, reads resources, or retrieves prompts. The client is typically embedded in an LLM application.

### Q6: Why was MCP created? What problem does it solve?

**Answer:** MCP was created to solve tool integration fragmentation. Before MCP, every LLM application needed custom integrations for each tool or data source. MCP provides a standardized protocol so that:
- Tools can be built once and used by any MCP-compatible client
- Clients can dynamically discover available tools without hard-coding
- The ecosystem becomes interoperable across different vendors and frameworks

---

## Intermediate Level

### Q7: Explain the MCP initialization/handshake process.

**Answer:** During initialization:
1. Client connects to server via chosen transport (stdio, SSE, etc.)
2. Client sends an `initialize` request with its capabilities and protocol version
3. Server responds with its capabilities, supported protocol version, and server info
4. Client sends an `initialized` notification to complete the handshake
5. Both sides now know each other's capabilities and can proceed with tool/resource/prompt operations

```json
// Client initialize request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"sampling": {}},
    "clientInfo": {"name": "my-client", "version": "1.0.0"}
  }
}

// Server response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}, "resources": {}},
    "serverInfo": {"name": "my-server", "version": "1.0.0"}
  }
}
```

### Q8: How do you implement tool input validation in an MCP server?

**Answer:** Tool input validation is done through JSON Schema in the `inputSchema` field when defining a tool. The SDK validates arguments against this schema before passing them to the tool handler.

```python
Tool(
    name="query_database",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 100}
        },
        "required": ["query"]
    }
)
```

In TypeScript, Zod schemas provide additional type safety:

```typescript
server.tool("calculate", {
    metric: z.enum(["revenue", "profit"]),
    startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/)
}, async ({ metric, startDate }) => { ... });
```

### Q9: How does MCP handle dynamic tool changes (tools being added/removed at runtime)?

**Answer:** MCP supports dynamic tool changes through the `listChanged` capability. When a server declares `"tools": {"listChanged": true}`, it can send a `notifications/tools/list_changed` notification to inform clients that the tool list has changed. Clients should then call `tools/list` again to get the updated list.

```python
# Server declares capability
capabilities = {
    "tools": {"listChanged": True}
}

# Server sends notification when tools change
await session.send_notification("notifications/tools/list_changed")
```

### Q10: Explain how resource subscriptions work in MCP.

**Answer:** Resource subscriptions allow clients to receive notifications when a resource's content changes:
1. Client calls `resources/subscribe` with the resource URI
2. Server tracks subscribed resources
3. When resource content changes, server sends `notifications/resources/updated` notification
4. Client can then re-read the resource with `resources/read`
5. Client can unsubscribe with `resources/unsubscribe`

This is useful for monitoring real-time data sources like dashboards, logs, or live metrics.

### Q11: What security considerations should you address when building an MCP server?

**Answer:**
- **Authentication** - Validate client identity before allowing access
- **Authorization** - Implement role-based access control for tools and resources
- **Input Validation** - Sanitize all tool arguments to prevent injection attacks
- **Read-Only Defaults** - Default to read-only operations; require explicit permission for writes
- **Rate Limiting** - Protect against abuse of external APIs and database queries
- **Audit Logging** - Log all tool invocations for compliance and debugging
- **Secrets Management** - Never expose credentials, API keys, or sensitive data in tool outputs
- **SQL Injection Prevention** - Use parameterized queries and restrict allowed operations

### Q12: How would you integrate an existing REST API as an MCP server?

**Answer:** Create an MCP server that wraps the REST API endpoints as tools:

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_user",
            description="Get user details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_user":
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.example.com/users/{arguments['user_id']}",
                headers={"Authorization": f"Bearer {API_KEY}"}
            ) as resp:
                data = await resp.json()
                return [TextContent(type="text", text=json.dumps(data))]
```

### Q13: What is the difference between stdio and SSE transport in MCP? When would you use each?

**Answer:**

| Aspect | stdio | SSE (HTTP) |
|--------|-------|------------|
| **Use Case** | Local processes | Remote/network connections |
| **Setup** | Spawn child process | HTTP server endpoint |
| **Latency** | Very low | Higher (network overhead) |
| **Security** | OS-level isolation | Requires TLS, auth tokens |
| **Scalability** | One-to-one | One-to-many |
| **When to Use** | Desktop apps, local agents | Cloud services, web apps |

### Q14: How do you handle errors in MCP tool execution?

**Answer:** MCP supports structured error handling:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except ValueError as e:
        # Return error as text content
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except PermissionError as e:
        return [TextContent(type="text", text=f"Permission denied: {str(e)}")]
    except Exception as e:
        # Log the error and return user-friendly message
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return [TextContent(type="text", text="An internal error occurred")]
```

For JSON-RPC level errors, throw exceptions that the SDK converts to proper error responses:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Tool not found: unknown_tool"
  }
}
```

### Q15: Can an MCP client connect to multiple servers simultaneously? How?

**Answer:** Yes. An MCP client can maintain connections to multiple servers, each with its own transport and session:

```python
async def connect_multiple_servers():
    servers = [
        StdioServerParameters(command="python", args=["db_server.py"]),
        StdioServerParameters(command="python", args=["api_server.py"]),
        StdioServerParameters(command="python", args=["file_server.py"])
    ]
    
    sessions = []
    for params in servers:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                sessions.append(session)
    
    # Now use all sessions to query different servers
    tools_db = await sessions[0].list_tools()
    tools_api = await sessions[1].list_tools()
```

---

## Advanced Level

### Q16: Describe how you would build an enterprise-grade MCP gateway that routes requests to multiple backend servers.

**Answer:** An enterprise MCP gateway acts as a single entry point that routes client requests to appropriate backend MCP servers:

```python
class MCPGateway:
    def __init__(self):
        self.server_registry = {}
        self.auth = AuthMiddleware()
        self.rate_limiter = RateLimiter()
    
    async def register_server(self, name: str, server_params: StdioServerParameters):
        """Register a backend MCP server."""
        session = await self._connect_to_server(server_params)
        tools = await session.list_tools()
        self.server_registry[name] = {
            "session": session,
            "tools": {t.name: t for t in tools.tools},
            "resources": {}
        }
    
    async def route_tool_call(self, client_id: str, tool_name: str, arguments: dict):
        """Route tool call to appropriate backend server."""
        # Authenticate
        role = self.auth.validate_client(client_id)
        
        # Find which server owns this tool
        for server_name, server_info in self.server_registry.items():
            if tool_name in server_info["tools"]:
                # Check authorization
                if not self.auth.check_permission(role, "execute", tool_name):
                    raise PermissionError(f"Not authorized to use {tool_name}")
                
                # Rate limit
                await self.rate_limiter.check(client_id)
                
                # Route to backend
                session = server_info["session"]
                result = await session.call_tool(tool_name, arguments)
                
                # Log for audit
                await self.audit_log.log(client_id, tool_name, arguments)
                
                return result
        
        raise ValueError(f"Tool not found: {tool_name}")
```

Key components:
- **Service Registry** - Tracks available backend servers and their capabilities
- **Authentication/Authorization** - Validates clients and enforces RBAC
- **Rate Limiting** - Prevents abuse across all backends
- **Load Balancing** - Distributes requests across server instances
- **Circuit Breaker** - Handles backend failures gracefully
- **Audit Logging** - Tracks all operations for compliance

### Q17: How would you implement streaming responses in MCP for long-running tool executions?

**Answer:** While MCP's base protocol doesn't natively support streaming in tool responses, you can implement it using:

1. **Progress Notifications** - Server sends periodic progress updates:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    task_id = str(uuid.uuid4())
    
    # Start async task
    asyncio.create_task(self._run_long_task(task_id, arguments))
    
    # Return task ID immediately
    return [TextContent(
        type="text",
        text=json.dumps({"task_id": task_id, "status": "started"})
    )]

async def _run_long_task(self, task_id: str, arguments: dict):
    for i in range(100):
        # Send progress notification
        await self.session.send_notification(
            "notifications/progress",
            {"task_id": task_id, "progress": i, "total": 100}
        )
        await asyncio.sleep(0.1)
    
    # Store final result
    self.task_results[task_id] = {"status": "completed", "data": "..."}
```

2. **Polling Pattern** - Client polls for results:

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(name="check_task_status", inputSchema={...}),
        Tool(name="get_task_result", inputSchema={...})
    ]
```

### Q18: Explain how you would implement OAuth 2.0 authentication for MCP servers accessing external APIs.

**Answer:**

```python
from authlib.integrations.httpx_client import AsyncOAuth2Client
import asyncio

class OAuth2MCPConnector:
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client = AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=token_url
        )
        self.token_lock = asyncio.Lock()
    
    async def get_access_token(self) -> str:
        """Get or refresh access token."""
        async with self.token_lock:
            if not self.client.token or self.is_token_expired():
                self.client.token = await self.client.fetch_token(
                    grant_type="client_credentials"
                )
            return self.client.token["access_token"]
    
    async def fetch_with_auth(self, url: str) -> dict:
        """Make authenticated API request."""
        token = await self.get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            return resp.json()
```

For user-delegated OAuth (authorization code flow), the MCP server would:
1. Redirect user to authorization endpoint
2. Receive callback with authorization code
3. Exchange code for access/refresh tokens
4. Store tokens securely and refresh as needed
5. Use tokens when making API calls through MCP tools

### Q19: How would you design an MCP server that provides access to a vector database for RAG applications?

**Answer:**

```python
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import json

server = Server("vector-db-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="embed_and_store",
            description="Embed text and store in vector database",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"},
                    "text": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["collection", "text"]
            }
        ),
        Tool(
            name="similarity_search",
            description="Search for similar documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"},
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "filter": {"type": "object"}
                },
                "required": ["collection", "query"]
            }
        ),
        Tool(
            name="list_collections",
            description="List all vector collections",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "similarity_search":
        collection = arguments["collection"]
        query = arguments["query"]
        top_k = arguments.get("top_k", 5)
        
        # Search vector database
        results = await vector_db.search(
            collection=collection,
            query=query,
            top_k=top_k,
            filter=arguments.get("filter")
        )
        
        # Format results for LLM context
        formatted = "\n\n".join([
            f"Document {i+1} (score: {r.score}):\n{r.text}"
            for i, r in enumerate(results)
        ])
        
        return [TextContent(type="text", text=formatted)]
    
    elif name == "embed_and_store":
        doc_id = await vector_db.add(
            collection=arguments["collection"],
            text=arguments["text"],
            metadata=arguments.get("metadata", {})
        )
        return [TextContent(type="text", text=f"Stored with ID: {doc_id}")]
    
    elif name == "list_collections":
        collections = await vector_db.list_collections()
        return [TextContent(type="text", text=json.dumps(collections))]
```

### Q20: What are the limitations of MCP and when would you NOT use it?

**Answer:**

**Limitations:**
- **Not for high-throughput** - JSON-RPC overhead makes it unsuitable for high-frequency data streaming
- **Single response model** - Tools return single responses, not continuous streams
- **No built-in state management** - Each tool call is stateless; session state must be managed externally
- **Transport constraints** - stdio is local-only; HTTP/SSE adds latency
- **Limited bidirectional communication** - Server-initiated client calls are restricted to notifications

**When NOT to use MCP:**
- High-frequency trading systems (need sub-millisecond latency)
- Real-time video/audio streaming (need continuous data flow)
- Simple single-tool applications (overhead not justified)
- Systems requiring complex multi-step transactions within a single call
- When you need full bidirectional RPC (consider gRPC instead)

### Q21: How would you implement caching in an MCP server to improve performance?

**Answer:**

```python
import hashlib
import time
from functools import wraps

class MCPCache:
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = {}
    
    def _key(self, tool_name: str, arguments: dict) -> str:
        content = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, tool_name: str, arguments: dict):
        key = self._key(tool_name, arguments)
        entry = self.cache.get(key)
        if entry and time.time() - entry["timestamp"] < self.ttl:
            return entry["value"]
        if key in self.cache:
            del self.cache[key]
        return None
    
    def set(self, tool_name: str, arguments: dict, value: str):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        key = self._key(tool_name, arguments)
        self.cache[key] = {"value": value, "timestamp": time.time()}

cache = MCPCache(ttl=300)

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # Check cache first
    cached = cache.get(name, arguments)
    if cached:
        return [TextContent(type="text", text=cached)]
    
    # Execute tool
    result = await execute_tool(name, arguments)
    
    # Cache result
    cache.set(name, arguments, result)
    
    return [TextContent(type="text", text=result)]
```

### Q22: Describe how you would monitor and observe an MCP-based system in production.

**Answer:**

```python
import logging
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class MCPMetrics:
    tool_name: str
    duration_ms: float
    status: str
    client_id: str
    timestamp: str
    error: str = None

class MCPObservability:
    def __init__(self):
        self.logger = logging.getLogger("mcp.observability")
        self.metrics_collector = MetricsCollector()
    
    async def record_tool_call(self, metrics: MCPMetrics):
        # Structured logging
        self.logger.info("tool_execution", extra=asdict(metrics))
        
        # Metrics collection
        self.metrics_collector.increment(
            f"mcp.tool.calls.{metrics.tool_name}",
            tags={"status": metrics.status}
        )
        self.metrics_collector.histogram(
            f"mcp.tool.duration.{metrics.tool_name}",
            metrics.duration_ms
        )
        
        # Distributed tracing
        if metrics.error:
            self.metrics_collector.increment(
                f"mcp.tool.errors.{metrics.tool_name}",
                tags={"error_type": type(metrics.error).__name__}
            )
        
        # Alert on anomalies
        if metrics.duration_ms > 5000:
            await self.alerting.send_alert(
                f"Slow tool execution: {metrics.tool_name} took {metrics.duration_ms}ms"
            )

# Integration with MCP server
observability = MCPObservability()

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    start = time.time()
    try:
        result = await execute_tool(name, arguments)
        await observability.record_tool_call(MCPMetrics(
            tool_name=name,
            duration_ms=(time.time() - start) * 1000,
            status="success",
            client_id=get_current_client_id(),
            timestamp=datetime.now().isoformat()
        ))
        return result
    except Exception as e:
        await observability.record_tool_call(MCPMetrics(
            tool_name=name,
            duration_ms=(time.time() - start) * 1000,
            status="error",
            client_id=get_current_client_id(),
            timestamp=datetime.now().isoformat(),
            error=str(e)
        ))
        raise
```

Key observability components:
- **Structured Logging** - JSON logs with consistent fields
- **Metrics** - Request counts, latencies, error rates per tool
- **Distributed Tracing** - Trace requests across multiple MCP servers
- **Alerting** - Anomaly detection on latency and error rates
- **Dashboards** - Real-time visibility into MCP system health


---

## Senior Deep Dive: MCP for Enterprise Tool/Data Integration & AI Copilots

> *The JD emphasizes Claude/Anthropic and AI copilots. MCP is Anthropic's open standard for connecting models to tools and data — interviewers probe whether you can integrate and secure it at enterprise scale.*

### SQ1: What problem does MCP solve, and why does it matter for enterprise copilots?

**Answer:** **MCP (Model Context Protocol)** is an open standard from **Anthropic** that standardizes how an LLM application connects to tools and data sources through **MCP servers** — often described as "USB-C for AI tools." Without MCP, every AI client that wants to call the same internal tool must implement its own bespoke connector, producing an **N×M integration matrix** that is expensive to build and painful to maintain. MCP collapses this to **N+M**: build a server once, and any MCP-capable host — Claude Desktop, an IDE plugin, a custom application — can consume it immediately. For enterprise copilots specifically, this means a single MCP server for a risk database or policy document store can be reused by the credit-analyst copilot, the compliance assistant, and the developer toolchain simultaneously. **Trade-off:** adopting an emerging protocol buys reuse and portability but is less mature than hand-rolled glue, so you pay some standardization cost up front — worth it when many AI clients must share the same integrations.

### SQ2: Describe MCP's architecture.

**Answer:** MCP defines three roles: the **Host** (the LLM application — e.g. Claude Desktop or a custom Python service), the **Client** (a thin connection manager embedded in the host, one per server), and the **MCP Server** (the integration process that exposes capabilities). Servers expose three primitives: **resources** (read-only data or context the model can read, like a file or a database row), **tools** (callable actions with side effects, like running a query or posting a message), and **prompts** (reusable, parameterized prompt templates). Transport is either **stdio** for local in-process servers or **HTTP with Server-Sent Events (SSE)** for remote servers. The key architectural insight is **separation of concerns**: the host contains no integration code — it speaks the MCP protocol, and each server owns the domain knowledge of its integration. **Trade-off:** the protocol hop adds one layer of indirection, but it standardizes everything behind it and makes the integration swappable without touching the host.

### SQ3: How do you secure MCP tool access in a regulated environment?

**Answer:** Security for MCP in a regulated context rests on several layers working together. First, apply **least-privilege, scoped servers**: each MCP server should expose only the tools and resources its role requires — a read-only analytics server must not expose write tools. Second, enforce **per-server authentication and credential management**: servers connect to backend systems using secrets stored in a vault (e.g. Azure Key Vault), never embedded in code. Third, maintain **tool allow-lists** in the host so the model can only invoke approved tools, and require **human-in-the-loop approval** for any state-changing or high-risk action before execution. Fourth, **audit every tool invocation** — log the tool name, parameters, caller identity, and result to an immutable audit trail; in a regulated domain this is not optional. Finally, and critically, **validate and sanitize tool outputs** before they are added to the model's context, because tool results are a **prompt-injection** vector: a malicious or compromised document returned by a tool can contain instructions that hijack the model's next action. **Trade-off:** tighter controls reduce the agent's speed and flexibility, but in any environment where tool calls touch money, PII, or regulated decisions, these controls are mandatory — the risk of a compromised tool call is higher than the cost of the gate.

### SQ4: MCP vs traditional function/tool calling — what's the difference, and when do you use each?

**Answer:** **Function/tool calling** (as implemented natively by OpenAI, Anthropic, and others) is in-app and model-specific: you define JSON schemas for tools inside your application, and the model returns structured calls that your application dispatches. It is tightly coupled — the integration logic lives in the app, and it only serves that app. **MCP** standardizes and **decouples** the integration: the server runs as a separate process reachable over a transport, it can be shared across many hosts, and the protocol is model-agnostic. Choose **plain tool calling** for bespoke, tightly-coupled tools in a single application where you want the simplest possible path and have no cross-client sharing requirement. Choose **MCP** when the same integration must be consumed by multiple AI clients or teams, when you want integrations to be discoverable and versioned independently of the model application, or when you want to adopt the emerging standard that major AI tooling is converging on. **Trade-off:** MCP's reusability and portability come at the cost of a slightly more involved setup than an in-process function definition — the break-even is reached quickly whenever more than one host needs the same integration.

### SQ5: Where do Claude and Anthropic fit in this picture?

**Answer:** **MCP is Anthropic's** open standard, and **Claude** is Anthropic's frontier model with strong **tool-use and agentic** capabilities — both directly relevant to a JD that names Claude and AI copilots. Claude's tool-use API (the model signals which tool to call and with what arguments) pairs naturally with MCP: Claude acts as the reasoning engine, and MCP servers provide the enterprise integrations. The strategic payoff for an engineering team is that building an MCP server means the integration works across Claude and every other MCP-capable host, so your enterprise investments are **not locked to a single model vendor's tool-calling format** — if the team later uses a different model or a different host application, the server is reused unchanged. **Trade-off:** betting on an open but still-maturing standard carries some early-adopter risk versus building to a single vendor's SDK; the standard wins on portability as the ecosystem grows, which makes it the right long-term choice for a broad enterprise integration estate.

# Model Context Protocol (MCP) - Interview Questions

This document contains interview questions and answers covering Module 5: Model Context Protocol (MCP).

---

## 1. MCP Overview

### Q1: What is the Model Context Protocol (MCP)?

**Answer:** MCP is a standardized protocol that enables LLMs to interact with external tools, services, and data sources. It provides:

- **Standard Interface:** Consistent way for AI models to access tools
- **Tool Discovery:** Models can discover available capabilities
- **Resource Management:** Access to data and files
- **State Management:** Maintain context across interactions

Think of it as a "USB-C for AI" - a universal port for connecting AI to anything.

---

### Q2: Why do we need a standard interface between LLMs and tools?

**Answer:** Need for standardization:

- **Current Problem:** Each tool requires custom integration
- **Scalability:** Hard to add new tools
- **Portability:** Locked into specific frameworks
- **Developer Experience:**重复 work for each integration

MCP solves this by providing a universal standard.

---

### Q3: What are the core components of MCP?

**Answer:** Core components:

- **MCP Server:** Provides tools, resources, prompts
- **MCP Client:** Connects to servers, makes requests
- **Transport Layer:** Communication (stdio, HTTP)
- **Message Protocol:** JSON-RPC based messages

---

## 2. MCP Servers

### Q4: What are MCP Servers?

**Answer:** MCP Servers are:

- **Expose Tools:** Functions the AI can call
- **Provide Resources:** Data the AI can read
- **Define Prompts:** Reusable prompt templates
- **Examples:**
  - Weather API server
  - Database server
  - Filesystem server
  - Finance API server

---

### Q5: How do you create an MCP Server?

**Answer:** Creation steps:

1. **Define Tools:** Create functions with descriptions
2. **Tool Registration:** Register with MCP server
3. **Run Server:** Start listening for requests

```python
from mcp.server import Server
from mcp.types import Tool

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="Get weather for a location",
            inputSchema={"type": "object", "properties": {"location": {"type": "string"}}}
        )
    ]
```

---

### Q6: What are examples of MCP Servers?

**Answer:** Example servers:

- **Weather API:** Get weather data for locations
- **UK Carbon Intensity:** Carbon emissions data
- **Database Server:** SQL query execution
- **Filesystem:** Read/write files
- **Finance API:** Stock prices, company data
- **GitHub:** Repository management

---

### Q7: How do you run an MCP Server?

**Answer:** Running:

1. **Install Package:** `pip install mcp`
2. **Configure:** Set transport (stdio or SSE)
3. **Run Command:** Start the server process
4. **Connect Client:** Connect to use tools

```bash
python my_server.py
# or
mcp run my_server
```

---

## 3. MCP Client

### Q8: What is an MCP Client?

**Answer:** MCP Client:

- **Connects to Servers:** Initiates connections
- **Sends Requests:** Calls tools on servers
- **Receives Results:** Gets tool outputs
- **Manages Sessions:** Maintains connections

Used in AI applications to access external capabilities.

---

### Q9: How do you create an MCP Client?

**Answer:** Client creation:

```python
from mcp import Client

# Connect to server
client = Client("my-server")

# List available tools
tools = await client.list_tools()

# Call a tool
result = await client.call_tool("get_weather", {"location": "London"})
```

---

### Q10: How do you test an MCP Client?

**Answer:** Testing:

1. **Unit Tests:** Test tool definitions
2. **Integration Tests:** Test server-client communication
3. **Mock Server:** Use mock for testing
4. **Error Handling:** Test edge cases

---

## Technical Deep-Dive

### Q11: What transport layers does MCP support?

**Answer:** Transport types:

- **Stdio:** Local process communication (most common)
- **SSE (Server-Sent Events):** HTTP-based streaming
- **HTTP:** REST-like communication

Choice depends on deployment scenario.

---

### Q12: What is the MCP message format?

**Answer:** Message format:

- **JSON-RPC 2.0:** Standard JSON-RPC protocol
- **Methods:**
  - `initialize`: Start session
  - `tools/list`: Get available tools
  - `tools/call`: Execute a tool
  - `resources/list`: Get available resources

---

### Q13: How does tool definition work in MCP?

**Answer:** Tool definition:

```json
{
  "name": "get_weather",
  "description": "Get current weather",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name"
      }
    },
    "required": ["location"]
  }
}
```

---

## Architecture Questions

### Q14: How does MCP fit into an agent architecture?

**Answer:** Architecture integration:

```
┌─────────────┐
│    LLM     │
└──────┬──────┘
       │
┌──────▼──────┐
│  MCP Client │
└──────┬──────┘
       │
┌──────▼──────┐
│  MCP Server │ → Tools, Resources
└─────────────┘
```

MCP provides the bridge between AI and external capabilities.

---

### Q15: What is the difference between MCP and function calling?

**Answer:**

| Aspect | MCP | Function Calling |
|--------|-----|------------------|
| Standard | Universal | Provider-specific |
| Discovery | Dynamic | Static definitions |
| Resources | Yes | No |
| State | Session-based | Per-call |
| Use Case | General | LLM-specific |

---

### Q16: How do you secure MCP communications?

**Answer:** Security:

- **Authentication:** API keys or tokens
- **Authorization:** Limit tool access
- **Input Validation:** Sanitize all inputs
- **Audit Logging:** Track all tool calls
- **Encryption:** TLS for network transport

---

## Production Questions

### Q17: How do you debug MCP server issues?

**Answer:** Debugging:

1. **Check Server Logs:** Error messages
2. **Verify Tool Definitions:** Schema validation
3. **Test Transport:** Ensure communication works
4. **Client Tracing:** See what's being sent
5. **Mock Responses:** Test without real server

---

### Q18: What are best practices for MCP server design?

**Answer:** Best practices:

- **Clear Tool Names:** Descriptive, consistent
- **Detailed Descriptions:** Help the LLM understand when to use
- **Proper Error Handling:** Return meaningful errors
- **Idempotency:** Same input = same output
- **Timeouts:** Don't hang indefinitely

---

### Q19: How do you handle MCP server failures?

**Answer:** Failure handling:

- **Connection Retry:** Automatic reconnection
- **Fallback Tools:** Alternative approaches
- **Graceful Degradation:** Continue without unavailable tools
- **Monitoring:** Alert on failures
- **Circuit Breaker:** Stop calling failing servers

---

## Scenario Questions

### Q20: How would you build a weather MCP server?

**Answer:** Implementation:

1. **Define Tool:** `get_weather(location)`
2. **API Integration:** Connect to weather API
3. **Error Handling:** Handle invalid locations
4. **Caching:** Cache results to reduce API calls
5. **Rate Limiting:** Respect API limits

---

### Q21: How do you connect an MCP server to a database?

**Answer:** Database connection:

```python
@server.list_tools()
async def list_tools():
    return [Tool(
        name="query_db",
        description="Run SQL query",
        inputSchema={...}
    )]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "query_db":
        return run_query(arguments["sql"])
```

---

## Summary

Key MCP topics:

1. **Overview:** What is MCP, why it matters
2. **Servers:** Creating and running MCP servers
3. **Clients:** Connecting to and using servers
4. **Security:** Protecting MCP communications
5. **Production:** Debugging, failure handling

---

## References

- [MCP Specification](references.md)
- [MCP Server Examples](references.md)
- [MCP Client SDK](references.md)

---

## Enterprise-Level Questions

### Q22: How do you implement authentication in MCP servers?

**Answer:** Authentication implementation:

```python
from mcp.server import Server
from functools import wraps

# API Key authentication
API_KEYS = {"key1": "client1", "key2": "client2"}

def authenticate(func):
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        # Extract API key from request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise PermissionError("No authorization header")
        
        api_key = auth_header.replace("Bearer ", "")
        if api_key not in API_KEYS:
            raise PermissionError("Invalid API key")
        
        return await func(request, *args, **kwargs)
    return wrapper

# Usage
@server.call_tool()
@authenticate
async def call_tool(name: str, arguments: dict):
    # Tool implementation
    pass
```

---

### Q23: What are the best practices for MCP server performance?

**Answer:** Performance best practices:

| Practice | Description |
|----------|-------------|
| **Connection Pooling** | Reuse connections to reduce overhead |
| **Caching** | Cache frequently accessed data |
| **Async Operations** | Use async/await for I/O operations |
| **Rate Limiting** | Prevent abuse with rate limits |
| **Resource Limits** | Limit memory and execution time |

```python
# Caching example
from functools import lru_cache
import time

cache = {}
CACHE_TTL = 300

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    key = f"{name}:{json.dumps(arguments)}"
    
    if key in cache:
        result, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return result
    
    result = await execute_tool(name, arguments)
    cache[key] = (result, time.time())
    return result
```

---

### Q24: How do you handle MCP server failures and resilience?

**Answer:** Resilience patterns:

1. **Circuit Breaker** - Stop calling failing servers
2. **Retry with Backoff** - Exponential backoff for transient failures
3. **Fallback** - Use alternative tools when primary fails
4. **Timeout** - Set reasonable timeouts

```python
# Retry with exponential backoff
import asyncio

async def retry_call(client, tool, args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.call_tool(tool, args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait)

# Circuit breaker
class CircuitBreaker:
    def __init__(self, threshold=5):
        self.failures = 0
        self.threshold = threshold
        self.state = "closed"
    
    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "open"
```

---

### Q25: How do you secure MCP communications in production?

**Answer:** Security measures:

- **TLS/SSL** - Encrypt all network communication
- **API Keys** - Token-based authentication
- **Input Validation** - Sanitize all tool inputs
- **Rate Limiting** - Prevent abuse
- **Audit Logging** - Log all requests and responses
- **IP Whitelisting** - Restrict access to known IPs

```python
# Security configuration
SECURITY_CONFIG = {
    "tls_enabled": True,
    "require_api_key": True,
    "rate_limit": {
        "calls_per_minute": 100,
        "burst": 20
    },
    "allowed_ips": ["10.0.0.0/8", "192.168.0.0/16"]
}
```

---

### Q26: How do you monitor MCP servers in production?

**Answer:** Monitoring strategy:

| Metric | Description | Tools |
|--------|-------------|-------|
| **Request Rate** | Calls per second | Prometheus |
| **Latency** | Response time | Grafana |
| **Error Rate** | Failed requests | Datadog |
| **Tool Usage** | Popular tools | Custom dashboard |
| **Resource Usage** | CPU, Memory | CloudWatch |

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram

request_counter = Counter('mcp_requests_total', 'Total MCP requests')
latency_histogram = Histogram('mcp_request_latency', 'Request latency')

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    start = time.time()
    try:
        result = await execute_tool(name, arguments)
        request_counter.labels(tool=name, status='success').inc()
        return result
    finally:
        latency_histogram.observe(time.time() - start)
```

---

### Q27: How do you scale MCP servers horizontally?

**Answer:** Horizontal scaling approach:

```
┌─────────────────────────────────────────────────────────────┐
│                   LOAD BALANCER                             │
│                    (nginx/haproxy)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ MCP     │  │ MCP     │  │ MCP     │  │ MCP     │
   │ Server 1│  │ Server 2│  │ Server 3│  │ Server 4│
   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                      ┌──────▼──────┐
                      │  Shared     │
                      │  State      │
                      │  (Redis)    │
                      └─────────────┘
```

Implementation:
1. Use stateless servers with shared state
2. Implement sticky sessions if needed
3. Use connection pooling
4. Deploy behind load balancer

---

### Q28: How do you implement MCP server logging and tracing?

**Answer:** Logging implementation:

```python
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Structured logging
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(json.dumps({
        "event": "tool_call",
        "timestamp": datetime.utcnow().isoformat(),
        "tool": name,
        "args": arguments
    }))
    
    try:
        result = await execute_tool(name, arguments)
        logger.info(json.dumps({
            "event": "tool_success",
            "tool": name,
            "duration_ms": duration
        }))
        return result
    except Exception as e:
        logger.error(json.dumps({
            "event": "tool_error",
            "tool": name,
            "error": str(e)
        }))
        raise
```

---

### Q29: What are the differences between MCP transport mechanisms?

**Answer:** Transport comparison:

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **Stdio** | Local processes | Simple, secure | No network access |
| **SSE** | Web apps | Real-time, HTTP | Complex setup |
| **HTTP** | REST APIs | Familiar, scalable | More overhead |

```python
# Stdio transport (most common for local)
from mcp.server.stdio import stdio_server

async with stdio_server() as streams:
    await app.run(streams[0], streams[1], options)

# SSE transport for web
from mcp.server.sse import SseServerTransport

transport = SseServerTransport("/mcp")
async with serve(app, transport) as server:
    await server.serve()
```

---

### Q30: How do you test MCP servers and clients?

**Answer:** Testing strategy:

```python
# Unit tests
import pytest

@pytest.mark.asyncio
async def test_tool_execution():
    server = create_test_server()
    result = await server.call_tool("add", {"a": 1, "b": 2})
    assert result[0].text == "3"

@pytest.mark.asyncio
async def test_tool_schema():
    server = create_test_server()
    tools = await server.list_tools()
    assert any(t.name == "add" for t in tools)

# Integration tests
@pytest.mark.asyncio
async def test_server_client():
    # Start server
    proc = await asyncio.create_subprocess_exec(
        "python", "server.py",
        stdout=asyncio.subprocess.PIPE
    )
    
    # Connect client
    async with Client("test") as client:
        result = await client.call_tool("test", {})
        assert result
    
    proc.terminate()
```

---

### Q31: How do you handle MCP protocol versioning?

**Answer:** Version handling:

```python
# Server side - advertise version
app = Server("my-server")

@app.list_tools()
async def list_tools():
    return tools

# Client side - check version during initialize
async with Client("my-server") as client:
    # Initialize with version negotiation
    await client.initialize(
        protocol_version="1.0.0",
        capabilities={"tools": True, "resources": True}
    )
    
    # Check server capabilities
    server_info = client.server_info
```

---

### Q32: What are common MCP anti-patterns to avoid?

**Answer:** Anti-patterns:

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| **Large tool schemas** | Hard to parse | Keep schemas simple |
| **No error handling** | Poor UX | Return meaningful errors |
| **Synchronous calls** | Blocking | Use async/await |
| **No input validation** | Security risk | Validate all inputs |
| **Missing timeouts** | Hanging requests | Set reasonable timeouts |

---

### Q33: How do you migrate from custom integrations to MCP?

**Answer:** Migration strategy:

1. **Inventory** - List all current integrations
2. **Prioritize** - Start with simple integrations
3. **Wrapper** - Create MCP wrapper for existing services
4. **Migrate** - Replace custom code with MCP calls
5. **Validate** - Test functionality
6. **Iterate** - Move more integrations

```python
# Wrap existing service as MCP
class LegacyServiceWrapper:
    def __init__(self, legacy_service):
        self.service = legacy_service
    
    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="legacy_api",
                description="Legacy API wrapper",
                inputSchema={...}
            )
        ]
    
    @app.call_tool()
    async def call_tool(name, arguments):
        # Call legacy service
        result = self.service.execute(name, arguments)
        return [TextContent(type="text", text=str(result))]
```

---

### Q34: How do you implement MCP in a microservices architecture?

**Answer:** Microservices integration:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / BFF                        │
│                    (MCP Client)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│  User   │         │  Order  │         │  Payment│
│ Service │         │ Service │         │ Service │
│ (MCP)   │         │ (MCP)   │         │ (MCP)   │
└─────────┘         └─────────┘         └─────────┘
```

Implementation:
- Each microservice exposes MCP server
- API Gateway/BFF acts as MCP client
- Single entry point for AI applications
- Service-to-service communication via MCP

---

### Q35: What is the future roadmap for MCP?

**Answer:** MCP roadmap directions:

- **Enhanced Security** - Built-in OAuth, mTLS support
- **Better Tool Discovery** - Semantic tool matching
- **Multi-modal Support** - Image, audio tool support
- **Standardized Prompts** - Prompt library ecosystem
- **Performance** - Binary protocol, compression
- **Ecosystem Growth** - More servers, better tooling

---

## Quick Reference

### MCP Methods

| Method | Direction | Description |
|--------|-----------|-------------|
| `initialize` | Client→Server | Start session |
| `tools/list` | Client→Server | Get available tools |
| `tools/call` | Client→Server | Execute tool |
| `resources/list` | Client→Server | Get available resources |
| `resources/read` | Client→Server | Read resource |
| `prompts/list` | Client→Server | Get available prompts |
| `prompts/get` | Client→Server | Get prompt content |

### Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Auth error |

---

## Senior Deep Dive: MCP in the Enterprise

> Senior interviews move beyond "can you build an MCP server" to "can you own the platform that runs MCP servers for hundreds of teams and thousands of agents." Expect questions that probe how you secure, scale, govern, and operate MCP infrastructure across an org — where blast radius, ownership boundaries, and threat models matter as much as protocol mechanics.

---

### System Design & Scale

#### Q: Design an MCP server platform that serves many tools to many agents across an organization.

**Answer:** Build a centralized MCP platform around a tool registry backed by a service catalog — not a single monolithic server. Agents discover tools through a registry API rather than hard-coded server addresses, which decouples consumers from topology changes.

**Core platform layers:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent / LLM Clients                         │
└────────────────────────────┬────────────────────────────────────┘
                             │  MCP (HTTP/SSE or stdio proxy)
┌────────────────────────────▼────────────────────────────────────┐
│              MCP Gateway / Tool Registry                        │
│  - Auth (OAuth 2.0 / AAD token validation)                      │
│  - Route: tool-name → server URL                                │
│  - Rate limiting, quota enforcement                             │
│  - Audit log (every tool call + caller identity)                │
└──────────┬─────────────────┬──────────────────┬─────────────────┘
           │                 │                  │
    ┌──────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
    │ Weather     │  │ DB Query     │  │ CRM Read     │
    │ MCP Server  │  │ MCP Server   │  │ MCP Server   │
    │ (team-A)    │  │ (team-B)     │  │ (team-C)     │
    └─────────────┘  └──────────────┘  └──────────────┘
```

**Key design decisions:**

- **Registry/discovery:** Store tool metadata (name, version, owning team, schema, SLA tier) in Azure API Management or a lightweight service like Consul. Agents call `GET /tools` against the gateway; the gateway fans out to registered servers or returns a cached manifest.
- **Auth:** Use Azure Active Directory (AAD) + managed identities. Agents present a short-lived JWT; the gateway validates it and forwards a scoped credential to downstream servers. Servers never trust caller-supplied identity directly.
- **Transport:** Use HTTP/SSE for cross-host tools (enables horizontal scaling, TLS, load balancing). Stdio is reserved for local-agent scenarios where the process boundary is the trust boundary.
- **Versioning:** Semantic versioning on tool schemas. The gateway routes `get_weather@2` to the v2 server while `get_weather@1` still reaches v1, allowing rolling upgrades without breaking existing agents.
- **Multi-tenancy:** Namespace tools by team (`team-b/query_db`). Quota and rate limits enforced per tenant at the gateway layer, not inside each server. This prevents one team's runaway agent from starving another team's workload.

**Senior framing:** The failure mode of skipping a gateway is that each agent hard-codes server addresses, every security control is implemented twelve different ways (or not at all), and you have no central place to rotate credentials or pull a compromised tool. The gateway is the control plane — treat it with the same rigor as an API gateway for external traffic.

---

#### Q: How do you scale and isolate tool execution behind MCP?

**Answer:** Treat each tool as an untrusted workload. Isolation is the safety property; elasticity is the operational property. Achieve both through per-tool sandboxing combined with resource controls enforced at the platform layer.

**Isolation tiers by risk:**

| Risk tier | Example tools | Isolation mechanism |
|-----------|---------------|---------------------|
| Low (read-only, public data) | Weather, exchange rates | Shared process, read-only network |
| Medium (internal read) | DB SELECT, doc retrieval | Separate container, VNet-scoped egress |
| High (write, side-effects) | DB write, email send, code exec | Dedicated pod, time-boxed, no lateral egress |
| Critical (code execution) | Sandboxed REPL, shell commands | Azure Container Instances / gVisor, ephemeral, zero persistence |

**Resource controls per tool:**
- **Timeouts:** Hard deadline at the gateway (e.g., 30 s default, 5 s for low-tier). The server's own timeout is set 10 % lower so it can return a clean error before the gateway drops the connection.
- **Rate limits:** Token-bucket per `(caller-identity, tool-name)`. On Azure API Management this is a built-in policy. Prevents a single agent from monopolising a shared tool.
- **Memory/CPU quotas:** If tools run as containers (Azure Container Apps, Kubernetes), set `resources.limits`. An OOM-killed tool returns an error; it does not cascade to the MCP server process.
- **Concurrency caps:** Semaphore inside the tool handler. A DB tool caps at 20 concurrent queries; callers above that receive a `429` rather than saturating the connection pool.

**Senior framing:** The most dangerous mistake is running all tools in one process with no resource caps. A single slow or misbehaving tool call then blocks the event loop or exhaust memory for every other caller. Isolate early — retrofitting per-tool sandboxing after an incident is expensive.

---

#### Q: How do you handle resource and context management when tool outputs are large?

**Answer:** LLM context windows are finite and expensive. Large tool outputs are the leading cause of context overflow in production agentic systems. The MCP server must be a responsible context steward, not just a dumb data pipe.

**Layered strategy:**

1. **Pagination by default.** Any tool that can return N items must support `limit` and `cursor` parameters. The server returns `{"items": [...], "next_cursor": "abc123"}`. The agent fetches only what it needs for the current reasoning step.

2. **Truncation with a signal.** When a single result (e.g., a log file) exceeds a configurable byte limit (say, 8 KB), return the first N bytes plus `"truncated": true, "total_bytes": 142000`. The agent knows data was cut and can request a specific range if needed.

3. **Streaming via SSE for progressive results.** Long-running tools (database scans, report generation) stream partial results as SSE events. The agent can act on early results and cancel early if the answer is already found, avoiding full result materialisation.

4. **Token-budget headers.** The MCP client can send a `X-Token-Budget: 2000` header. The server tailors its response — summarise rather than dump raw data, omit low-signal fields — to fit the declared budget.

5. **Summary vs. raw modes.** Expose two tool variants: `search_logs` (returns a structured summary of matches) and `search_logs_raw` (returns full text, gated to privileged callers). Most agents never need the raw form.

**Senior framing:** Token budget awareness at the tool layer is a competitive advantage in production — it directly reduces cost and latency. Teams that skip this end up with agents that silently truncate context at the LLM layer, losing information without any audit trail.

---

### Trade-offs & Decisions

#### Q: When should you use MCP versus a direct/custom tool integration?

**Answer:** Default to MCP for any tool integration that will be used by more than one team or more than one agent framework. Use a custom/direct integration only when you have a strong forcing function — not as the default.

**Decision framework:**

| Factor | Favour MCP | Favour custom integration |
|--------|-----------|--------------------------|
| Number of consumers | 2+ teams or frameworks | Single agent, single team |
| Ecosystem longevity | Multi-year investment | Prototype / throwaway |
| Standardization value | High (auth, logging, versioning already solved) | Low (one-off, unique semantics) |
| Overhead tolerance | Can absorb gateway hop | Sub-millisecond latency critical |
| Interoperability | Must work with Claude, GPT-4o, open-source agents | Single LLM vendor forever |

**Where custom integration wins:** latency-critical hot paths (e.g., real-time trading signals), proprietary binary protocols that don't map cleanly to JSON-RPC, or a quick proof-of-concept where the overhead of MCP server setup exceeds the value delivered.

**Where MCP wins:** everything else. The standardized protocol means you write auth, logging, rate limiting, and versioning once at the gateway layer rather than reimplementing them in every integration. Ecosystem momentum (Anthropic, Microsoft, open-source) is now large enough that MCP-compatible tools can be dropped into any compliant client without a rewrite.

**Senior framing:** The most expensive error is building bespoke integrations for the first five tools, then re-platforming onto MCP once the sixth team asks to reuse them. Make the MCP decision before the second integration, not after the sixth.

---

#### Q: One mega MCP server versus many focused servers — how do you choose?

**Answer:** Favour many focused servers. The mega-server pattern is a monolith by another name and inherits all the same operational problems.

**Blast radius analysis:**

```
Mega-server failure impact:
  Deploy a bug in tool-A → ALL tools go down
  Memory leak in tool-B → tool-C, D, E are starved
  Config change for tool-F → full server restart needed

Focused-server failure impact:
  Deploy a bug in weather-server → only weather tools affected
  Memory leak in db-server → only DB tools affected
  Config change → only that server restarts
```

**Ownership and deploy cadence:** A mega-server has no clear owner — every team touches it. A focused server is owned by one team that ships it on their own cadence without coordinating with five other teams. Ownership clarity accelerates both development and incident response.

**When to consolidate:** A single server is acceptable when tools are tightly coupled (share state, share a database connection pool, or are always deployed together), maintained by the same team, and the combined tool count stays small (under ~10 tools). Example: a "CRM tools" server that owns `get_contact`, `update_contact`, and `list_deals` — all from the same database, same team.

**Practical middle ground:** Start with one server per owning team, not one server per tool. This gives ownership clarity without the operational overhead of hundreds of single-tool servers. As teams grow, they split their server — same pattern as microservices.

**Senior framing:** The governance question "who approves a change to the mega-server" often becomes the bottleneck that kills developer velocity. Focused servers eliminate the coordination overhead by design.

---

#### Q: How do you choose between stdio and remote (HTTP/SSE) transport?

**Answer:** The transport choice is fundamentally a trust boundary and operational model decision, not a performance decision.

**Comparison:**

| Dimension | stdio | HTTP/SSE |
|-----------|-------|----------|
| Trust model | OS process isolation; agent and server in same host/pod | Network boundary; mTLS + auth enforced |
| Scaling | 1:1 (one server process per agent) | N:M (many agents share server instances) |
| Latency | ~0 ms IPC overhead | 1–10 ms network hop (LAN) |
| Security surface | Smaller (no network exposure) | Larger (must harden HTTP endpoint) |
| Operational complexity | Simple to run locally; hard to observe remotely | Requires load balancer, TLS certs, service discovery |
| Appropriate for | Local dev, single-machine agents, sandboxed code exec | Shared org infrastructure, cross-team tools, cloud agents |

**Decision rule:** Use stdio when the agent and the tool server are co-located and the OS process boundary is a sufficient trust boundary — typically local developer environments and sandboxed code execution tools (where spawning a child process is the isolation mechanism). Use HTTP/SSE for everything shared: tools that serve multiple agents, tools running as cloud services, or any scenario where you need independent scaling of the tool server.

**Hybrid pattern:** Many production systems use a "stdio proxy" — the agent spawns a lightweight local stdio process that simply proxies to a remote HTTP/SSE endpoint. This preserves the simple stdio API on the client side while gaining the operational benefits of a remote server. Azure AI Foundry's MCP support uses this pattern.

**Senior framing:** Teams that default to stdio for everything hit a wall the moment they want to share a tool across agents or scale it independently. Define the transport boundary at architecture time, not as an afterthought.

---

### Failure Modes & Incidents

#### Q: A malicious or compromised MCP tool is discovered in your platform. How do you contain it and prevent recurrence?

**Answer:** Treat this as a supply-chain incident, not just a bug. Immediate containment first, then root-cause investigation, then systemic prevention.

**Immediate containment (first 15 minutes):**
1. Pull the tool from the registry — set its status to `disabled` so the gateway stops routing to it. No deployment needed.
2. Revoke the tool server's managed identity / API key so it can no longer call downstream services even if still running.
3. Kill running instances and quarantine the container image. Do not delete — preserve for forensics.
4. Review audit logs for the blast window: which agents called the tool, what arguments were passed, what data was returned. Scope the breach.

**Prevention (systemic controls):**

- **Least privilege by default.** Each tool server's identity has only the permissions it needs (read-only on the specific DB table, not full DB access). Compromising a tool server gives an attacker minimal foothold.
- **Allow-list for tool registration.** New tools cannot be added to the registry without a security review workflow (see governance Q below). No self-service registration in production.
- **Output validation at the gateway.** The gateway validates that tool responses conform to the declared output schema. Unexpected fields or binary blobs that weren't in the schema are stripped and flagged.
- **Image signing.** Use Azure Container Registry content trust / Sigstore. The gateway only routes to servers whose container images are signed by an approved pipeline.
- **Continuous audit log analysis.** Stream MCP audit logs to Azure Sentinel. Alert on anomalous patterns: a tool suddenly reading 10x its normal data volume, a tool calling an external endpoint it has never called before.

**Senior framing:** The hardest part of this incident is the blast-radius assessment — figuring out whether the compromised tool exfiltrated data or injected malicious content into agent reasoning chains. Audit logs with full input/output capture are non-negotiable for this. Teams that log only "tool X was called" and not the arguments and results cannot scope the incident.

---

#### Q: An MCP server became a bottleneck and single point of failure. How do you respond and prevent recurrence?

**Answer:** Immediate response is to restore availability; the real work is eliminating the SPOF before the next incident.

**Incident response:**
1. Check if the issue is load-induced (high CPU/memory) or a bug (crash loop). If load-induced, scale horizontally immediately — Azure Container Apps, AKS HPA.
2. If it cannot be scaled (e.g., a stateful server holding session data), shed load: the gateway enforces stricter rate limits, queues excess requests, or returns graceful degradation responses ("tool temporarily unavailable, please retry").
3. For a crash loop, roll back to the last known-good image. Do not hotfix under pressure.

**Architectural prevention:**

```
Before (SPOF):                  After (resilient):
                                
  Agent → MCP Server ──────→   Agent → Gateway → MCP Server (primary AZ-1)
           ↓                                    ↘ MCP Server (replica AZ-2)
           DB                                   ↘ MCP Server (replica AZ-3)
                                                  (shared Redis session store)
```

- **Stateless servers + shared session store.** Sessions in Redis (Azure Cache for Redis), not in-process. Any replica can handle any request.
- **Health checks.** The gateway's load balancer does `/health` probes every 5 seconds. Unhealthy instances are removed from rotation without manual intervention.
- **Circuit breaker at the gateway.** If a server fails 5 consecutive calls in 30 seconds, open the circuit — return a cached response or a structured error to the agent rather than queuing requests behind a broken server.
- **Timeouts everywhere.** Gateway enforces a hard deadline. The tool server enforces a slightly shorter one. Neither hangs waiting for the other.
- **Multi-region for SLA > 99.9%.** Active-active across Azure regions with Traffic Manager or Azure Front Door. The gateway in each region routes to local servers; cross-region is a fallback.

**Senior framing:** The most insidious SPOF is not the server itself but the database it depends on. A "replicated" MCP server cluster that shares a single DB instance is still a SPOF. Trace the dependency chain to external systems, not just the MCP process.

---

#### Q: Version skew between an MCP client and server caused tool calls to break. How do you handle it and prevent it?

**Answer:** Version skew is inevitable in a distributed system where clients and servers deploy independently. The protocol must be designed to tolerate it; the platform must detect it before it reaches production.

**Root cause categories:**
1. Client sends a field the server's schema doesn't recognise (additive change — usually benign if server ignores unknown fields).
2. Server removes or renames a required field the client depends on (breaking change — must be managed).
3. Client and server disagree on the semantics of an enum value or error code (silent corruption — the worst kind).

**Protocol-level defences:**

- **Capability negotiation on `initialize`.** Client advertises `{"protocol_version": "2025-06-01", "capabilities": {"tools": true, "streaming": true}}`. Server responds with the intersection of supported capabilities. Neither side calls features the other hasn't confirmed.
- **Semantic versioning on tool schemas.** Bump the major version for breaking changes (`get_weather` → `get_weather@v2`). The gateway routes by version. Old clients continue hitting v1 until they migrate.
- **Additive-only policy for minor versions.** Never remove or rename a field in a minor version. Deprecate with a grace period (e.g., 90 days), announced via the registry's tool metadata.

**Contract testing (prevention):**

```
CI pipeline for MCP server:
  1. Build server image
  2. Run Pact consumer-driven contract tests:
     - Load recorded client expectations
     - Replay against new server build
     - Fail if any client expectation is broken
  3. Only then allow deploy to staging
```

Azure DevOps pipeline stage: "Contract Verification" gate before any MCP server deploys to non-dev environments. Breaks are caught before they reach agents.

**Incident recovery:** When skew is detected in production (tool call returns unexpected schema), the gateway serves the last compatible version from a blue/green deployment until the client is updated. Never force a client upgrade in production without a compatibility window.

**Senior framing:** The most expensive skew incidents are the silent ones — the server returns a subtly wrong value that the agent acts on without error. Type-safe schemas (JSON Schema with `additionalProperties: false`) and contract tests are the only reliable defences. Logging alone catches this too late.

---

### Leadership & Behavioral

#### Q: How do you govern which MCP servers and tools are approved for organizational use?

**Answer:** Governance must balance security rigour with developer velocity. A process that takes three weeks to approve a tool will be bypassed; one with no process is a security disaster.

**Lightweight approval workflow:**

1. **Self-service registration request.** Team submits a tool registration PR to a central `mcp-registry` repo (GitOps). PR includes: tool name, owning team, schema, data classification, required permissions, and a threat model checklist.
2. **Automated checks (no human needed):** Schema linter, image signature verification, dependency scan (Dependabot / Snyk), no hardcoded secrets check.
3. **Tiered human review based on data classification:**
   - Public/internal data: peer review from another engineer on the owning team.
   - Confidential data or write operations: security engineer review (target SLA: 2 business days).
   - Regulated data (PII, financial): security + data governance review.
4. **Merge = registration.** The pipeline registers the tool in the platform registry with its approved permissions. Any deviation from the declared schema triggers an alert.
5. **Annual re-review.** Tools are automatically flagged for re-review if their dependency graph has high-severity CVEs or if they haven't been updated in 12 months.

**Metrics to track:** Time-to-approval by tier, number of tools pending review, percentage of tools with up-to-date security reviews, incident rate by tool tier.

**Senior framing:** Governance that lives only in a ticket system dies when the ticketing team is overwhelmed. Codify the rules as automated checks (linters, policy-as-code via OPA/Azure Policy) so the fast path for low-risk tools requires no human at all. Reserve human review for high-risk decisions.

---

#### Q: Tell me about a time you standardized tool access via MCP across multiple teams. (STAR format)

**Answer:**

**Situation:** At a previous role, three separate product teams had independently built LLM-powered features over 18 months. Each team had built its own tool integration layer: Team A used LangChain with custom REST wrappers, Team B had direct OpenAI function-calling with hardcoded API keys, and Team C had a homegrown JSON-RPC microservice. All three accessed overlapping internal services (the CRM, the data warehouse, and the document store) through different code paths with different auth mechanisms. When a security audit flagged that two of these paths lacked audit logging and one had over-privileged credentials, we had three separate remediations to coordinate — and no shared infrastructure to build on.

**Task:** I was asked to design and drive adoption of a common tool access layer that would eliminate the duplicated integrations, close the security gaps, and give the platform team visibility into all tool calls across the AI surface area — without forcing the three teams to rewrite their agent logic.

**Action:**
1. Started by mapping the overlap: all three teams called the same five internal services. Built five focused MCP servers (one per service) and deployed them behind an internal gateway on Azure API Management. Each server used a managed identity scoped to exactly the permissions that service required.
2. Negotiated a migration timeline with each team: no forced cutover, but new tools must go through MCP. Provided a thin compatibility shim that wrapped the existing LangChain and function-calling interfaces so teams could adopt MCP incrementally without rewriting agent orchestration code.
3. Wrote the registry governance process (PR-based, automated schema linting, tiered review) and ran the first three tools through it myself to prove the process worked before asking other teams to follow it.
4. Instrumented the gateway with structured audit logs piped to our SIEM. Within a week of rollout, we surfaced two previously invisible over-calling patterns that were driving up API costs.

**Result:** All three teams migrated within a quarter. Tool call audit coverage went from ~40% to 100%. Credential sprawl dropped from 14 service-account keys to 5 managed identities. The security gaps from the audit were remediated as a side effect of the migration, not as a separate project. Two quarters later, two new teams adopted MCP from day one because the platform now had clear documentation and an established approval path — the standardization had compounded.

**Senior framing:** The key to cross-team standardization is making the standard the path of least resistance, not mandating compliance. The compatibility shims were what unlocked adoption: teams didn't have to choose between shipping features and adopting the platform.

---

> 🎯 **Staff/Principal stretch:** Define the enterprise MCP governance model — covering registry, security review, and tool ownership — that scales from 10 tools to 1,000 tools without becoming a bottleneck.
>
> **Model answer:** The governance model must be a platform, not a process. At 10 tools, a human approval checklist is fine. At 1,000 tools, the same checklist is a queue that kills developer velocity and gets bypassed.
>
> **Registry architecture:** The registry is a GitOps repo (`mcp-registry`) where every tool is a YAML manifest (name, version, owner team, schema ref, data classification, permission set, SLA tier). The registry is the source of truth; the gateway reads from it. Adding a tool = merging a PR; removing a tool = deleting the manifest and the gateway stops routing within minutes.
>
> **Security review as code:** Map data classification to automated policy gates (Open Policy Agent / Azure Policy). Tools touching only public or internal-read data pass automatically if they clear automated checks (schema lint, image signing, dependency scan, no secrets). Tools with write access or confidential data require a human security review — but the policy gate enforces this automatically; no human needs to manually triage what tier a tool falls into.
>
> **Ownership model:** Every tool manifest has a required `owner_team` and `oncall_contact`. The platform auto-pages the owner on P1 incidents involving their tool. Tools with no valid owner contact are automatically deprecated after a 30-day warning. This eliminates orphaned tools, which are the highest-risk category at scale (no one monitors them, no one patches them).
>
> **Scaling the review queue:** At 100+ tool registrations per month, the bottleneck shifts to human review of medium-risk tools. Solve this with peer review (any security-certified engineer from any team can approve a same-tier tool) rather than a central security team bottleneck. The platform tracks review quality via quarterly audits of approved tools — if a peer-approved tool has an incident, that feeds back into the certification process.
>
> **Metrics for governance health:** approval cycle time by tier (target: <4 hours automated, <2 days human), orphaned tool rate (target: 0), security review backlog (target: <10 tools), incident rate per tool tier (leading indicator of tier miscalibration). Review these monthly; adjust policy thresholds when the data warrants it — not on a fixed schedule.

---

End of Interview Questions

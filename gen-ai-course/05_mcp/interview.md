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

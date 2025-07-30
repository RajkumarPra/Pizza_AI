# Pizza AI - Model Context Protocol Implementation

## Overview

This project implements a pizza ordering system using the **Model Context Protocol (MCP)** - an open standard for AI-tool integration. The system consists of an MCP server that exposes pizza-related tools and resources, and a FastAPI client that integrates Groq LLM with these MCP tools.

## What is Model Context Protocol (MCP)?

Model Context Protocol is a standardized way for AI applications to access external tools and data sources. Unlike traditional REST APIs, MCP provides:

- **Standardized tool integration** - Tools are defined with JSON schemas
- **Resource management** - Structured access to data and context
- **LLM-agnostic design** - Works with any language model
- **Type safety** - Built-in validation for tool parameters

## Architecture Components

### 🍕 MCP Server (`pizza_mcp_server.py`)
The core business logic server that exposes pizza ordering capabilities via MCP protocol.

**Tools Exposed:**
- `get_menu` - Retrieve pizza menu by category (all/veg/non-veg)
- `find_pizza` - Search for specific pizzas by name and size
- `place_order` - Place pizza orders with customer details
- `track_order` - Track orders by ID or customer email
- `check_user` - Verify user existence and get information
- `save_user` - Store/update user information
- `get_suggestions` - Get pizza recommendations based on preferences

**Resources Exposed:**
- `memory://menu` - Complete pizza menu with all items
- `memory://orders` - Order history and current status
- `memory://users` - User database and preferences

**Transport:** Standard I/O (stdio) - communicates via JSON-RPC messages

### 🌐 FastAPI Client (`pizza_api.py`)
Web API that integrates Groq LLM with MCP tools via a single endpoint.

**Key Features:**
- Single POST endpoint: `/chat`
- Automatic intent detection using Groq LLM
- Dynamic tool selection based on user input
- Natural language response generation
- Automatic MCP server lifecycle management

**API Flow:**
1. User sends message to `/chat` endpoint
2. FastAPI client analyzes intent using Groq LLM
3. Client calls appropriate MCP tools via stdio communication
4. MCP server executes business logic and returns structured data
5. Client generates natural language response using Groq

### 🧠 LLM Integration (`utils/groq_integration.py`)
Groq Llama 3.1 7B integration for:
- Intent recognition and parameter extraction
- Natural language response generation
- Fallback intent detection when LLM calls fail

## Key Differences from Traditional Approaches

### ❌ **Before (Traditional REST APIs)**
- Tight coupling between AI logic and business logic
- Custom integration code for each tool
- Inconsistent tool definitions across different services
- Difficult to reuse tools with different LLMs

### ✅ **After (MCP Implementation)**
- Standardized tool interface via MCP protocol
- Clean separation between AI reasoning and business operations
- Reusable tools that work with any MCP-compatible client
- Type-safe tool calling with JSON schema validation

## Running the System

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### Available Commands

```bash
# Run FastAPI client (recommended for normal use)
python main.py fastapi

# Run MCP server standalone (for testing/debugging)
python main.py mcp

# Show architecture information
python main.py info

# Test integration
python main.py test
```

### API Usage

**Endpoint:** `POST http://localhost:8001/chat`

**Request:**
```json
{
    "message": "I want a pepperoni pizza",
    "user_email": "john@example.com",
    "user_name": "John"
}
```

**Response:**
```json
{
    "response": "Great! I found Pepperoni Pizza (Large) for $15.99. Would you like me to place this order for you?",
    "tools_used": ["find_pizza"],
    "context": {
        "intent": "order",
        "pending_order": {...},
        "user_email": "john@example.com"
    }
}
```

## Example Interactions

### 1. Getting Menu
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the menu"}'
```

### 2. Ordering Pizza
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a large margherita pizza",
    "user_email": "customer@example.com",
    "user_name": "Alice"
  }'
```

### 3. Tracking Orders
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Track my order",
    "user_email": "customer@example.com"
  }'
```

## Benefits of MCP Architecture

### 🎯 **Standardization**
- Consistent tool interface across all pizza operations
- JSON schema validation for all tool parameters
- Standard resource access patterns

### 🔧 **Reusability**
- MCP server can be used with different client applications
- Tools work with any MCP-compatible LLM client
- Easy to add new tools without changing client code

### 🛡️ **Type Safety**
- All tool parameters validated against JSON schemas
- Compile-time safety for tool definitions
- Runtime validation prevents invalid tool calls

### 🚀 **Scalability**
- MCP server can run independently and be scaled
- Multiple clients can connect to the same MCP server
- Stateless tool design enables horizontal scaling

### 🧪 **Testability**
- Business logic isolated in MCP server
- Tools can be tested independently
- Mock MCP servers for integration testing

## Development Guidelines

### Adding New Tools

1. **Define the tool in MCP server:**
```python
Tool(
    name="new_tool",
    description="Description of what the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param1"]
    }
)
```

2. **Implement the tool handler:**
```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    if name == "new_tool":
        # Tool implementation
        return CallToolResult(content=[TextContent(type="text", text=result)])
```

3. **Add client integration (optional):**
```python
async def new_tool_action(self, param1: str) -> Dict[str, Any]:
    return await self.call_tool("new_tool", {"param1": param1})
```

### Adding New Resources

```python
Resource(
    uri="memory://new_resource",
    name="New Resource",
    description="Description of the resource",
    mimeType="application/json"
)
```

## Troubleshooting

### Common Issues

1. **MCP Server fails to start:**
   - Check that all dependencies are installed
   - Ensure Python path includes the project directory

2. **Groq API errors:**
   - Verify GROQ_API_KEY is set in .env file
   - Check API key validity and rate limits

3. **Tool calls fail:**
   - Verify tool parameters match the JSON schema
   - Check MCP server logs for detailed error messages

### Debug Mode

Run with verbose logging:
```bash
export MCP_DEBUG=1
python main.py fastapi
```

## Future Enhancements

- **Persistent Storage**: Replace in-memory storage with database
- **Authentication**: Add user authentication and authorization
- **Real-time Updates**: WebSocket support for order status updates
- **Multi-tenant**: Support multiple restaurant clients
- **Advanced AI**: More sophisticated intent recognition and conversation memory

## Learn More

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Groq API Documentation](https://docs.groq.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 
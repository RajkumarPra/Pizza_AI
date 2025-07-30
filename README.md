# Pizza AI - Modular, Scalable, and Developer-Friendly

Pizza AI is a smart pizza ordering system built with a focus on clean code, separation of concerns, and future scalability. Whether you're placing a large BBQ chicken pizza order or tracking it via a custom protocol, this system has it covered.



## Why This Structure?

Most projects mix business logic with frameworks, databases, and external services, which makes them hard to change, test, or scale. We took a modular approach instead. Each part of the system has its own responsibility:

- Core logic knows nothing about APIs or databases.
- Application logic coordinates workflows like ordering or tracking.
- Infrastructure handles FastAPI, Groq, storage, and communication protocols like MCP.

This makes the codebase easier to test, extend, and maintain without surprises.



## Project Structure

```

src/
├── domain/             # Pure business logic: Pizza, Order, User, etc.
├── application/        # Workflows like "place order", "track order"
└── infrastructure/     # APIs, external services, storage, MCP, DI setup

````

Each layer is loosely coupled and serves a single purpose. You can change one part without affecting the others.



## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
````

### 2. Set up environment variables

```bash
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### 3. Run the system

```bash
# Run both FastAPI and MCP server
python main.py both
```

Other options:

```bash
python main.py fastapi   # Only FastAPI
python main.py mcp       # Only MCP
python main.py info      # Show architecture info
python main.py test      # Run tests
```



## API Overview

### FastAPI Server ([http://localhost:8001](http://localhost:8001))

| Endpoint          | Description                     |
| -- | - |
| `POST /chat`      | Natural language pizza ordering |
| `GET /menu`       | Fetch pizza menu                |
| `POST /order`     | Place an order (structured)     |
| `GET /order/{id}` | Track an existing order         |
| `GET /health`     | Health check endpoint           |

### MCP Server (stdio)

Built for protocol-level integration using JSON-RPC over stdio.

**Available tools:** `get_menu`, `place_order`, `track_order`, `check_user`, `get_suggestions`
**Resources:** `menu`, `orders`, `users`



## Example Usage

### Order via Chat

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a large pepperoni pizza",
    "user_email": "john@example.com",
    "user_name": "John"
  }'
```

### Get Menu Items

```bash
curl http://localhost:8001/menu?category=veg
```



## Tech Stack

| Layer         | Tech Used                                   |
| - | - |
| Core (domain) | Pure Python, `dataclasses`, `enum`          |
| App layer     | FastAPI, Pydantic                           |
| Infra layer   | Groq (LLM), MCP protocol, in-memory storage |



## What's Next?

Thanks to the modular design, you can easily:

* Add database support (PostgreSQL, etc.)
* Plug in authentication
* Connect to different LLMs (OpenAI, Claude)
* Integrate payments or user preferences
* Add a modern frontend UI without touching core logic



## Final Note

Pizza AI isn’t just about pizza. It's a foundation for any AI-driven, protocol-based interaction system. It just happens to be delicious to start with.


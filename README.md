# 🍕 Pizza AI - Clean Architecture Implementation

A modern pizza ordering system built with **Clean Architecture** principles, **Model Context Protocol (MCP)** integration, and **Groq LLM** for natural language processing.

## 🏗️ Architecture Overview

This project follows **Clean Architecture** patterns with strict dependency inversion, ensuring maintainable, testable, and framework-independent code.

### **Directory Structure**
```
Pizza_AI/
├── src/                           # Clean Architecture Implementation
│   ├── domain/                    # Enterprise Business Rules
│   │   ├── entities/             # Core business entities
│   │   │   ├── pizza.py         # Pizza entity with validation
│   │   │   ├── order.py         # Order aggregate root
│   │   │   └── user.py          # User entity
│   │   ├── repositories/         # Repository interfaces (DIP)
│   │   ├── services/             # Domain services
│   │   └── data/                 # Domain data models
│   ├── application/              # Application Business Rules
│   │   ├── use_cases/           # Application use cases
│   │   └── interfaces/          # External service contracts
│   └── infrastructure/          # Frameworks & External Concerns
│       ├── external/            # External service implementations
│       ├── persistence/         # Data persistence
│       └── web/                 # Web framework integration
├── tests/                        # Test suite
├── Frontend/                     # React frontend (unchanged)
├── main.py                       # Application entry point
└── requirements.txt              # Dependencies
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Groq API key

### **Installation**
```bash
# Clone and navigate to project
cd Pizza_AI

# Install dependencies
pip install -r requirements.txt

# Setup environment
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

### **Running the System**
```bash
# Start both MCP server and FastAPI client
python main.py both

# Or run components separately:
python main.py mcp      # MCP server only
python main.py client   # FastAPI client only

# Show architecture info
python main.py info
```

## 🎯 Clean Architecture Benefits

### **1. Dependency Inversion**
- **Domain** layer has no external dependencies
- **Application** layer depends only on Domain
- **Infrastructure** implements Domain interfaces
- **Easy to swap implementations** (Groq → OpenAI, Memory → Database)

### **2. Testability**
- **Domain logic** is pure and easily unit tested
- **Use cases** can be tested with mocked dependencies
- **Integration tests** verify external service contracts

### **3. Maintainability**
- **Business rules** are centralized in entities and domain services
- **Clear separation** between what the system does vs. how it does it
- **Framework independence** allows easy technology migrations

## 🍕 Domain Model

### **Core Entities**

#### **Pizza Entity**
```python
Pizza(
    id="pizza_1",
    name="Margherita", 
    size=PizzaSize.LARGE,
    price=8.99,
    category=PizzaCategory.VEG,
    description="Fresh tomato sauce, mozzarella, and basil",
    ingredients=["tomato sauce", "mozzarella", "basil"]
)
```

#### **Order Aggregate**
```python
Order(
    customer=CustomerInfo(...),
    items=[OrderItem(pizza=pizza, quantity=2)],
    status=OrderStatus.CONFIRMED,
    estimated_delivery_time=datetime.now() + timedelta(minutes=30)
)
```

### **Business Rules**
- **Pizza validation**: Price must be positive, ingredients required
- **Order lifecycle**: Defined status transitions with business constraints
- **Delivery time calculation**: Based on order complexity and peak hours
- **Customer management**: Email validation and order history tracking

## 🤖 MCP Integration

### **What is MCP?**
Model Context Protocol enables standardized communication between LLMs and external tools, providing:
- **Type-safe tool definitions** with JSON schemas
- **Standardized resource access** patterns
- **LLM-agnostic design** that works with any compatible client

### **MCP Tools Exposed**
```python
# Menu Operations
get_menu(category="all|veg|non-veg")          # Get pizza menu
find_pizza(name="margherita", size="large")   # Search specific pizza

# Order Operations  
place_order(customer_info, items)             # Create new order
track_order(order_id?, customer_email?)       # Track order status

# User Operations
check_user(email)                             # Verify user existence
save_user(email, name)                        # Store user data

# Recommendations
get_suggestions(customer_email?, preferences) # Get personalized suggestions
```

### **Architecture Flow**
```
User Message → FastAPI → Groq LLM → Intent Parsing → MCP Tool Selection → Domain Logic → Response Generation
```

## 🔧 Technology Stack

### **Domain Layer**
- **Pure Python**: No external dependencies
- **Dataclasses & Enums**: Type-safe entity definitions
- **Business rule validation**: Built into entities

### **Application Layer**
- **FastAPI**: Modern web framework
- **Pydantic**: Data validation and serialization

### **Infrastructure Layer**
- **Groq**: LLM integration (Llama 3.1 7B Instant)
- **MCP Python SDK**: Model Context Protocol implementation
- **In-memory storage**: For development (easily replaceable)

## 📋 API Usage

### **Single Chat Endpoint**
```bash
POST http://localhost:8001/chat
```

**Request:**
```json
{
    "message": "I want a large pepperoni pizza",
    "user_email": "customer@example.com", 
    "user_name": "John",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "response": "🍕 Great choice! I found Pepperoni Classic (Large) for $10.49. Would you like me to place this order for you?",
    "tools_used": ["find_pizza"],
    "context": {
        "intent": "find_pizza",
        "pizza_found": {
            "name": "Pepperoni Classic",
            "size": "Large", 
            "price": "$10.49"
        }
    }
}
```

### **Example Interactions**

#### **Menu Browsing**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me vegetarian options"}'
```

#### **Order Placement**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want 2 large margherita pizzas",
    "user_email": "john@example.com",
    "user_name": "John"
  }'
```

#### **Order Tracking**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where is my order?",
    "user_email": "john@example.com"
  }'
```

## 🧪 Testing

### **Running Tests**
```bash
# Unit tests (domain entities and services)
python -m pytest tests/unit/

# Integration tests (MCP communication, LLM integration)  
python -m pytest tests/integration/

# End-to-end tests (complete order flows)
python -m pytest tests/e2e/

# All tests
python -m pytest
```

### **Test Coverage**
- **Domain Entities**: Business rule validation
- **Domain Services**: Complex business logic
- **Use Cases**: Application workflow orchestration
- **MCP Integration**: Tool calling and response handling
- **LLM Service**: Intent parsing and response generation

## 🚀 Deployment

### **Local Development**
```bash
python main.py both
```
- **FastAPI**: http://localhost:8001
- **MCP Server**: stdio communication

### **Production Setup**
```bash
# Environment variables
export GROQ_API_KEY="your_api_key"
export ENVIRONMENT="production"

# Start with process manager
python main.py both
```

## 📈 Monitoring & Logging

### **Health Checks**
- **FastAPI Health**: `GET /health`
- **MCP Server Health**: Built-in MCP diagnostics

### **Logging**
- **Domain Events**: Order lifecycle changes
- **LLM Interactions**: Intent parsing and response generation
- **Error Tracking**: Graceful fallbacks and error recovery

## 🛣️ Roadmap

### **Phase 1: Enhanced Persistence**
- [ ] Database repository implementations
- [ ] User session management
- [ ] Order history persistence

### **Phase 2: Advanced Features**
- [ ] Payment processing integration
- [ ] Real-time order status notifications
- [ ] Advanced recommendation algorithms

### **Phase 3: Scalability**
- [ ] Microservices architecture
- [ ] Distributed MCP server deployment
- [ ] Multi-tenant support

## 🤝 Contributing

### **Development Guidelines**
1. **Follow Clean Architecture**: Keep dependencies pointing inward
2. **Write Tests**: Unit tests for domain logic, integration tests for external services
3. **Domain-First**: New features start with domain entities and business rules
4. **Interface Segregation**: Keep interfaces focused and minimal

### **Adding New Features**
1. **Define Domain Entity**: Add business rules and validation
2. **Create Repository Interface**: Abstract data access contract
3. **Implement Use Case**: Orchestrate domain logic
4. **Add Infrastructure**: External service implementations
5. **Expose via MCP**: Define tools and integrate with existing flow

## 📚 Learn More

- **Clean Architecture**: [Architecture documentation](ARCHITECTURE.md)
- **Model Context Protocol**: [MCP Specification](https://modelcontextprotocol.io/)
- **Groq API**: [Documentation](https://docs.groq.com/)
- **FastAPI**: [Official docs](https://fastapi.tiangolo.com/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with Clean Architecture principles for maintainable, testable, and scalable pizza ordering! 🍕** 
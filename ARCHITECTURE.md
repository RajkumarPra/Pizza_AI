# Pizza AI - Clean Architecture Implementation

## Overview

This project implements a pizza ordering system using **Clean Architecture** principles with **Model Context Protocol (MCP)** integration. The system is designed to be maintainable, testable, and independent of external frameworks.

## Clean Architecture Layers

### 🏢 **Domain Layer** (`src/domain/`)
The core business logic and rules, completely independent of external concerns.

#### **Entities** (`src/domain/entities/`)
Core business objects that encapsulate enterprise-wide business rules:

- **`Pizza`**: Represents pizza items with validation, pricing, and categorization
- **`Order`**: Complex aggregate root managing order lifecycle and business rules
- **`User`**: Customer entity with profile management and validation
- **`OrderItem`**: Individual order line items with quantity and pricing
- **`CustomerInfo`**: Value object for customer details

#### **Repository Interfaces** (`src/domain/repositories/`)
Abstract contracts for data access following Dependency Inversion Principle:

- **`IPizzaRepository`**: Pizza data operations
- **`IOrderRepository`**: Order persistence and retrieval
- **`IUserRepository`**: User management operations

#### **Domain Services** (`src/domain/services/`)
Business logic that doesn't naturally fit within a single entity:

- **`OrderDomainService`**: Complex order operations, delivery time calculation, suggestions

### 🎯 **Application Layer** (`src/application/`)
Application-specific business rules and orchestration.

#### **Use Cases** (`src/application/use_cases/`)
High-level application operations that coordinate domain entities:

- **`OrderUseCases`**: Complete order management workflows
  - Place orders with validation
  - Track orders with progress calculation
  - Menu browsing and search
  - Personalized recommendations

#### **Interfaces** (`src/application/interfaces/`)
Contracts for external services:

- **`ILLMService`**: Language model integration interface

### 🔧 **Infrastructure Layer** (`src/infrastructure/`)
External concerns, frameworks, and implementation details.

#### **External Services** (`src/infrastructure/external/`)
Concrete implementations of external service interfaces:

- **`GroqLLMService`**: Groq API integration for natural language processing
  - Intent recognition and parsing
  - Response generation
  - Order confirmation messages
  - Error handling with fallbacks

#### **Persistence** (`src/infrastructure/persistence/`) 
Data storage implementations (in-memory for now):

- Repository implementations
- Data mappers
- Database adapters

#### **Web** (`src/infrastructure/web/`)
Web framework integration:

- FastAPI controllers
- MCP server implementation
- HTTP request/response handling

## Key Design Principles

### **1. Dependency Inversion**
```
┌─────────────────┐    ┌─────────────────┐
│   Application   │    │  Infrastructure │
│   Use Cases     │────▶│  Implementations│
└─────────────────┘    └─────────────────┘
         │                       │
         │              implements│
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     Domain      │    │   Interfaces    │
│   Interfaces    │◀───│   (Abstract)    │
└─────────────────┘    └─────────────────┘
```

### **2. Clean Dependencies**
- **Domain**: No external dependencies
- **Application**: Depends only on Domain
- **Infrastructure**: Depends on Application and Domain
- **Web/CLI**: Depends on all layers

### **3. Business Rules Enforcement**
- **Entities**: Validate their own data and enforce invariants
- **Domain Services**: Handle complex business operations
- **Use Cases**: Orchestrate workflows and external interactions

## Model Context Protocol (MCP) Integration

### **MCP Architecture**
```
┌─────────────────┐    stdio    ┌─────────────────┐
│   FastAPI       │◀──────────▶│   MCP Server    │
│   (Host/Client) │             │   (Pizza Tools) │
└─────────────────┘             └─────────────────┘
         │                               │
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   Groq LLM      │             │  Domain Logic   │
│   Integration   │             │  (Order, Pizza) │
└─────────────────┘             └─────────────────┘
```

### **MCP Tools Exposed**
- **`get_menu`**: Retrieve pizza menu by category
- **`find_pizza`**: Search for specific pizzas
- **`place_order`**: Create new orders
- **`track_order`**: Check order status
- **`check_user`** / **`save_user`**: User management
- **`get_suggestions`**: Personalized recommendations

## Technology Stack

### **Core Dependencies**
```python
# Domain Layer - No external dependencies
# Pure Python with dataclasses and enums

# Application Layer
fastapi>=0.104.0        # Web framework
pydantic>=2.0.0         # Data validation

# Infrastructure Layer  
groq>=0.4.0             # LLM integration
mcp>=1.0.0              # Model Context Protocol
python-dotenv>=1.0.0    # Environment management
uvicorn[standard]>=0.24.0  # ASGI server
```

### **Development Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
echo "GROQ_API_KEY=your_api_key_here" > .env

# Run the system
python main.py both    # Start both MCP server and FastAPI client
```

## Data Flow

### **Order Placement Flow**
1. **Web Layer**: Receives HTTP request
2. **Application**: `OrderUseCases.place_order()`
3. **Domain**: Creates `Order` entity with business rules
4. **Domain Service**: Calculates delivery time, validates items
5. **Infrastructure**: Persists order, generates LLM confirmation
6. **Response**: Returns structured order confirmation

### **MCP Integration Flow**
1. **FastAPI Client**: Receives chat message
2. **LLM Service**: Parses intent and parameters
3. **MCP Client**: Calls appropriate MCP tool
4. **MCP Server**: Executes domain logic
5. **LLM Service**: Generates natural language response
6. **Client**: Returns formatted response

## Testing Strategy

### **Unit Tests**
- **Domain Entities**: Business rule validation
- **Domain Services**: Complex business logic
- **Use Cases**: Application workflows

### **Integration Tests**
- **MCP Communication**: Client-server interaction
- **LLM Integration**: Intent parsing and response generation
- **Repository Implementations**: Data persistence

### **End-to-End Tests**
- **Complete Order Flow**: From chat to order completion
- **Error Handling**: Graceful failure scenarios
- **Performance**: Response times and throughput

## Deployment

### **Local Development**
```bash
python main.py both
```

### **Production Considerations**
- **Environment Variables**: Secure API key management
- **Database**: Replace in-memory storage with persistent database
- **Monitoring**: Add logging and metrics
- **Scaling**: Containerize and deploy with orchestration

## Benefits of This Architecture

### **1. Maintainability**
- Clear separation of concerns
- Easy to locate and modify business rules
- Independent layer testing

### **2. Testability**
- Domain logic is pure and easily testable
- Dependency injection enables mocking
- Clear interfaces for external services

### **3. Flexibility**
- Easy to swap LLM providers (Groq → OpenAI)
- Database-agnostic design
- Framework independence

### **4. Scalability**
- MCP enables distributed tool execution
- Clean interfaces support microservices
- Business logic reusable across interfaces

## Future Enhancements

1. **Persistent Storage**: Database repository implementations
2. **Authentication**: User session management
3. **Payment Integration**: Secure payment processing
4. **Real-time Updates**: WebSocket order status notifications
5. **Analytics**: Order pattern analysis and reporting
6. **Multi-tenancy**: Support for multiple restaurant chains

This clean architecture ensures the system remains maintainable, testable, and adaptable to changing business requirements while providing a robust foundation for the pizza ordering platform. 
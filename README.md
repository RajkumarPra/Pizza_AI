# 🍕 Pizza Planet AI - Smart Pizza Ordering System

An intelligent pizza ordering system with conversational AI, built with **Python FastAPI**, **React**, and **Google Gemini Flash**.

![Pizza Planet](https://img.shields.io/badge/Pizza-Planet-orange?style=for-the-badge&logo=pizza)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)

## ✨ Features

### 🧠 **Smart AI Integration**
- **Gemini Flash Model** for natural language processing
- Intelligent intent recognition (order, track, menu, casual conversation)
- Dynamic response generation with personalized messages

### 🍕 **Complete Ordering System**
- **Voice & Text Ordering**: "I want BBQ Chicken large" → AI confirmation → Order placed
- **Menu Filtering**: Smart categorization (Veg/Non-Veg)
- **Order Confirmation Flow**: AI-powered confirmation with dynamic responses
- **Real-time Order Tracking**: Live status updates with progress indicators

### 🎯 **User Experience**
- **Personalized Welcome Flow**: Email-based user identification
- **Thank You Animation**: Smooth order confirmation with progress visualization
- **Dynamic ETA Calculation**: Real-time delivery estimates
- **Order History**: Track current and past orders

### 🏗️ **Architecture**
- **MCP (Model Context Protocol)**: Centralized communication hub
- **Modular Design**: Separate agents for ordering and scheduling
- **RESTful API**: Clean FastAPI backend with Pydantic validation
- **Responsive Frontend**: Modern React UI with TypeScript

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API Key

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Pizza-Planet-AI.git
cd Pizza-Planet-AI
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Gemini API
# Edit utils/config.py and add your API key:
# genai.configure(api_key="YOUR_GEMINI_API_KEY")
```

### 3. Start Backend Server
```bash
cd mcp
python mcp_server_from_spec.py
```
Server runs on: `http://localhost:8001`

### 4. Frontend Setup (if applicable)
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on: `http://localhost:3000`

## 📡 API Endpoints

### **Order Management**
- `POST /api/order` - Place pizza order
- `GET /api/order/{order_id}` - Track specific order
- `GET /api/menu` - Get pizza menu

### **Chat Interface**
- `POST /api/chat` - AI-powered conversation (ordering, tracking, menu)

### **User Management**
- `POST /api/user/check` - Check if user exists
- `POST /api/user/save` - Save user information
- `GET /api/user/{email}/orders` - Get user order history

## 🍕 Available Pizzas

### Vegetarian
- **Margherita** (Large) - $8.99
- **Veggie Supreme** (Medium) - $9.25
- **Paneer Tikka** (Large) - $11.25
- **Mushroom Delight** (Small) - $7.99

### Non-Vegetarian
- **Pepperoni Classic** (Medium) - $10.49
- **BBQ Chicken** (Large) - $12.99
- **Meat Lovers** (Large) - $14.99
- **Chicken Supreme** (Medium) - $11.99

## 💬 Example Conversations

### Ordering
```
User: "I want BBQ Chicken large"
AI: "🚀 Perfect! Your Large BBQ Chicken pizza for $12.99. Confirm?"
User: "yes confirm"
AI: "🎉 Order confirmed! Your delicious BBQ Chicken is being prepared. ETA: 28 minutes"
```

### Menu Browsing
```
User: "Show me non-veg options"
AI: "🍖 Here are our amazing non-vegetarian pizzas! Loaded with meat!"
[Displays filtered non-veg menu]
```

### Order Tracking
```
User: "Track my order"
AI: "🔥 Your order #MCP-ORD-abc123 is currently cooking! ETA: 15 minutes 🍕"
```

## 🏗️ Project Structure

```
Pizza-Planet-AI/
├── agents/                 # AI Agents
│   ├── ordering_agent.py   # Pizza ordering logic
│   └── scheduler_agent.py  # Delivery scheduling
├── mcp/                    # MCP Server
│   └── mcp_server_from_spec.py  # Main FastAPI server
├── utils/                  # Utilities
│   ├── config.py          # Gemini configuration
│   ├── menu.py            # Pizza menu data
│   ├── mcp_helpers.py     # Helper functions
│   └── gemini_integration.py  # AI integration
├── frontend/              # React Frontend
│   └── src/               # React components
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

### Test Order Flow
```bash
python test_order_flow.py
```

### Test with cURL
```bash
# Place order
curl -X POST "http://localhost:8001/api/order" \
  -H "Content-Type: application/json" \
  -d '{
    "items": ["BBQ Chicken"],
    "address": "123 Main St",
    "phone": "555-0123",
    "user_id": "test_user",
    "email": "test@pizza-planet.com"
  }'

# Track order
curl -X GET "http://localhost:8001/api/order/ORDER_ID"
```

## 🔧 Configuration

### Gemini API Setup
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update `utils/config.py`:
```python
genai.configure(api_key="YOUR_API_KEY_HERE")
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Future Enhancements

- [ ] Payment integration
- [ ] Real-time delivery tracking with maps
- [ ] Customer reviews and ratings
- [ ] Multi-restaurant support
- [ ] Mobile app development
- [ ] Voice-only ordering interface

## 👨‍💻 Author

**Your Name** - [GitHub](https://github.com/yourusername)

---

**⭐ If you found this project helpful, please give it a star!**

Made with ❤️ and 🍕 
"""Helper utilities for MCP server operations"""

def sanitize_message(message: str) -> str:
    """Sanitize user message for processing"""
    return message.strip()

def format_order_items(items: list) -> str:
    """Format order items for display"""
    return ", ".join([f"{item['name']} ({item['size']})" for item in items])

def format_price(price: float) -> str:
    """Format price for display"""
    return f"${price:.2f}"

def create_order_id() -> str:
    """Generate a unique order ID"""
    import uuid
    return f"MCP-ORD-{str(uuid.uuid4())[:8]}"

def create_user_id() -> str:
    """Generate a unique user ID"""
    import uuid
    return str(uuid.uuid4())

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(email_regex, email) is not None

def extract_order_id_from_message(message: str) -> str:
    """Extract order ID from user message"""
    import re
    order_id_patterns = [
        r'(MCP-ORD-[\w\d]+)',  # Standard format
        r'order\s+(\w+)',      # "track order 123"
        r'#(\w+)',             # "track #123"
        r'\b(\d{3,8})\b'       # Any 3-8 digit number
    ]
    
    for pattern in order_id_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            extracted_id = match.group(1)
            # If it's just a number, format it as MCP order
            if extracted_id.isdigit():
                return f"MCP-ORD-{extracted_id}"
            else:
                return extracted_id if extracted_id.startswith('MCP-ORD-') else f"MCP-ORD-{extracted_id}"
    
    return None 
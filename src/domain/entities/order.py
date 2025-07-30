"""
Domain Entities - Order
Core order management entities and business rules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
import uuid

from .pizza import Pizza


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    COOKING = "cooking"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    """Individual item in an order"""
    pizza: Pizza
    quantity: int = 1
    special_instructions: Optional[str] = None
    
    def __post_init__(self):
        """Validate order item"""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if not self.pizza.is_available:
            raise ValueError(f"Pizza {self.pizza.name} is not available")
    
    @property
    def total_price(self) -> float:
        """Calculate total price for this item"""
        return self.pizza.price * self.quantity
    
    @property
    def display_name(self) -> str:
        """Get display name for the item"""
        base = f"{self.quantity}x {self.pizza.display_name}"
        if self.special_instructions:
            base += f" (Note: {self.special_instructions})"
        return base


@dataclass
class CustomerInfo:
    """Customer information for orders"""
    name: str
    email: str
    phone: str
    address: str
    
    def __post_init__(self):
        """Validate customer information"""
        if not self.name.strip():
            raise ValueError("Customer name is required")
        
        if not self.email.strip() or "@" not in self.email:
            raise ValueError("Valid email is required")
        
        if not self.phone.strip():
            raise ValueError("Phone number is required")
        
        if not self.address.strip():
            raise ValueError("Delivery address is required")


@dataclass
class Order:
    """Order aggregate root"""
    
    id: str = field(default_factory=lambda: f"MCP-ORD-{str(uuid.uuid4())[:8]}")
    customer: CustomerInfo = field(default=None)
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_delivery_time: Optional[datetime] = None
    special_instructions: Optional[str] = None
    
    def __post_init__(self):
        """Validate order after initialization"""
        if not self.items:
            raise ValueError("Order must contain at least one item")
        
        if self.customer is None:
            raise ValueError("Customer information is required")
    
    @property
    def total_amount(self) -> float:
        """Calculate total order amount"""
        return sum(item.total_price for item in self.items)
    
    @property
    def total_items(self) -> int:
        """Get total number of items (including quantities)"""
        return sum(item.quantity for item in self.items)
    
    @property
    def formatted_total(self) -> str:
        """Get formatted total amount"""
        return f"${self.total_amount:.2f}"
    
    @property
    def is_active(self) -> bool:
        """Check if order is active (not delivered or cancelled)"""
        return self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    
    @property
    def estimated_eta(self) -> Optional[str]:
        """Get estimated time of arrival as string"""
        if not self.estimated_delivery_time:
            return None
        
        now = datetime.now()
        if self.estimated_delivery_time <= now:
            return "Ready!"
        
        time_diff = self.estimated_delivery_time - now
        minutes = int(time_diff.total_seconds() / 60)
        
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''}"
    
    def add_item(self, pizza: Pizza, quantity: int = 1, special_instructions: Optional[str] = None):
        """Add an item to the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed order")
        
        # Check if pizza already in order, update quantity
        for item in self.items:
            if item.pizza.id == pizza.id and item.special_instructions == special_instructions:
                item.quantity += quantity
                self.updated_at = datetime.now()
                return
        
        # Add new item
        new_item = OrderItem(pizza=pizza, quantity=quantity, special_instructions=special_instructions)
        self.items.append(new_item)
        self.updated_at = datetime.now()
    
    def remove_item(self, pizza_id: str):
        """Remove an item from the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed order")
        
        self.items = [item for item in self.items if item.pizza.id != pizza_id]
        self.updated_at = datetime.now()
        
        if not self.items:
            raise ValueError("Order cannot be empty")
    
    def confirm_order(self):
        """Confirm the order and set estimated delivery time"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Order is already confirmed")
        
        self.status = OrderStatus.CONFIRMED
        self.updated_at = datetime.now()
        
        # Calculate estimated delivery time (30-45 minutes based on order size)
        base_time = 30  # Base 30 minutes
        additional_time = min(self.total_items * 2, 15)  # Max 15 extra minutes
        total_minutes = base_time + additional_time
        
        self.estimated_delivery_time = datetime.now() + timedelta(minutes=total_minutes)
    
    def update_status(self, new_status: OrderStatus):
        """Update order status with business rules"""
        # Define valid status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.COOKING, OrderStatus.CANCELLED],
            OrderStatus.COOKING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],  # Final state
            OrderStatus.CANCELLED: []   # Final state
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Cannot transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        self.updated_at = datetime.now()
        
        # Adjust delivery time if needed
        if new_status == OrderStatus.READY:
            # If ready earlier than expected, update delivery time
            if self.estimated_delivery_time and datetime.now() < self.estimated_delivery_time:
                self.estimated_delivery_time = datetime.now() + timedelta(minutes=10)
    
    def cancel_order(self, reason: str = "Customer request"):
        """Cancel the order"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel completed or already cancelled order")
        
        if self.status in [OrderStatus.OUT_FOR_DELIVERY]:
            raise ValueError("Cannot cancel order that is out for delivery")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
        self.special_instructions = f"CANCELLED: {reason}" 
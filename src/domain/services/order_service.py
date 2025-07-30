"""
Domain Services - Order Service
Core business logic for order management that doesn't belong to a specific entity.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities import Order, OrderItem, OrderStatus, Pizza, CustomerInfo, User
from ..repositories import IOrderRepository, IPizzaRepository, IUserRepository


class OrderDomainService:
    """Domain service for order-related business logic"""
    
    def __init__(self, 
                 order_repo: IOrderRepository,
                 pizza_repo: IPizzaRepository, 
                 user_repo: IUserRepository):
        self._order_repo = order_repo
        self._pizza_repo = pizza_repo
        self._user_repo = user_repo
    
    async def create_order_from_items(self, 
                                    customer_email: str,
                                    customer_name: str,
                                    customer_phone: str,
                                    customer_address: str,
                                    pizza_items: List[Dict[str, Any]]) -> Order:
        """Create a new order from pizza items"""
        
        # Validate customer info
        customer = CustomerInfo(
            name=customer_name,
            email=customer_email,
            phone=customer_phone,
            address=customer_address
        )
        
        # Create order items
        order_items = []
        for item_data in pizza_items:
            pizza = await self._pizza_repo.get_by_id(item_data['pizza_id'])
            if not pizza:
                raise ValueError(f"Pizza with ID {item_data['pizza_id']} not found")
            
            if not pizza.is_available:
                raise ValueError(f"Pizza {pizza.name} is not available")
            
            order_item = OrderItem(
                pizza=pizza,
                quantity=item_data.get('quantity', 1),
                special_instructions=item_data.get('special_instructions')
            )
            order_items.append(order_item)
        
        # Create order
        order = Order(customer=customer, items=order_items)
        
        # Save order
        saved_order = await self._order_repo.save(order)
        
        # Update user order count if user exists
        user = await self._user_repo.get_by_email(customer_email)
        if user:
            user.record_order()
            await self._user_repo.save(user)
        
        return saved_order
    
    async def find_pizza_and_create_order_item(self, 
                                              pizza_name: str, 
                                              size: str, 
                                              quantity: int = 1) -> OrderItem:
        """Find a pizza by name and size, create order item"""
        
        # Search for pizza by name
        pizzas = await self._pizza_repo.search_by_name(pizza_name)
        
        if not pizzas:
            raise ValueError(f"No pizza found matching '{pizza_name}'")
        
        # Filter by size if specified
        size_lower = size.lower() if size else "large"
        matching_pizza = None
        
        for pizza in pizzas:
            if pizza.size.value.lower() == size_lower:
                matching_pizza = pizza
                break
        
        if not matching_pizza:
            # If no exact size match, use first available
            matching_pizza = pizzas[0]
        
        if not matching_pizza.is_available:
            raise ValueError(f"Pizza {matching_pizza.name} is not available")
        
        return OrderItem(pizza=matching_pizza, quantity=quantity)
    
    async def calculate_delivery_time(self, order: Order) -> datetime:
        """Calculate estimated delivery time based on order complexity"""
        
        # Base preparation time
        base_time = 20  # 20 minutes base
        
        # Add time based on number of items
        item_time = min(order.total_items * 3, 20)  # Max 20 minutes for items
        
        # Add time based on order complexity (different pizza types)
        unique_pizzas = len(set(item.pizza.id for item in order.items))
        complexity_time = min(unique_pizzas * 2, 10)  # Max 10 minutes for complexity
        
        # Peak hours adjustment (11-13, 18-20)
        current_hour = datetime.now().hour
        peak_adjustment = 0
        if current_hour in [11, 12, 18, 19]:
            peak_adjustment = 10  # Add 10 minutes during peak hours
        
        total_minutes = base_time + item_time + complexity_time + peak_adjustment
        
        return datetime.now() + timedelta(minutes=total_minutes)
    
    async def get_order_suggestions(self, customer_email: str) -> List[Pizza]:
        """Get pizza suggestions based on customer order history"""
        
        # Get customer's previous orders
        customer_orders = await self._order_repo.get_by_customer_email(customer_email)
        
        if not customer_orders:
            # New customer - return popular items
            return await self._get_popular_pizzas()
        
        # Get pizzas the customer has ordered before
        ordered_pizza_ids = set()
        for order in customer_orders:
            for item in order.items:
                ordered_pizza_ids.add(item.pizza.id)
        
        # Get those pizzas (if still available)
        previous_pizzas = []
        for pizza_id in ordered_pizza_ids:
            pizza = await self._pizza_repo.get_by_id(pizza_id)
            if pizza and pizza.is_available:
                previous_pizzas.append(pizza)
        
        # If customer has order history, return their favorites
        if previous_pizzas:
            return previous_pizzas[:5]  # Top 5 previous orders
        
        # Fallback to popular pizzas
        return await self._get_popular_pizzas()
    
    async def _get_popular_pizzas(self) -> List[Pizza]:
        """Get popular pizzas (simplified - in real app would use analytics)"""
        all_pizzas = await self._pizza_repo.get_available_pizzas()
        
        # For now, return first 5 available pizzas
        # In a real system, this would be based on order frequency
        return all_pizzas[:5]
    
    async def can_modify_order(self, order_id: str) -> bool:
        """Check if order can be modified"""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            return False
        
        # Orders can only be modified if they're pending or confirmed
        return order.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    async def can_cancel_order(self, order_id: str) -> bool:
        """Check if order can be cancelled"""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            return False
        
        # Orders can be cancelled unless they're out for delivery or already delivered
        return order.status not in [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    
    async def get_order_progress(self, order_id: str) -> Dict[str, Any]:
        """Get detailed order progress information"""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Calculate progress percentage
        status_progression = {
            OrderStatus.PENDING: 0,
            OrderStatus.CONFIRMED: 20,
            OrderStatus.PREPARING: 40,
            OrderStatus.COOKING: 60,
            OrderStatus.READY: 80,
            OrderStatus.OUT_FOR_DELIVERY: 90,
            OrderStatus.DELIVERED: 100,
            OrderStatus.CANCELLED: 0
        }
        
        progress_percentage = status_progression.get(order.status, 0)
        
        return {
            "order_id": order.id,
            "status": order.status.value,
            "progress_percentage": progress_percentage,
            "estimated_eta": order.estimated_eta,
            "is_active": order.is_active,
            "total_amount": order.formatted_total,
            "items_count": order.total_items,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        } 
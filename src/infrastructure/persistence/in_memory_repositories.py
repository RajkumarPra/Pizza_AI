"""
Infrastructure - In-Memory Repository Implementations
Concrete implementations of domain repository interfaces using in-memory storage.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import Pizza, Order, User, PizzaSize, PizzaCategory, OrderStatus
from ...domain.repositories import IPizzaRepository, IOrderRepository, IUserRepository
from ...domain.data.menu_data import get_default_menu


class InMemoryPizzaRepository(IPizzaRepository):
    """In-memory implementation of pizza repository"""
    
    def __init__(self):
        self._pizzas: Dict[str, Pizza] = {}
        # Load default menu
        for pizza in get_default_menu():
            self._pizzas[pizza.id] = pizza
    
    async def get_all(self) -> List[Pizza]:
        """Get all pizzas"""
        return list(self._pizzas.values())
    
    async def get_by_id(self, pizza_id: str) -> Optional[Pizza]:
        """Get pizza by ID"""
        return self._pizzas.get(pizza_id)
    
    async def get_by_category(self, category: PizzaCategory) -> List[Pizza]:
        """Get pizzas by category"""
        return [pizza for pizza in self._pizzas.values() if pizza.category == category]
    
    async def get_by_size(self, size: PizzaSize) -> List[Pizza]:
        """Get pizzas by size"""
        return [pizza for pizza in self._pizzas.values() if pizza.size == size]
    
    async def search_by_name(self, name: str) -> List[Pizza]:
        """Search pizzas by name (fuzzy matching)"""
        name_lower = name.lower()
        matches = []
        
        for pizza in self._pizzas.values():
            # Exact name match
            if name_lower in pizza.name.lower():
                matches.append(pizza)
            # Word-based matching
            elif any(word in pizza.name.lower() for word in name_lower.split()):
                matches.append(pizza)
        
        return matches
    
    async def search_by_ingredients(self, ingredient: str) -> List[Pizza]:
        """Search pizzas by ingredient"""
        ingredient_lower = ingredient.lower()
        return [
            pizza for pizza in self._pizzas.values()
            if any(ingredient_lower in ing.lower() for ing in pizza.ingredients)
        ]
    
    async def get_available_pizzas(self) -> List[Pizza]:
        """Get only available pizzas"""
        return [pizza for pizza in self._pizzas.values() if pizza.is_available]
    
    async def add(self, pizza: Pizza) -> Pizza:
        """Add a new pizza"""
        self._pizzas[pizza.id] = pizza
        return pizza
    
    async def update(self, pizza: Pizza) -> Pizza:
        """Update existing pizza"""
        if pizza.id not in self._pizzas:
            raise ValueError(f"Pizza with ID {pizza.id} not found")
        self._pizzas[pizza.id] = pizza
        return pizza
    
    async def delete(self, pizza_id: str) -> bool:
        """Delete pizza by ID"""
        if pizza_id in self._pizzas:
            del self._pizzas[pizza_id]
            return True
        return False
    
    async def set_availability(self, pizza_id: str, is_available: bool) -> bool:
        """Set pizza availability"""
        if pizza_id in self._pizzas:
            self._pizzas[pizza_id].is_available = is_available
            return True
        return False


class InMemoryOrderRepository(IOrderRepository):
    """In-memory implementation of order repository"""
    
    def __init__(self):
        self._orders: Dict[str, Order] = {}
    
    async def save(self, order: Order) -> Order:
        """Save an order (create or update)"""
        self._orders[order.id] = order
        return order
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)
    
    async def get_by_customer_email(self, email: str) -> List[Order]:
        """Get all orders for a customer by email"""
        email_lower = email.lower()
        return [
            order for order in self._orders.values()
            if order.customer.email.lower() == email_lower
        ]
    
    async def get_active_orders(self) -> List[Order]:
        """Get all active orders (not delivered or cancelled)"""
        return [order for order in self._orders.values() if order.is_active]
    
    async def get_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status"""
        return [order for order in self._orders.values() if order.status == status]
    
    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders"""
        sorted_orders = sorted(
            self._orders.values(),
            key=lambda o: o.created_at,
            reverse=True
        )
        return sorted_orders[:limit]
    
    async def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Get orders within date range"""
        return [
            order for order in self._orders.values()
            if start_date <= order.created_at <= end_date
        ]
    
    async def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update order status"""
        if order_id in self._orders:
            self._orders[order_id].update_status(status)
            return True
        return False
    
    async def delete(self, order_id: str) -> bool:
        """Delete order by ID"""
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False
    
    async def get_customer_order_count(self, email: str) -> int:
        """Get total order count for a customer"""
        email_lower = email.lower()
        return len([
            order for order in self._orders.values()
            if order.customer.email.lower() == email_lower
        ])


class InMemoryUserRepository(IUserRepository):
    """In-memory implementation of user repository"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
    
    async def save(self, user: User) -> User:
        """Save a user (create or update)"""
        self._users[user.email.lower()] = user
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        for user in self._users.values():
            if user.id == user_id:
                return user
        return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self._users.get(email.lower())
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        return email.lower() in self._users
    
    async def get_all_active(self) -> List[User]:
        """Get all active users"""
        return [user for user in self._users.values() if user.is_active]
    
    async def get_frequent_customers(self, min_orders: int = 5) -> List[User]:
        """Get frequent customers"""
        return [user for user in self._users.values() if user.total_orders >= min_orders]
    
    async def search_by_name(self, name: str) -> List[User]:
        """Search users by name"""
        name_lower = name.lower()
        return [
            user for user in self._users.values()
            if user.name and name_lower in user.name.lower()
        ]
    
    async def update_order_count(self, user_id: str) -> bool:
        """Increment user's order count"""
        for user in self._users.values():
            if user.id == user_id:
                user.record_order()
                return True
        return False
    
    async def deactivate(self, user_id: str) -> bool:
        """Deactivate user account"""
        for user in self._users.values():
            if user.id == user_id:
                user.deactivate()
                return True
        return False
    
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        email_to_delete = None
        for email, user in self._users.items():
            if user.id == user_id:
                email_to_delete = email
                break
        
        if email_to_delete:
            del self._users[email_to_delete]
            return True
        return False 
"""
Domain Repository Interfaces - Order Repository
Abstract interfaces for order data access.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities import Order, OrderStatus


class IOrderRepository(ABC):
    """Abstract interface for order data access"""
    
    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Save an order (create or update)"""
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_by_customer_email(self, email: str) -> List[Order]:
        """Get all orders for a customer by email"""
        pass
    
    @abstractmethod
    async def get_active_orders(self) -> List[Order]:
        """Get all active orders (not delivered or cancelled)"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status"""
        pass
    
    @abstractmethod
    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders"""
        pass
    
    @abstractmethod
    async def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Get orders within date range"""
        pass
    
    @abstractmethod
    async def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update order status"""
        pass
    
    @abstractmethod
    async def delete(self, order_id: str) -> bool:
        """Delete order by ID"""
        pass
    
    @abstractmethod
    async def get_customer_order_count(self, email: str) -> int:
        """Get total order count for a customer"""
        pass 
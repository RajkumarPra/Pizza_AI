"""
Domain Repository Interfaces - User Repository
Abstract interfaces for user data access.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import User


class IUserRepository(ABC):
    """Abstract interface for user data access"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a user (create or update)"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[User]:
        """Get all active users"""
        pass
    
    @abstractmethod
    async def get_frequent_customers(self, min_orders: int = 5) -> List[User]:
        """Get frequent customers"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str) -> List[User]:
        """Search users by name"""
        pass
    
    @abstractmethod
    async def update_order_count(self, user_id: str) -> bool:
        """Increment user's order count"""
        pass
    
    @abstractmethod
    async def deactivate(self, user_id: str) -> bool:
        """Deactivate user account"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass 
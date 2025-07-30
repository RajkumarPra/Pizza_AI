"""
Domain Repository Interfaces - Pizza Repository
Abstract interfaces that define contracts for data access, following dependency inversion principle.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Pizza, PizzaSize, PizzaCategory


class IPizzaRepository(ABC):
    """Abstract interface for pizza data access"""
    
    @abstractmethod
    async def get_all(self) -> List[Pizza]:
        """Get all available pizzas"""
        pass
    
    @abstractmethod
    async def get_by_id(self, pizza_id: str) -> Optional[Pizza]:
        """Get pizza by ID"""
        pass
    
    @abstractmethod
    async def get_by_category(self, category: PizzaCategory) -> List[Pizza]:
        """Get pizzas by category"""
        pass
    
    @abstractmethod
    async def get_by_size(self, size: PizzaSize) -> List[Pizza]:
        """Get pizzas by size"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str) -> List[Pizza]:
        """Search pizzas by name (fuzzy matching)"""
        pass
    
    @abstractmethod
    async def search_by_ingredients(self, ingredient: str) -> List[Pizza]:
        """Search pizzas by ingredient"""
        pass
    
    @abstractmethod
    async def get_available_pizzas(self) -> List[Pizza]:
        """Get only available pizzas"""
        pass
    
    @abstractmethod
    async def add(self, pizza: Pizza) -> Pizza:
        """Add a new pizza"""
        pass
    
    @abstractmethod
    async def update(self, pizza: Pizza) -> Pizza:
        """Update existing pizza"""
        pass
    
    @abstractmethod
    async def delete(self, pizza_id: str) -> bool:
        """Delete pizza by ID"""
        pass
    
    @abstractmethod
    async def set_availability(self, pizza_id: str, is_available: bool) -> bool:
        """Set pizza availability"""
        pass 
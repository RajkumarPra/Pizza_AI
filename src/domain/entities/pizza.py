"""
Domain Entities - Pizza
Core business entities that represent the fundamental concepts of the pizza business.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class PizzaSize(Enum):
    """Pizza size enumeration"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class PizzaCategory(Enum):
    """Pizza category enumeration"""
    VEG = "veg"
    NON_VEG = "non-veg"


@dataclass
class Pizza:
    """Pizza entity representing a pizza item"""
    
    id: str
    name: str
    size: PizzaSize
    price: float
    category: PizzaCategory
    description: str
    ingredients: List[str]
    is_available: bool = True
    
    def __post_init__(self):
        """Validate pizza data after initialization"""
        if self.price <= 0:
            raise ValueError("Pizza price must be positive")
        
        if not self.name.strip():
            raise ValueError("Pizza name cannot be empty")
        
        if not self.ingredients:
            raise ValueError("Pizza must have at least one ingredient")
    
    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        return f"{self.name} ({self.size.value.title()})"
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price string"""
        return f"${self.price:.2f}"
    
    def is_vegetarian(self) -> bool:
        """Check if pizza is vegetarian"""
        return self.category == PizzaCategory.VEG
    
    def matches_search(self, query: str) -> bool:
        """Check if pizza matches search query"""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower() or
            any(query_lower in ingredient.lower() for ingredient in self.ingredients)
        ) 
"""
Domain Repository Interfaces
Abstract interfaces that define contracts for data access, following dependency inversion principle.
"""

from .pizza_repository import IPizzaRepository
from .order_repository import IOrderRepository  
from .user_repository import IUserRepository

__all__ = [
    'IPizzaRepository',
    'IOrderRepository',
    'IUserRepository',
] 
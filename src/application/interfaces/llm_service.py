"""
Application Interfaces - LLM Service
Interface for LLM integration following dependency inversion principle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ...domain.entities import Order, Pizza


class ILLMService(ABC):
    """Abstract interface for LLM service integration"""
    
    @abstractmethod
    async def parse_user_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user message to determine intent and extract parameters"""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a response using the LLM"""
        pass
    
    @abstractmethod
    async def generate_order_confirmation_message(self, order: Order) -> str:
        """Generate order confirmation message"""
        pass
    
    @abstractmethod
    async def generate_tracking_message(self, order: Order) -> str:
        """Generate order tracking message"""
        pass
    
    @abstractmethod
    async def generate_suggestions_message(self, pizzas: List[Pizza], preferences: str) -> str:
        """Generate pizza suggestions message"""
        pass
    
    @abstractmethod
    async def generate_welcome_message(self, user_name: Optional[str] = None, is_new_user: bool = False) -> str:
        """Generate welcome message"""
        pass
    
    @abstractmethod
    async def generate_error_message(self, error: str, context: Dict[str, Any] = None) -> str:
        """Generate user-friendly error message"""
        pass 
"""
Infrastructure - Dependency Injection Container
Sets up all dependencies following clean architecture principles.
"""

from typing import Optional

from ..application.interfaces import ILLMService
from ..application.use_cases.order_use_cases import OrderUseCases
from ..domain.repositories import IPizzaRepository, IOrderRepository, IUserRepository
from ..domain.services.order_service import OrderDomainService

from .external.groq_llm_service import GroqLLMService
from .persistence.in_memory_repositories import (
    InMemoryPizzaRepository, 
    InMemoryOrderRepository, 
    InMemoryUserRepository
)


class DIContainer:
    """Dependency injection container for the application"""
    
    def __init__(self):
        self._pizza_repository: Optional[IPizzaRepository] = None
        self._order_repository: Optional[IOrderRepository] = None
        self._user_repository: Optional[IUserRepository] = None
        self._llm_service: Optional[ILLMService] = None
        self._order_domain_service: Optional[OrderDomainService] = None
        self._order_use_cases: Optional[OrderUseCases] = None
    
    # Repository implementations
    def get_pizza_repository(self) -> IPizzaRepository:
        if self._pizza_repository is None:
            self._pizza_repository = InMemoryPizzaRepository()
        return self._pizza_repository
    
    def get_order_repository(self) -> IOrderRepository:
        if self._order_repository is None:
            self._order_repository = InMemoryOrderRepository()
        return self._order_repository
    
    def get_user_repository(self) -> IUserRepository:
        if self._user_repository is None:
            self._user_repository = InMemoryUserRepository()
        return self._user_repository
    
    # External service implementations
    def get_llm_service(self) -> ILLMService:
        if self._llm_service is None:
            self._llm_service = GroqLLMService()
        return self._llm_service
    
    # Domain services
    def get_order_domain_service(self) -> OrderDomainService:
        if self._order_domain_service is None:
            self._order_domain_service = OrderDomainService(
                order_repo=self.get_order_repository(),
                pizza_repo=self.get_pizza_repository(),
                user_repo=self.get_user_repository()
            )
        return self._order_domain_service
    
    # Application use cases
    def get_order_use_cases(self) -> OrderUseCases:
        if self._order_use_cases is None:
            self._order_use_cases = OrderUseCases(
                order_repo=self.get_order_repository(),
                pizza_repo=self.get_pizza_repository(),
                user_repo=self.get_user_repository(),
                llm_service=self.get_llm_service()
            )
        return self._order_use_cases


# Global container instance
container = DIContainer() 
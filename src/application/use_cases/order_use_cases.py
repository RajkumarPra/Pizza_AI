"""
Application Use Cases - Order Management
Application-specific business rules and use cases that orchestrate domain entities and services.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..interfaces import ILLMService
from ...domain.entities import Order, OrderStatus, Pizza
from ...domain.repositories import IOrderRepository, IPizzaRepository, IUserRepository
from ...domain.services.order_service import OrderDomainService


@dataclass
class OrderRequest:
    """Request model for creating orders"""
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: str
    items: List[str]  # Pizza names or IDs


@dataclass 
class OrderResponse:
    """Response model for order operations"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    order_details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OrderUseCases:
    """Application use cases for order management"""
    
    def __init__(self,
                 order_repo: IOrderRepository,
                 pizza_repo: IPizzaRepository,
                 user_repo: IUserRepository,
                 llm_service: ILLMService):
        self._order_repo = order_repo
        self._pizza_repo = pizza_repo
        self._user_repo = user_repo
        self._llm_service = llm_service
        self._order_service = OrderDomainService(order_repo, pizza_repo, user_repo)
    
    async def place_order(self, request: OrderRequest) -> OrderResponse:
        """Place a new pizza order"""
        try:
            # Convert item names to pizza items
            pizza_items = []
            for item_name in request.items:
                # Try to find pizza by name
                pizzas = await self._pizza_repo.search_by_name(item_name)
                if not pizzas:
                    return OrderResponse(
                        success=False,
                        error=f"Pizza '{item_name}' not found"
                    )
                
                pizza = pizzas[0]  # Take first match
                pizza_items.append({
                    'pizza_id': pizza.id,
                    'quantity': 1
                })
            
            # Create order using domain service
            order = await self._order_service.create_order_from_items(
                customer_email=request.customer_email,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone,
                customer_address=request.customer_address,
                pizza_items=pizza_items
            )
            
            # Confirm order and calculate delivery time
            order.confirm_order()
            estimated_time = await self._order_service.calculate_delivery_time(order)
            order.estimated_delivery_time = estimated_time
            
            # Save updated order
            await self._order_repo.save(order)
            
            # Generate success message using LLM
            message = await self._llm_service.generate_order_confirmation_message(order)
            
            return OrderResponse(
                success=True,
                order_id=order.id,
                message=message,
                order_details={
                    "order_id": order.id,
                    "total_amount": order.formatted_total,
                    "estimated_delivery": order.estimated_eta,
                    "items": [item.display_name for item in order.items]
                }
            )
            
        except Exception as e:
            return OrderResponse(
                success=False,
                error=str(e)
            )
    
    async def track_order(self, order_id: Optional[str] = None, 
                         customer_email: Optional[str] = None) -> OrderResponse:
        """Track an order by ID or customer email"""
        try:
            order = None
            
            if order_id:
                order = await self._order_repo.get_by_id(order_id)
            elif customer_email:
                # Get most recent order for customer
                orders = await self._order_repo.get_by_customer_email(customer_email)
                if orders:
                    # Sort by creation date and get the most recent
                    orders.sort(key=lambda o: o.created_at, reverse=True)
                    order = orders[0]
            
            if not order:
                return OrderResponse(
                    success=False,
                    error="Order not found"
                )
            
            # Get detailed progress
            progress = await self._order_service.get_order_progress(order.id)
            
            # Generate tracking message using LLM
            message = await self._llm_service.generate_tracking_message(order)
            
            return OrderResponse(
                success=True,
                order_id=order.id,
                message=message,
                order_details=progress
            )
            
        except Exception as e:
            return OrderResponse(
                success=False,
                error=str(e)
            )
    
    async def find_pizza(self, name: str, size: str = "large") -> Dict[str, Any]:
        """Find pizza by name and size"""
        try:
            # Search for pizzas by name
            pizzas = await self._pizza_repo.search_by_name(name)
            
            if not pizzas:
                # Try ingredient search as fallback
                pizzas = await self._pizza_repo.search_by_ingredients(name)
            
            if not pizzas:
                return {
                    "success": False,
                    "error": f"No pizza found matching '{name}'"
                }
            
            # Filter by size if specified
            matching_pizza = None
            for pizza in pizzas:
                if pizza.size.value.lower() == size.lower():
                    matching_pizza = pizza
                    break
            
            if not matching_pizza:
                matching_pizza = pizzas[0]  # Use first match if size not found
            
            return {
                "success": True,
                "pizza": {
                    "id": matching_pizza.id,
                    "name": matching_pizza.display_name,
                    "price": matching_pizza.formatted_price,
                    "description": matching_pizza.description,
                    "ingredients": matching_pizza.ingredients,
                    "available": matching_pizza.is_available
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_menu(self, category: str = "all") -> Dict[str, Any]:
        """Get pizza menu"""
        try:
            if category.lower() == "all":
                pizzas = await self._pizza_repo.get_available_pizzas()
            else:
                from ...domain.entities import PizzaCategory
                cat = PizzaCategory.VEG if category.lower() == "veg" else PizzaCategory.NON_VEG
                pizzas = await self._pizza_repo.get_by_category(cat)
                # Filter only available ones
                pizzas = [p for p in pizzas if p.is_available]
            
            menu_items = []
            for pizza in pizzas:
                menu_items.append({
                    "id": pizza.id,
                    "name": pizza.display_name,
                    "price": pizza.formatted_price,
                    "description": pizza.description,
                    "category": pizza.category.value,
                    "ingredients": pizza.ingredients
                })
            
            return {
                "success": True,
                "category": category,
                "items": menu_items,
                "total_items": len(menu_items)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_suggestions(self, customer_email: Optional[str] = None, 
                            preferences: str = "popular") -> Dict[str, Any]:
        """Get pizza suggestions"""
        try:
            if customer_email:
                # Personalized suggestions based on order history
                suggestions = await self._order_service.get_order_suggestions(customer_email)
            else:
                # Popular pizzas for new customers
                suggestions = await self._pizza_repo.get_available_pizzas()
                suggestions = suggestions[:5]  # Top 5
            
            suggestion_items = []
            for pizza in suggestions:
                suggestion_items.append({
                    "id": pizza.id,
                    "name": pizza.display_name,
                    "price": pizza.formatted_price,
                    "description": pizza.description,
                    "category": pizza.category.value
                })
            
            # Generate suggestions message using LLM
            message = await self._llm_service.generate_suggestions_message(suggestions, preferences)
            
            return {
                "success": True,
                "message": message,
                "suggestions": suggestion_items
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 
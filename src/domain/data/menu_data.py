"""
Domain Data - Menu
Pizza menu data converted to domain entities.
"""

from typing import List
from ..entities import Pizza, PizzaSize, PizzaCategory


def get_default_menu() -> List[Pizza]:
    """Get the default pizza menu as domain entities"""
    
    return [
        # Vegetarian Pizzas
        Pizza(
            id="pizza_1",
            name="Margherita",
            size=PizzaSize.LARGE,
            price=8.99,
            category=PizzaCategory.VEG,
            description="Fresh tomato sauce, mozzarella, and basil",
            ingredients=["tomato sauce", "mozzarella", "basil"],
            is_available=True
        ),
        Pizza(
            id="pizza_2",
            name="Veggie Supreme",
            size=PizzaSize.MEDIUM,
            price=9.25,
            category=PizzaCategory.VEG,
            description="Bell peppers, mushrooms, onions, olives, and tomatoes",
            ingredients=["bell peppers", "mushrooms", "onions", "olives", "tomatoes"],
            is_available=True
        ),
        Pizza(
            id="pizza_3",
            name="Paneer Tikka",
            size=PizzaSize.LARGE,
            price=11.25,
            category=PizzaCategory.VEG,
            description="Spiced paneer, bell peppers, onions, and tikka sauce",
            ingredients=["paneer", "bell peppers", "onions", "tikka sauce", "spices"],
            is_available=True
        ),
        Pizza(
            id="pizza_4",
            name="Mushroom Delight",
            size=PizzaSize.SMALL,
            price=7.99,
            category=PizzaCategory.VEG,
            description="Mixed mushrooms, garlic, herbs, and cheese",
            ingredients=["mushrooms", "garlic", "herbs", "cheese"],
            is_available=True
        ),
        
        # Non-Vegetarian Pizzas
        Pizza(
            id="pizza_5",
            name="Pepperoni Classic",
            size=PizzaSize.MEDIUM,
            price=10.49,
            category=PizzaCategory.NON_VEG,
            description="Classic pepperoni with mozzarella cheese",
            ingredients=["pepperoni", "mozzarella cheese"],
            is_available=True
        ),
        Pizza(
            id="pizza_6",
            name="BBQ Chicken",
            size=PizzaSize.LARGE,
            price=12.99,
            category=PizzaCategory.NON_VEG,
            description="BBQ sauce, grilled chicken, red onions, and cilantro",
            ingredients=["BBQ sauce", "grilled chicken", "red onions", "cilantro"],
            is_available=True
        ),
        Pizza(
            id="pizza_7",
            name="Meat Lovers",
            size=PizzaSize.LARGE,
            price=14.99,
            category=PizzaCategory.NON_VEG,
            description="Pepperoni, sausage, ham, and bacon",
            ingredients=["pepperoni", "sausage", "ham", "bacon"],
            is_available=True
        ),
        Pizza(
            id="pizza_8",
            name="Chicken Supreme",
            size=PizzaSize.MEDIUM,
            price=11.99,
            category=PizzaCategory.NON_VEG,
            description="Grilled chicken, mushrooms, peppers, and onions",
            ingredients=["grilled chicken", "mushrooms", "peppers", "onions"],
            is_available=True
        ),
    ]


# Legacy mapping for backward compatibility
LEGACY_MENU_MAPPING = {
    "margherita": "pizza_1",
    "margarita": "pizza_1", 
    "classic": "pizza_1",
    "veggie": "pizza_2",
    "vegetable": "pizza_2",
    "veg supreme": "pizza_2",
    "paneer": "pizza_3",
    "paneer tikka": "pizza_3",
    "indian": "pizza_3",
    "mushroom": "pizza_4",
    "fungi": "pizza_4",
    "pepperoni": "pizza_5",
    "classic pepperoni": "pizza_5", 
    "bbq": "pizza_6",
    "bbq chicken": "pizza_6",
    "chicken bbq": "pizza_6",
    "barbecue": "pizza_6",
    "meat lovers": "pizza_7",
    "meat": "pizza_7",
    "carnivore": "pizza_7",
    "chicken supreme": "pizza_8",
    "chicken": "pizza_8",
    "supreme": "pizza_8"
} 
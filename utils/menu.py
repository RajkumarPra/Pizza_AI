from typing import Optional, List
import difflib

# 🍕 Pizza-Only Menu (Veg and Non-Veg)
MENU = [
    # Vegetarian Pizzas
    {"id": "1", "name": "Margherita", "size": "Large", "price": 8.99, "description": "Fresh tomato sauce, mozzarella, and basil", "category": "veg", "aliases": ["margherita", "margarita", "classic"]},
    {"id": "3", "name": "Veggie Supreme", "size": "Medium", "price": 9.25, "description": "Bell peppers, mushrooms, onions, olives, and tomatoes", "category": "veg", "aliases": ["veggie", "vegetable", "veg supreme"]},
    {"id": "5", "name": "Paneer Tikka", "size": "Large", "price": 11.25, "description": "Spiced paneer, bell peppers, onions, and tikka sauce", "category": "veg", "aliases": ["paneer", "paneer tikka", "indian"]},
    {"id": "7", "name": "Mushroom Delight", "size": "Small", "price": 7.99, "description": "Mixed mushrooms, garlic, herbs, and cheese", "category": "veg", "aliases": ["mushroom", "fungi"]},
    
    # Non-Vegetarian Pizzas
    {"id": "2", "name": "Pepperoni Classic", "size": "Medium", "price": 10.49, "description": "Classic pepperoni with mozzarella cheese", "category": "non-veg", "aliases": ["pepperoni", "classic pepperoni"]},
    {"id": "4", "name": "BBQ Chicken", "size": "Large", "price": 12.99, "description": "BBQ sauce, grilled chicken, red onions, and cilantro", "category": "non-veg", "aliases": ["bbq", "bbq chicken", "chicken bbq", "barbecue"]},
    {"id": "6", "name": "Meat Lovers", "size": "Large", "price": 14.99, "description": "Pepperoni, sausage, ham, and bacon", "category": "non-veg", "aliases": ["meat lovers", "meat", "carnivore"]},
    {"id": "8", "name": "Chicken Supreme", "size": "Medium", "price": 11.99, "description": "Grilled chicken, mushrooms, peppers, and onions", "category": "non-veg", "aliases": ["chicken supreme", "chicken", "supreme"]},
]

# ✅ Check if a pizza name + size exists in the menu (legacy function)
def is_pizza_available(name: str, size: str) -> bool:
    """Legacy function for basic pizza availability check"""
    for item in MENU:
        if item["name"].lower() == name.lower() and item["size"].lower() == size.lower():
            return True
    return False

# ✅ Suggest closest matching pizza name+size using fuzzy matching (legacy function)
def suggest_similar_pizza(name: str, size: str) -> Optional[str]:
    """Legacy function for basic pizza suggestions"""
    menu_names = [f"{item['size']} {item['name']}" for item in MENU]
    user_combo = f"{size} {name}"
    match = difflib.get_close_matches(user_combo, menu_names, n=1, cutoff=0.5)
    return match[0] if match else None

# 🆕 Enhanced MCP Functions

def find_menu_item(name: str, size: str = None) -> Optional[dict]:
    """Find a menu item by name and optionally size - enhanced MCP version"""
    name_lower = name.lower()
    
    for item in MENU:
        # Check exact name match
        if item["name"].lower() == name_lower:
            if size is None or item["size"].lower() == size.lower():
                return item
        
        # Check aliases
        if "aliases" in item:
            for alias in item["aliases"]:
                if alias.lower() == name_lower:
                    if size is None or item["size"].lower() == size.lower():
                        return item
    
    return None

def suggest_similar_items(name: str, size: str = None) -> List[dict]:
    """Suggest similar items when exact match not found - enhanced MCP version"""
    suggestions = []
    name_lower = name.lower()
    
    # Find items with similar names
    for item in MENU:
        # Check if any word in the item name matches
        item_words = item["name"].lower().split()
        name_words = name_lower.split()
        
        if any(word in item_words for word in name_words) or any(word in name_words for word in item_words):
            suggestions.append(item)
        
        # Check aliases
        if "aliases" in item:
            for alias in item["aliases"]:
                if any(word in alias.lower() for word in name_words):
                    suggestions.append(item)
                    break
    
    # Remove duplicates and limit to 3 suggestions
    seen = set()
    unique_suggestions = []
    for item in suggestions:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique_suggestions.append(item)
        if len(unique_suggestions) >= 3:
            break
    
    return unique_suggestions

def get_menu_by_category(category: str = None) -> List[dict]:
    """Get menu items filtered by category (veg or non-veg only)"""
    if category is None:
        return MENU
    
    return [item for item in MENU if item["category"] == category.lower()]

def get_all_categories() -> List[str]:
    """Get all available menu categories (veg and non-veg only)"""
    categories = set()
    for item in MENU:
        categories.add(item["category"])
    return list(categories)

# ✅ Print menu to CLI
def print_menu():
    """Print the complete pizza menu organized by categories"""
    print("\n📋 Pizza AI Menu:")
    
    categories = {
        "veg": "🥗 Vegetarian Pizzas",
        "non-veg": "🍖 Non-Vegetarian Pizzas"
    }
    
    for category_key, category_name in categories.items():
        items = get_menu_by_category(category_key)
        if items:
            print(f"\n{category_name}:")
            for item in items:
                print(f"  🧾 {item['name']} ({item['size']}) - ${item['price']}")
                print(f"     {item['description']}")

def print_menu_simple():
    """Print a simple menu list (legacy format)"""
    print("\n📋 Pizza Menu:")
    for item in MENU:
        print(f"🧾 {item['size']} {item['name']} - ${item['price']}")

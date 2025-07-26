import random
from datetime import datetime, timedelta

def schedule_delivery(order_data: dict) -> dict:
    """Schedule delivery for an order and return ETA information"""
    if not order_data.get("order_id"):
        return {
            "status": "error",
            "message": "Missing order_id for scheduling"
        }

    # Enhanced ETA calculation based on order status
    order_status = order_data.get("status", "placed")
    
    if order_status == "placed":
        eta_minutes = random.randint(25, 35)
    elif order_status == "preparing":
        eta_minutes = random.randint(15, 25)
    elif order_status == "cooking":
        eta_minutes = random.randint(8, 15)
    elif order_status == "ready":
        eta_minutes = random.randint(3, 8)
    elif order_status == "delivered":
        eta_minutes = 0
    else:
        eta_minutes = random.randint(20, 40)

    now = datetime.now()
    delivery_time = now + timedelta(minutes=eta_minutes)
    delivery_slot = delivery_time.strftime("%I:%M %p")

    return {
        "order_id": order_data["order_id"],
        "status": "scheduled",
        "eta_minutes": eta_minutes,
        "delivery_slot": delivery_slot,
        "current_status": order_status,
        "message": f"Your order is scheduled for delivery at {delivery_slot}."
    }

def get_eta(order_data: dict) -> dict:
    """Get current ETA for an order based on its status"""
    if not order_data.get("order_id"):
        return {
            "status": "error",
            "message": "Missing order_id for ETA calculation"
        }
    
    order_status = order_data.get("status", "placed")
    order_id = order_data["order_id"]
    
    # Calculate ETA based on current status
    if order_status == "placed":
        eta_minutes = random.randint(25, 35)
        message = f"Your order #{order_id} has been placed. Estimated delivery: {eta_minutes} minutes."
    elif order_status == "preparing":
        eta_minutes = random.randint(15, 25)
        message = f"Your order #{order_id} is being prepared. Estimated delivery: {eta_minutes} minutes."
    elif order_status == "cooking":
        eta_minutes = random.randint(8, 15)
        message = f"Your order #{order_id} is cooking in the oven! Estimated delivery: {eta_minutes} minutes."
    elif order_status == "ready":
        eta_minutes = random.randint(3, 8)
        message = f"Your order #{order_id} is ready! It will arrive in approximately {eta_minutes} minutes."
    elif order_status == "delivered":
        eta_minutes = 0
        message = f"Your order #{order_id} has been delivered! Enjoy your meal!"
    else:
        eta_minutes = random.randint(20, 40)
        message = f"Your order #{order_id} is being processed. Estimated delivery: {eta_minutes} minutes."
    
    now = datetime.now()
    if eta_minutes > 0:
        delivery_time = now + timedelta(minutes=eta_minutes)
        delivery_slot = delivery_time.strftime("%I:%M %p")
    else:
        delivery_slot = "Delivered"
    
    return {
        "order_id": order_id,
        "status": "calculated",
        "eta_minutes": eta_minutes,
        "delivery_slot": delivery_slot,
        "current_status": order_status,
        "message": message,
        "eta_text": f"{eta_minutes} minutes" if eta_minutes > 0 else "Delivered"
    }

def update_order_status(order_data: dict, new_status: str) -> dict:
    """Update order status and recalculate ETA"""
    if not order_data.get("order_id"):
        return {
            "status": "error",
            "message": "Missing order_id for status update"
        }
    
    order_data["status"] = new_status
    eta_info = get_eta(order_data)
    
    return {
        "order_id": order_data["order_id"],
        "old_status": order_data.get("previous_status", "unknown"),
        "new_status": new_status,
        "eta_info": eta_info,
        "message": f"Order status updated to {new_status}. {eta_info['message']}"
    }

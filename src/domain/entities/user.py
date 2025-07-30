"""
Domain Entities - User
User management entities and business rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid
import re


@dataclass
class User:
    """User entity representing a customer"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    phone: Optional[str] = None
    default_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_order_at: Optional[datetime] = None
    total_orders: int = 0
    is_active: bool = True
    preferences: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate user data after initialization"""
        if not self.email:
            raise ValueError("Email is required")
        
        if not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")
        
        if self.name and len(self.name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        
        if self.phone and not self._is_valid_phone(self.phone):
            raise ValueError("Invalid phone number format")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it has 10 digits (US format) or 11 digits (with country code)
        return len(digits_only) in [10, 11]
    
    @property
    def display_name(self) -> str:
        """Get display name for the user"""
        if self.name:
            return self.name
        else:
            # Use email prefix if no name provided
            return self.email.split('@')[0]
    
    @property
    def is_new_customer(self) -> bool:
        """Check if user is a new customer"""
        return self.total_orders == 0
    
    @property
    def is_frequent_customer(self) -> bool:
        """Check if user is a frequent customer"""
        return self.total_orders >= 5
    
    @property
    def formatted_phone(self) -> Optional[str]:
        """Get formatted phone number"""
        if not self.phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', self.phone)
        
        if len(digits) == 10:
            # Format as (XXX) XXX-XXXX
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11:
            # Format as +X (XXX) XXX-XXXX
            return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return self.phone  # Return original if unexpected format
    
    def update_profile(self, name: Optional[str] = None, phone: Optional[str] = None, 
                      default_address: Optional[str] = None):
        """Update user profile information"""
        if name is not None:
            if len(name.strip()) < 2:
                raise ValueError("Name must be at least 2 characters")
            self.name = name.strip()
        
        if phone is not None:
            if phone and not self._is_valid_phone(phone):
                raise ValueError("Invalid phone number format")
            self.phone = phone
        
        if default_address is not None:
            self.default_address = default_address.strip() if default_address else None
    
    def add_preference(self, preference: str):
        """Add a preference for the user"""
        preference = preference.strip().lower()
        if preference and preference not in self.preferences:
            self.preferences.append(preference)
    
    def remove_preference(self, preference: str):
        """Remove a preference for the user"""
        preference = preference.strip().lower()
        if preference in self.preferences:
            self.preferences.remove(preference)
    
    def record_order(self):
        """Record that user has placed an order"""
        self.total_orders += 1
        self.last_order_at = datetime.now()
    
    def deactivate(self):
        """Deactivate the user account"""
        self.is_active = False
    
    def reactivate(self):
        """Reactivate the user account"""
        self.is_active = True 
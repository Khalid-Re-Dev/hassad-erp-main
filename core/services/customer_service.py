"""
Customer Service Layer.

Provides business logic and CRUD operations for Customer management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Customer


class CustomerService(BaseService):
    """
    Customer service for managing customer records.
    
    Handles:
    - Customer CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize customer service."""
        super().__init__(Customer)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Customer] = None
    ) -> List[ValidationError]:
        """
        Validate customer data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing customer instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['name', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'name': 255, 'email': 255, 'phone': 50, 'address': 500, 'city': 100, 'tax_number': 50}
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors


# Singleton instance
_customer_service = None

def get_customer_service() -> CustomerService:
    """Get or create customer service singleton."""
    global _customer_service
    if _customer_service is None:
        _customer_service = CustomerService()
    return _customer_service

"""
Supplier Service Layer.

Provides business logic and CRUD operations for Supplier management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Supplier


class SupplierService(BaseService):
    """
    Supplier service for managing supplier records.
    
    Handles:
    - Supplier CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize supplier service."""
        super().__init__(Supplier)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Supplier] = None
    ) -> List[ValidationError]:
        """
        Validate supplier data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing supplier instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['name', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'name': 255, 'email': 255, 'phone': 50, 'contact_person': 255, 'address': 500}
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors


# Singleton instance
_supplier_service = None

def get_supplier_service() -> SupplierService:
    """Get or create supplier service singleton."""
    global _supplier_service
    if _supplier_service is None:
        _supplier_service = SupplierService()
    return _supplier_service

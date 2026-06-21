"""
Product Service Layer.

Provides business logic and CRUD operations for Product management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Product, StockMovement


class InventoryValuationService(BaseService):
    """
    Product service for managing inventory_valuation records.
    
    Handles:
    - Product CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize inventory_valuation service."""
        super().__init__(Product)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Product] = None
    ) -> List[ValidationError]:
        """
        Validate inventory_valuation data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing inventory_valuation instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = []
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        return errors


# Singleton instance
_inventory_valuation_service = None

def get_inventory_valuation_service() -> InventoryValuationService:
    """Get or create inventory_valuation service singleton."""
    global _inventory_valuation_service
    if _inventory_valuation_service is None:
        _inventory_valuation_service = InventoryValuationService()
    return _inventory_valuation_service

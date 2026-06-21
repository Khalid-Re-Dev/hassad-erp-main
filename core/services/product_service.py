"""
Product Service Layer.

Provides business logic and CRUD operations for Product management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Product, Category, Unit


class ProductService(BaseService):
    """
    Product service for managing product records.
    
    Handles:
    - Product CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize product service."""
        super().__init__(Product)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Product] = None
    ) -> List[ValidationError]:
        """
        Validate product data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing product instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['sku', 'name_en', 'company_id', 'base_unit_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'sku': 100, 'barcode': 100, 'name_en': 255, 'name_ar': 255, 'description': 500}
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors


# Singleton instance
_product_service = None

def get_product_service() -> ProductService:
    """Get or create product service singleton."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service

"""
Category Service Layer.

Provides business logic and CRUD operations for Category management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Category, Product


class CategoryService(BaseService):
    """
    Category service for managing category records.
    
    Handles:
    - Category CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize category service."""
        super().__init__(Category)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Category] = None
    ) -> List[ValidationError]:
        """
        Validate category data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing category instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['name_en', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'name_en': 255, 'name_ar': 255, 'description': 500}
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors

    def _can_delete(
        self, 
        session: Session, 
        instance: Category
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if category can be deleted.
        
        Args:
            session: Database session
            instance: Category instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        errors = []
        
        # Check for products
        product_count = session.query(Product).filter(Product.category_id == instance.id).count()
        if product_count > 0:
            errors.append(ValidationError(
                '_general', 'cannot_delete',
                message=f'Category has {product_count} product(s). Reassign or delete products first.'
            ))
            return False, errors
        
        return True, []


# Singleton instance
_category_service = None

def get_category_service() -> CategoryService:
    """Get or create category service singleton."""
    global _category_service
    if _category_service is None:
        _category_service = CategoryService()
    return _category_service

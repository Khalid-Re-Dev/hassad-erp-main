"""
Sale Service Layer.

Provides business logic and CRUD operations for Sale management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Sale, SaleLine, Customer


class SaleService(BaseService):
    """
    Sale service for managing sale records.
    
    Handles:
    - Sale CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize sale service."""
        super().__init__(Sale)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Sale] = None
    ) -> List[ValidationError]:
        """
        Validate sale data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing sale instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['invoice_no', 'company_id', 'branch_id', 'cashier_user_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'invoice_no': 50, 'customer_name': 200}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        # Validate amounts are non-negative
        for field in ['subtotal', 'discount_total', 'tax_total', 'grand_total']:
            if field in data and data[field] is not None:
                try:
                    if float(data[field]) < 0:
                        errors.append(ValidationError(
                            field, 'invalid_data',
                            message=f'{field} must be non-negative'
                        ))
                except (ValueError, TypeError):
                    pass
        
        return errors


# Singleton instance
_sale_service = None

def get_sale_service() -> SaleService:
    """Get or create sale service singleton."""
    global _sale_service
    if _sale_service is None:
        _sale_service = SaleService()
    return _sale_service

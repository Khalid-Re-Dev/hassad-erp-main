"""
Sale Service Layer.

Provides business logic and CRUD operations for Sale management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Sale, SaleLine, Product, Payment


class POSService(BaseService):
    """
    Sale service for managing pos records.
    
    Handles:
    - Sale CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize pos service."""
        super().__init__(Sale)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Sale] = None
    ) -> List[ValidationError]:
        """
        Validate pos data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing pos instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['invoice_no', 'company_id', 'branch_id', 'cashier_user_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'invoice_no': 50}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        # Validate grand_total >= 0
        if 'grand_total' in data and data['grand_total'] is not None:
            try:
                if float(data['grand_total']) < 0:
                    errors.append(ValidationError(
                        'grand_total', 'invalid_data',
                        message='Grand total must be non-negative'
                    ))
            except (ValueError, TypeError):
                pass
        
        return errors


# Singleton instance
_pos_service = None

def get_pos_service() -> POSService:
    """Get or create pos service singleton."""
    global _pos_service
    if _pos_service is None:
        _pos_service = POSService()
    return _pos_service

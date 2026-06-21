"""
Account Service Layer.

Provides business logic and CRUD operations for Account management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Account


class AccountService(BaseService):
    """
    Account service for managing account records.
    
    Handles:
    - Account CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize account service."""
        super().__init__(Account)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Account] = None
    ) -> List[ValidationError]:
        """
        Validate account data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing account instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['code', 'name', 'account_type', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'code': 50, 'name': 255, 'description': 500}
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors


# Singleton instance
_account_service = None

def get_account_service() -> AccountService:
    """Get or create account service singleton."""
    global _account_service
    if _account_service is None:
        _account_service = AccountService()
    return _account_service

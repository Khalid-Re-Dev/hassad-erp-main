"""
Account Service Layer.

Provides business logic and CRUD operations for Account management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Account, JournalLine


class TrialBalanceService(BaseService):
    """
    Account service for managing trial_balance records.
    
    Handles:
    - Account CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize trial_balance service."""
        super().__init__(Account)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Account] = None
    ) -> List[ValidationError]:
        """
        Validate trial_balance data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing trial_balance instance (for updates)
            
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
_trial_balance_service = None

def get_trial_balance_service() -> TrialBalanceService:
    """Get or create trial_balance service singleton."""
    global _trial_balance_service
    if _trial_balance_service is None:
        _trial_balance_service = TrialBalanceService()
    return _trial_balance_service

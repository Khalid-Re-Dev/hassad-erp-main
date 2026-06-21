"""
JournalEntry Service Layer.

Provides business logic and CRUD operations for JournalEntry management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import JournalEntry, JournalLine, Account


class JournalService(BaseService):
    """
    JournalEntry service for managing journal records.
    
    Handles:
    - JournalEntry CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize journal service."""
        super().__init__(JournalEntry)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[JournalEntry] = None
    ) -> List[ValidationError]:
        """
        Validate journal data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing journal instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['entry_number', 'reference', 'entry_date', 'company_id', 'branch_id', 'created_by']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'entry_number': 50, 'reference': 255, 'entry_date': 10}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        # Validate entry_date format (YYYY-MM-DD)
        if 'entry_date' in data and data['entry_date']:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(data['entry_date'])):
                errors.append(ValidationError(
                    'entry_date', 'invalid_data',
                    message='Entry date must be in YYYY-MM-DD format'
                ))
        
        return errors


# Singleton instance
_journal_service = None

def get_journal_service() -> JournalService:
    """Get or create journal service singleton."""
    global _journal_service
    if _journal_service is None:
        _journal_service = JournalService()
    return _journal_service

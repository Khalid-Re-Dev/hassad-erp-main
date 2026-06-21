"""
Settings Service Layer.

Provides business logic and CRUD operations for Settings management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Settings


class SettingsService(BaseService):
    """
    Settings service for managing settings records.
    
    Handles:
    - Settings CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize settings service."""
        super().__init__(Settings)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Settings] = None
    ) -> List[ValidationError]:
        """
        Validate settings data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing settings instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['category', 'key']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'category': 50, 'key': 100, 'value': 2000, 'data_type': 20}
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
_settings_service = None

def get_settings_service() -> SettingsService:
    """Get or create settings service singleton."""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service

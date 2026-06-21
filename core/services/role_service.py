"""
Role Service Layer.

Provides business logic and CRUD operations for Role management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Role, Permission, User


class RoleService(BaseService):
    """
    Role service for managing role records.
    
    Handles:
    - Role CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize role service."""
        super().__init__(Role)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Role] = None
    ) -> List[ValidationError]:
        """
        Validate role data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing role instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['name', 'code']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'name': 100, 'code': 50, 'description': 500}
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
        instance: Role
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if role can be deleted.
        
        Args:
            session: Database session
            instance: Role instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        errors = []
        
        # Check for assigned users
        user_count = session.query(User).join(User.roles).filter(Role.id == instance.id).count()
        if user_count > 0:
            errors.append(ValidationError(
                '_general', 'cannot_delete',
                message=f'Role has {user_count} assigned user(s). Remove users first.'
            ))
            return False, errors
        
        return True, []


# Singleton instance
_role_service = None

def get_role_service() -> RoleService:
    """Get or create role service singleton."""
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service

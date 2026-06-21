"""
Branch Service Layer.

Provides business logic and CRUD operations for Branch management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Branch, Company, User


class BranchService(BaseService):
    """
    Branch service for managing branch records.
    
    Handles:
    - Branch creation and updates
    - Location information validation
    - Unique code enforcement
    - Dependency checking (users, sales, etc.)
    """
    
    def __init__(self):
        """Initialize branch service."""
        super().__init__(Branch)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Branch] = None
    ) -> List[ValidationError]:
        """
        Validate branch data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing branch instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create, not update)
        if not is_update:
            required_fields = ['name', 'code', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {
            'name': 255,
            'code': 50,
            'email': 255,
            'phone': 50,
            'city': 100,
            'state': 100,
            'country': 100,
            'postal_code': 20,
            'manager_name': 255
        }
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        # Code format validation (alphanumeric, dashes, underscores)
        if 'code' in data and data['code']:
            import re
            code = str(data['code']).strip()
            if not re.match(r'^[A-Za-z0-9_-]+$', code):
                errors.append(ValidationError(
                    'code',
                    'invalid_data',
                    message='Branch code must contain only letters, numbers, dashes, and underscores'
                ))
        
        return errors
    
    def _can_delete(
        self, 
        session: Session, 
        instance: Branch
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if branch can be deleted.
        
        Branches with active users cannot be deleted.
        
        Args:
            session: Database session
            instance: Branch instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        errors = []
        
        # Check for active users
        user_count = session.query(User).filter(
            User.branch_id == instance.id,
            User.is_active == True
        ).count()
        
        if user_count > 0:
            errors.append(ValidationError(
                '_general',
                'cannot_delete',
                message=f'Branch has {user_count} active user(s). Reassign or deactivate users first.'
            ))
            return False, errors
        
        # Check if this is the main branch
        if instance.is_main:
            errors.append(ValidationError(
                '_general',
                'cannot_delete',
                message='Cannot delete the main branch. Set another branch as main first.'
            ))
            return False, errors
        
        return True, []
    
    def get_by_code(self, session: Session, code: str) -> Optional[Branch]:
        """
        Get branch by code.
        
        Args:
            session: Database session
            code: Branch code
            
        Returns:
            Branch instance or None
        """
        try:
            return session.query(Branch).filter_by(code=code).first()
        except Exception as e:
            self.logger.error(f"Error fetching branch by code {code}: {e}")
            return None
    
    def get_by_company(
        self, 
        session: Session, 
        company_id: int,
        active_only: bool = False
    ) -> List[Branch]:
        """
        Get all branches for a company.
        
        Args:
            session: Database session
            company_id: Company ID
            active_only: If True, return only active branches
            
        Returns:
            List of branches
        """
        filters = {'company_id': company_id}
        if active_only:
            filters['is_active'] = True
        
        return self.get_all(session, filters=filters, order_by='name')
    
    def get_main_branch(self, session: Session, company_id: int) -> Optional[Branch]:
        """
        Get the main branch for a company.
        
        Args:
            session: Database session
            company_id: Company ID
            
        Returns:
            Main branch instance or None
        """
        try:
            return session.query(Branch).filter_by(
                company_id=company_id,
                is_main=True
            ).first()
        except Exception as e:
            self.logger.error(f"Error fetching main branch for company {company_id}: {e}")
            return None
    
    def set_main_branch(
        self, 
        session: Session, 
        branch_id: int
    ) -> Tuple[Optional[Branch], List[ValidationError]]:
        """
        Set a branch as the main branch (unsets others in same company).
        
        Args:
            session: Database session
            branch_id: Branch ID to set as main
            
        Returns:
            Tuple of (branch_instance, validation_errors)
        """
        branch = self.get_by_id(session, branch_id)
        if not branch:
            return None, [ValidationError('id', 'not_found')]
        
        # Unset other main branches in the same company
        session.query(Branch).filter(
            Branch.company_id == branch.company_id,
            Branch.id != branch_id,
            Branch.is_main == True
        ).update({'is_main': False})
        
        # Set this branch as main
        branch.is_main = True
        session.flush()
        
        self.logger.info(f"Set branch ID {branch_id} as main branch")
        return branch, []
    
    def activate(
        self, 
        session: Session, 
        branch_id: int
    ) -> Tuple[Optional[Branch], List[ValidationError]]:
        """
        Activate a branch.
        
        Args:
            session: Database session
            branch_id: Branch ID
            
        Returns:
            Tuple of (branch_instance, validation_errors)
        """
        branch = self.get_by_id(session, branch_id)
        if not branch:
            return None, [ValidationError('id', 'not_found')]
        
        branch.is_active = True
        session.flush()
        
        self.logger.info(f"Activated branch ID {branch_id}")
        return branch, []
    
    def deactivate(
        self, 
        session: Session, 
        branch_id: int
    ) -> Tuple[Optional[Branch], List[ValidationError]]:
        """
        Deactivate a branch.
        
        Args:
            session: Database session
            branch_id: Branch ID
            
        Returns:
            Tuple of (branch_instance, validation_errors)
        """
        branch = self.get_by_id(session, branch_id)
        if not branch:
            return None, [ValidationError('id', 'not_found')]
        
        # Check if can deactivate (has active users)
        can_deactivate, errors = self._can_delete(session, branch)
        if not can_deactivate:
            return None, errors
        
        # Cannot deactivate main branch
        if branch.is_main:
            return None, [ValidationError(
                '_general',
                'cannot_delete',
                message='Cannot deactivate the main branch. Set another branch as main first.'
            )]
        
        branch.is_active = False
        session.flush()
        
        self.logger.info(f"Deactivated branch ID {branch_id}")
        return branch, []


# Singleton instance
_branch_service = None

def get_branch_service() -> BranchService:
    """Get or create branch service singleton."""
    global _branch_service
    if _branch_service is None:
        _branch_service = BranchService()
    return _branch_service

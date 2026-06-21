"""
User Service Layer.

Provides business logic and CRUD operations for User management with authentication.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import re

from core.services.base_service import BaseService, ValidationError
from models import User, Role, Branch


class UserService(BaseService):
    """
    User service for managing user accounts.
    
    Handles:
    - User CRUD with password management
    - Authentication validation
    - Role assignment
    - Branch assignment
    - Access control
    """
    
    def __init__(self):
        """Initialize user service."""
        super().__init__(User)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[User] = None
    ) -> List[ValidationError]:
        """
        Validate user data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing user instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create, not update)
        if not is_update:
            required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'company_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {
            'username': 100,
            'email': 255,
            'first_name': 100,
            'last_name': 100,
            'phone': 50
        }
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        # Username validation (alphanumeric + underscore/dash)
        if 'username' in data and data['username']:
            username = str(data['username']).strip()
            if not re.match(r'^[A-Za-z0-9_-]+$', username):
                errors.append(ValidationError(
                    'username',
                    'invalid_data',
                    message='Username must contain only letters, numbers, dashes, and underscores'
                ))
            if len(username) < 3:
                errors.append(ValidationError(
                    'username',
                    'invalid_data',
                    message='Username must be at least 3 characters long'
                ))
        
        # Password validation (only on create or if password provided)
        if ('password' in data and data['password']) or (not is_update and 'password' in data):
            password = str(data.get('password', ''))
            if len(password) < 8:
                errors.append(ValidationError(
                    'password',
                    'invalid_data',
                    message='Password must be at least 8 characters long'
                ))
        
        return errors
    
    def create(
        self, 
        session: Session, 
        data: Dict[str, Any]
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Create new user with password hashing.
        
        Args:
            session: Database session
            data: Dictionary of field values (must include 'password')
            
        Returns:
            Tuple of (created_instance, validation_errors)
        """
        try:
            # Validate input
            errors = self.validate(data, is_update=False)
            if errors:
                return None, errors
            
            # Extract password before creating instance
            password = data.pop('password', None)
            if not password:
                return None, [ValidationError('password', 'required')]
            
            # Prepare data and create instance
            prepared_data = self._prepare_data(data)
            user = self.model_class(**prepared_data)
            
            # Set password (uses bcrypt hashing)
            user.set_password(password)
            
            # Add to session
            session.add(user)
            session.flush()
            
            self.logger.info(f"Created user with ID {user.id}, username: {user.username}")
            return user, []
            
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            error = ValidationError('_general', 'database_error')
            return None, [error]
    
    def update(
        self, 
        session: Session, 
        record_id: int, 
        data: Dict[str, Any]
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Update existing user (handles password separately).
        
        Args:
            session: Database session
            record_id: User ID to update
            data: Dictionary of field values (password optional)
            
        Returns:
            Tuple of (updated_instance, validation_errors)
        """
        try:
            # Get existing user
            user = self.get_by_id(session, record_id)
            if not user:
                error = ValidationError('id', 'not_found')
                return None, [error]
            
            # Extract password if provided
            password = data.pop('password', None)
            
            # Validate input
            errors = self.validate(data, is_update=True, instance=user)
            if errors:
                return None, errors
            
            # Update fields
            prepared_data = self._prepare_data(data)
            for field, value in prepared_data.items():
                if hasattr(user, field) and field != 'password_hash':
                    setattr(user, field, value)
            
            # Update password if provided
            if password:
                user.set_password(password)
            
            session.flush()
            
            self.logger.info(f"Updated user ID {record_id}")
            return user, []
            
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            error = ValidationError('_general', 'database_error')
            return None, [error]
    
    def authenticate(
        self,
        session: Session,
        username: str,
        password: str
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Authenticate user by username and password.
        
        Args:
            session: Database session
            username: Username
            password: Plain text password
            
        Returns:
            Tuple of (user_instance, validation_errors)
        """
        try:
            # Find user by username
            user = session.query(User).filter_by(username=username).first()
            
            if not user:
                error = ValidationError('username', 'invalid_data', 
                                      message='Invalid username or password')
                return None, [error]
            
            # Check if user is active
            if not user.is_active:
                error = ValidationError('username', 'invalid_data',
                                      message='User account is inactive')
                return None, [error]
            
            # Verify password
            if not user.check_password(password):
                error = ValidationError('password', 'invalid_data',
                                      message='Invalid username or password')
                return None, [error]
            
            self.logger.info(f"User authenticated: {username}")
            return user, []
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            error = ValidationError('_general', 'database_error')
            return None, [error]
    
    def get_by_username(self, session: Session, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            session: Database session
            username: Username
            
        Returns:
            User instance or None
        """
        try:
            return session.query(User).filter_by(username=username).first()
        except Exception as e:
            self.logger.error(f"Error fetching user by username {username}: {e}")
            return None
    
    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            session: Database session
            email: Email address
            
        Returns:
            User instance or None
        """
        try:
            return session.query(User).filter_by(email=email).first()
        except Exception as e:
            self.logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    def get_by_branch(
        self,
        session: Session,
        branch_id: int,
        active_only: bool = True
    ) -> List[User]:
        """
        Get all users in a branch.
        
        Args:
            session: Database session
            branch_id: Branch ID
            active_only: If True, return only active users
            
        Returns:
            List of users
        """
        filters = {'branch_id': branch_id}
        if active_only:
            filters['is_active'] = True
        
        return self.get_all(session, filters=filters, order_by='username')
    
    def assign_role(
        self,
        session: Session,
        user_id: int,
        role_id: int
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Assign a role to a user.
        
        Args:
            session: Database session
            user_id: User ID
            role_id: Role ID
            
        Returns:
            Tuple of (user_instance, validation_errors)
        """
        try:
            user = self.get_by_id(session, user_id)
            if not user:
                return None, [ValidationError('user_id', 'not_found')]
            
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                return None, [ValidationError('role_id', 'not_found')]
            
            if role not in user.roles:
                user.roles.append(role)
                session.flush()
                self.logger.info(f"Assigned role {role_id} to user {user_id}")
            
            return user, []
            
        except Exception as e:
            self.logger.error(f"Error assigning role: {e}")
            return None, [ValidationError('_general', 'database_error')]
    
    def remove_role(
        self,
        session: Session,
        user_id: int,
        role_id: int
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Remove a role from a user.
        
        Args:
            session: Database session
            user_id: User ID
            role_id: Role ID
            
        Returns:
            Tuple of (user_instance, validation_errors)
        """
        try:
            user = self.get_by_id(session, user_id)
            if not user:
                return None, [ValidationError('user_id', 'not_found')]
            
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                return None, [ValidationError('role_id', 'not_found')]
            
            if role in user.roles:
                user.roles.remove(role)
                session.flush()
                self.logger.info(f"Removed role {role_id} from user {user_id}")
            
            return user, []
            
        except Exception as e:
            self.logger.error(f"Error removing role: {e}")
            return None, [ValidationError('_general', 'database_error')]
    
    def activate(
        self,
        session: Session,
        user_id: int
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Activate a user account.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Tuple of (user_instance, validation_errors)
        """
        user = self.get_by_id(session, user_id)
        if not user:
            return None, [ValidationError('id', 'not_found')]
        
        user.is_active = True
        session.flush()
        
        self.logger.info(f"Activated user ID {user_id}")
        return user, []
    
    def deactivate(
        self,
        session: Session,
        user_id: int
    ) -> Tuple[Optional[User], List[ValidationError]]:
        """
        Deactivate a user account.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Tuple of (user_instance, validation_errors)
        """
        user = self.get_by_id(session, user_id)
        if not user:
            return None, [ValidationError('id', 'not_found')]
        
        user.is_active = False
        session.flush()
        
        self.logger.info(f"Deactivated user ID {user_id}")
        return user, []


# Singleton instance
_user_service = None

def get_user_service() -> UserService:
    """Get or create user service singleton."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service

"""
Centralized Permission Management System.

Provides role-based access control with wildcard admin support
and graceful fallback for missing database configuration.
"""

import logging
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models import User, Role, Permission

# Configure logging
logger = logging.getLogger(__name__)

# Permission configuration error
class PermissionConfigError(Exception):
    """Raised when permission configuration is invalid or missing."""
    pass


class PermissionManager:
    """
    Centralized permission management system.
    
    Features:
    - Role-based permission checking
    - Wildcard admin access (admin.full_access)
    - Database-backed permissions with in-memory fallback
    - Efficient caching for performance
    - Arabic/English error messages
    """
    
    def __init__(self):
        self._permission_cache: Dict[str, Set[str]] = {}
        self._role_cache: Dict[str, str] = {}
        self._cache_valid = False
        
        # Fallback permissions mapping (when DB is not available)
        self._fallback_permissions = {
            'admin': {
                'admin.full_access',
                'users.view', 'users.create', 'users.edit', 'users.delete',
                'roles.view', 'roles.create', 'roles.edit', 'roles.delete',
                'company.view', 'company.edit',
                'branches.view', 'branches.create', 'branches.edit', 'branches.delete',
                'accounting.view', 'accounting.create', 'accounting.edit',
                'inventory.view', 'inventory.create', 'inventory.edit',
                'sales.view', 'sales.create', 'sales.edit',
                'purchases.view', 'purchases.create', 'purchases.edit',
                'reports.view', 'reports.generate',
                'settings.view', 'settings.edit'
            },
            'accountant': {
                'accounting.view', 'accounting.create', 'accounting.edit',
                'reports.view', 'reports.generate'
            },
            'cashier': {
                'sales.view', 'sales.create',
                'inventory.view'
            },
            'inventory_manager': {
                'inventory.view', 'inventory.create', 'inventory.edit',
                'products.view', 'products.create', 'products.edit',
                'categories.view', 'categories.create', 'categories.edit'
            },
            'purchase_manager': {
                'purchases.view', 'purchases.create', 'purchases.edit',
                'suppliers.view', 'suppliers.create', 'suppliers.edit'
            },
            'sales_manager': {
                'sales.view', 'sales.create', 'sales.edit',
                'customers.view', 'customers.create', 'customers.edit'
            }
        }
    
    def has_permission(self, user: User, permission_code: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user: User object with roles
            permission_code: Permission code (e.g., 'accounting.view')
            
        Returns:
            bool: True if user has permission
        """
        try:
            # Check if user is superuser
            if user.is_superuser:
                logger.debug(f"Superuser {user.username} granted access to {permission_code}")
                return True
            
            # Check for admin wildcard
            if self.is_admin(user):
                logger.debug(f"Admin {user.username} granted wildcard access to {permission_code}")
                return True
            
            # Get user's permissions
            user_permissions = self._get_user_permissions(user)
            
            # Check direct permission
            if permission_code in user_permissions:
                logger.debug(f"User {user.username} has direct permission {permission_code}")
                return True
            
            # Check module-level access (e.g., 'accounting.*' grants 'accounting.view')
            module = permission_code.split('.')[0]
            module_wildcard = f"{module}.*"
            if module_wildcard in user_permissions:
                logger.debug(f"User {user.username} has module access {module_wildcard} for {permission_code}")
                return True
            
            logger.debug(f"User {user.username} denied access to {permission_code}")
            return False
            
        except Exception as e:
            logger.error(f"Permission check failed for user {user.username}, permission {permission_code}: {e}")
            # Fail securely - deny access on errors
            return False
    
    def is_admin(self, user: User) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            user: User object
            
        Returns:
            bool: True if user is admin
        """
        try:
            if user.is_superuser:
                return True
            
            role_codes = [role.code.lower() for role in user.roles]
            return 'admin' in role_codes or 'administrator' in role_codes
            
        except Exception as e:
            logger.error(f"Admin check failed for user {user.username}: {e}")
            return False
    
    def permissions_for_role(self, role_code: str) -> Set[str]:
        """
        Get all permissions for a specific role.
        
        Args:
            role_code: Role code (e.g., 'admin', 'accountant')
            
        Returns:
            Set[str]: Set of permission codes
        """
        try:
            role_code = role_code.lower()
            
            # Try database first
            permissions = self._get_role_permissions_from_db(role_code)
            if permissions:
                return permissions
            
            # Fallback to in-memory mapping
            return self._fallback_permissions.get(role_code, set())
            
        except Exception as e:
            logger.error(f"Failed to get permissions for role {role_code}: {e}")
            return set()
    
    def get_user_modules(self, user: User) -> List[str]:
        """
        Get list of modules user has access to.
        
        Args:
            user: User object
            
        Returns:
            List[str]: List of module names user can access
        """
        try:
            user_permissions = self._get_user_permissions(user)
            modules = set()
            
            for permission in user_permissions:
                if '.' in permission:
                    module = permission.split('.')[0]
                    modules.add(module)
            
            return sorted(list(modules))
            
        except Exception as e:
            logger.error(f"Failed to get modules for user {user.username}: {e}")
            return []
    
    def _get_user_permissions(self, user: User) -> Set[str]:
        """Get all permissions for a user from their roles."""
        try:
            permissions = set()
            
            for role in user.roles:
                role_permissions = self.permissions_for_role(role.code)
                permissions.update(role_permissions)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions for {user.username}: {e}")
            return set()
    
    def _get_role_permissions_from_db(self, role_code: str) -> Optional[Set[str]]:
        """
        Get role permissions from database.
        
        Args:
            role_code: Role code
            
        Returns:
            Optional[Set[str]]: Set of permission codes or None if DB unavailable
        """
        try:
            from core.database import SessionLocal
            
            with SessionLocal() as session:
                role = session.query(Role).filter(
                    Role.code == role_code,
                    Role.is_active == True
                ).first()
                
                if not role:
                    return None
                
                permissions = set()
                for permission in role.permissions:
                    permissions.add(permission.code)
                
                return permissions
                
        except SQLAlchemyError as e:
            logger.warning(f"Database unavailable for role permissions: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting role permissions from DB: {e}")
            return None
    
    def clear_cache(self):
        """Clear permission cache (call when roles/permissions are modified)."""
        self._permission_cache.clear()
        self._role_cache.clear()
        self._cache_valid = False
        logger.info("Permission cache cleared")
    
    def validate_permission_code(self, permission_code: str) -> bool:
        """
        Validate permission code format.
        
        Args:
            permission_code: Permission code to validate
            
        Returns:
            bool: True if valid format
        """
        if not permission_code or not isinstance(permission_code, str):
            return False
        
        # Must be in format 'module.action' or 'module.*'
        parts = permission_code.split('.')
        if len(parts) != 2:
            return False
        
        module, action = parts
        if not module or not action:
            return False
        
        # Valid actions
        valid_actions = {'view', 'create', 'edit', 'delete', 'generate', '*', 'full_access'}
        if action not in valid_actions:
            return False
        
        return True


# Global permission manager instance
permission_manager = PermissionManager()


def check_permission(user: User, permission_code: str) -> bool:
    """
    Convenience function for permission checking.
    
    Args:
        user: User object
        permission_code: Permission code
        
    Returns:
        bool: True if user has permission
    """
    return permission_manager.has_permission(user, permission_code)


def require_permission(permission_code: str):
    """
    Decorator to require permission for a function.
    
    Args:
        permission_code: Required permission code
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would need to be implemented based on how user context is passed
            # For now, just a placeholder
            raise NotImplementedError("Permission decorator not yet implemented")
        return wrapper
    return decorator
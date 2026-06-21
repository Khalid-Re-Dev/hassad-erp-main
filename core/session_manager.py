"""
Session manager for maintaining active user session state.

This module provides in-memory session management for the desktop application.
"""

from datetime import datetime
from typing import Optional

from models import Branch, User


class SessionManager:
    """
    Singleton session manager for maintaining active user session.

    Attributes:
        _instance: Singleton instance
        _user: Currently logged-in user
        _branch: Active branch
        _session_token: Session token
        _login_time: Login timestamp
    """

    _instance: Optional["SessionManager"] = None
    _user: Optional[User] = None
    _branch: Optional[Branch] = None
    _session_token: Optional[str] = None
    _login_time: Optional[datetime] = None

    def __new__(cls) -> "SessionManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def login(
        self,
        user: User,
        session_token: Optional[str] = None,
    ) -> None:
        """
        Set active user session.

        Args:
            user: Authenticated user object
            session_token: Session token (optional)
        """
        self._user = user
        self._branch = user.branch
        self._session_token = session_token
        self._login_time = datetime.utcnow()

    def logout(self) -> None:
        """Clear active session."""
        self._user = None
        self._branch = None
        self._session_token = None
        self._login_time = None

    def get_active_user(self) -> Optional[User]:
        """
        Get currently logged-in user.

        Returns:
            User: Active user or None if not logged in
        """
        return self._user

    def get_active_branch(self) -> Optional[Branch]:
        """
        Get active branch.

        Returns:
            Branch: Active branch or None
        """
        return self._branch

    def set_active_branch(self, branch: Branch) -> None:
        """
        Set active branch for current session.

        Args:
            branch: Branch to set as active
        """
        self._branch = branch

    def get_session_token(self) -> Optional[str]:
        """
        Get session token.

        Returns:
            str: Session token or None
        """
        return self._session_token

    def get_login_time(self) -> Optional[datetime]:
        """
        Get login timestamp.

        Returns:
            datetime: Login time or None
        """
        return self._login_time

    def is_logged_in(self) -> bool:
        """
        Check if user is logged in.

        Returns:
            bool: True if user is logged in
        """
        return self._user is not None

    def has_permission(self, permission_code: str) -> bool:
        """
        Check if active user has specific permission.

        Args:
            permission_code: Permission code to check

        Returns:
            bool: True if user has permission
        """
        if not self._user:
            return False

        if self._user.is_superuser:
            return True

        for role in self._user.roles:
            for permission in role.permissions:
                if permission.code == permission_code:
                    return True

        return False

    def get_user_roles(self) -> list[str]:
        """
        Get list of role codes for active user.

        Returns:
            list: List of role codes
        """
        if not self._user:
            return []

        return [role.code for role in self._user.roles]

    def __repr__(self) -> str:
        """String representation."""
        if self._user:
            return f"<SessionManager(user='{self._user.username}', branch='{self._branch.name if self._branch else None}')>"
        return "<SessionManager(not logged in)>"


# Global session manager instance
session_manager = SessionManager()

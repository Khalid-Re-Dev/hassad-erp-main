"""
Authentication module for user login and password validation.

This module provides secure authentication using bcrypt password hashing
and integrates with the User model and audit logging.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session, selectinload

from models import AuditLog, SessionLog, User


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when credentials are invalid."""

    pass


class InactiveUserError(AuthenticationError):
    """Exception raised when user account is inactive."""

    pass


class PasswordPolicyError(AuthenticationError):
    """Exception raised when password doesn't meet policy requirements."""

    pass


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        bool: True if password meets requirements

    Raises:
        PasswordPolicyError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise PasswordPolicyError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise PasswordPolicyError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise PasswordPolicyError("Password must contain at least one special character")

    return True


def authenticate_user(
    session: Session,
    username: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> User:
    """
    Authenticate user with username and password.

    Args:
        session: Database session
        username: Username or email
        password: Plain text password
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)

    Returns:
        User: Authenticated user object

    Raises:
        InvalidCredentialsError: If credentials are invalid
        InactiveUserError: If user account is inactive
    """
    # Find user by username or email with eagerly loaded roles
    user = (
        session.query(User)
        .options(selectinload(User.roles))
        .filter(
            (User.username == username) | (User.email == username),
            User.deleted_at.is_(None),
        )
        .first()
    )

    # Check if user exists and password is correct
    if not user or not user.check_password(password):
        # Log failed login attempt
        _log_failed_login(session, username, "Invalid credentials", ip_address, user_agent)
        raise InvalidCredentialsError("Invalid username or password")

    # Check if user is active
    if not user.is_active:
        # Log failed login attempt
        _log_failed_login(session, username, "Account inactive", ip_address, user_agent)
        raise InactiveUserError("User account is inactive")

    # Log successful login
    _log_successful_login(session, user, ip_address, user_agent)

    # Create audit log entry (temporarily disabled due to schema mismatch)
    # _create_audit_log(session, user, "LOGIN", "User logged in successfully")

    return user


def logout_user(
    session: Session,
    user: User,
    session_token: Optional[str] = None,
) -> None:
    """
    Log out user and update session log.

    Args:
        session: Database session
        user: User object
        session_token: Session token to close (optional)
    """
    # Find active session log
    if session_token:
        session_log = (
            session.query(SessionLog)
            .filter(
                SessionLog.session_token == session_token,
                SessionLog.logout_time.is_(None),
            )
            .first()
        )
    else:
        # Find most recent active session
        session_log = (
            session.query(SessionLog)
            .filter(
                SessionLog.user_id == user.id,
                SessionLog.logout_time.is_(None),
            )
            .order_by(SessionLog.login_time.desc())
            .first()
        )

    if session_log:
        session_log.logout_time = datetime.utcnow()
        session.commit()

    # Create audit log entry
    _create_audit_log(session, user, "LOGOUT", "User logged out")


def _log_successful_login(
    session: Session,
    user: User,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> SessionLog:
    """Create session log entry for successful login."""
    session_token = str(uuid4())

    session_log = SessionLog(
        id=uuid4(),
        user_id=user.id,
        login_time=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        session_token=session_token,
    )

    session.add(session_log)
    session.flush()  # Ensure ID is generated but don't commit yet

    return session_log


def _log_failed_login(
    session: Session,
    username: str,
    reason: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> None:
    """Create session log entry for failed login."""
    session_log = SessionLog(
        id=uuid4(),
        user_id=None,  # No user ID for failed attempts
        login_time=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        success=False,
        failure_reason=reason,
    )

    session.add(session_log)
    session.flush()  # Ensure record is written but don't commit yet


def _create_audit_log(
    session: Session,
    user: User,
    action: str,
    notes: str,
) -> None:
    """Create audit log entry for authentication event."""
    audit_log = AuditLog(
        id=uuid4(),
        user_id=user.id,
        action=action,
        entity_type="user",
        entity_id=user.id,
        old_values=None,
        new_values={"username": user.username, "timestamp": datetime.utcnow().isoformat()},
        ip_address=None,
        user_agent=None,
        notes=notes,
    )

    session.add(audit_log)
    session.flush()  # Ensure record is written but don't commit yet


def change_password(
    session: Session,
    user: User,
    old_password: str,
    new_password: str,
) -> None:
    """
    Change user password.

    Args:
        session: Database session
        user: User object
        old_password: Current password
        new_password: New password

    Raises:
        InvalidCredentialsError: If old password is incorrect
        PasswordPolicyError: If new password doesn't meet requirements
    """
    # Verify old password
    if not user.check_password(old_password):
        raise InvalidCredentialsError("Current password is incorrect")

    # Validate new password strength
    validate_password_strength(new_password)

    # Set new password
    user.set_password(new_password)
    session.commit()

    # Create audit log entry
    _create_audit_log(session, user, "PASSWORD_CHANGE", "User changed password")

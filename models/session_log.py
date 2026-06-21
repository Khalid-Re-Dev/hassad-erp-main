"""
Session log model for tracking user login/logout activity.

This model provides audit trail for authentication events.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel


class SessionLog(BaseModel):
    """
    Session log model for tracking user authentication events.

    Attributes:
        user_id: Foreign key to user
        login_time: Timestamp of login attempt
        logout_time: Timestamp of logout (nullable)
        ip_address: IP address of client (nullable)
        user_agent: Browser/client user agent (nullable)
        success: Whether login was successful
        failure_reason: Reason for login failure (nullable)
        session_token: Unique session identifier (nullable)
    """

    __tablename__ = "session_logs"

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for failed login attempts
        index=True,
        comment="User ID",
    )

    # Session Information
    login_time = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Login timestamp (UTC)",
    )

    logout_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Logout timestamp (UTC)",
    )

    # Client Information
    ip_address = Column(String(45), nullable=True, comment="Client IP address")
    user_agent = Column(String(500), nullable=True, comment="Client user agent")

    # Status
    success = Column(Boolean, nullable=False, default=False, comment="Login success status")
    failure_reason = Column(String(255), nullable=True, comment="Failure reason")

    # Session Token
    session_token = Column(
        String(255), nullable=True, unique=True, index=True, comment="Session token"
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"<SessionLog(id={self.id}, user_id={self.user_id}, status={status})>"

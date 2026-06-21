"""
Audit log model for tracking all system changes.

Audit logs are immutable and provide a complete history of data modifications.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID

from models.base import BaseModel


class AuditLog(BaseModel):
    """
    Immutable audit log for tracking system changes.

    Attributes:
        user_id: User who performed the action
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity affected (table name)
        entity_id: ID of affected entity
        old_values: Previous values (JSON)
        new_values: New values (JSON)
        ip_address: IP address of user
        user_agent: User agent string
        notes: Additional notes
    """

    __tablename__ = "audit_logs"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed action",
    )

    action = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Action type (CREATE, UPDATE, DELETE, etc.)",
    )

    entity_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Entity type (table name)",
    )

    entity_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of affected entity",
    )

    old_values = Column(JSON, nullable=True, comment="Previous values (JSON)")
    new_values = Column(JSON, nullable=True, comment="New values (JSON)")

    ip_address = Column(String(45), nullable=True, comment="User IP address")
    user_agent = Column(Text, nullable=True, comment="User agent string")
    notes = Column(Text, nullable=True, comment="Additional notes")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"entity_type='{self.entity_type}')>"
        )

"""
Settings model for system and company configuration.

Stores key-value configuration pairs with scope (system or company-level).
"""

from sqlalchemy import Column, ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from models.base import Base
from sqlalchemy.orm import relationship


class Settings(Base):
    """
    Settings model for flexible configuration storage.

    Attributes:
        company_id: Company ID (NULL for system-wide settings)
        key: Setting key
        value: Setting value (stored as text, parse as needed)
        value_type: Data type hint (string, integer, boolean, json, etc.)
        description: Setting description
    """

    __tablename__ = "settings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="Unique identifier (UUID)",
    )

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Company ID (NULL for system-wide)",
    )

    key = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Setting key",
    )

    value = Column(Text, nullable=True, comment="Setting value (text)")

    value_type = Column(
        String(20),
        nullable=True,
        comment="Data type (string, integer, boolean, json)",
    )

    description = Column(Text, nullable=True, comment="Setting description")

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Creation timestamp (UTC)",
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp (UTC)",
    )

    # Relationships
    company = relationship("Company", back_populates="settings")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Settings(id={self.id}, key='{self.key}')>"

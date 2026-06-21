"""
Permission model for granular access control.

Permissions define specific actions users can perform in the system.
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Permission(BaseModel):
    """
    Permission model for granular access control.

    Attributes:
        name: Permission name
        code: Permission code (e.g., 'sales.create', 'inventory.view')
        module: Module/feature this permission belongs to
        description: Permission description
    """

    __tablename__ = "permissions"

    name = Column(
        String(100), nullable=False, unique=True, index=True, comment="Permission name"
    )
    code = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Permission code (e.g., 'sales.create')",
    )
    module = Column(
        String(50), nullable=False, index=True, comment="Module/feature name"
    )
    description = Column(Text, nullable=True, comment="Permission description")

    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Permission(id={self.id}, code='{self.code}')>"

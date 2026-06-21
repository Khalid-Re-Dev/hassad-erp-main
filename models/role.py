"""
Role model for role-based access control (RBAC).

Roles group permissions and are assigned to users.
"""

from sqlalchemy import Boolean, Column, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from models.base import Base, BaseModel

# Many-to-many association table for roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(BaseModel):
    """
    Role model for grouping permissions.

    Attributes:
        name: Role name (unique)
        code: Role code for programmatic access
        description: Role description
        is_active: Whether role is active
        is_system: Whether role is system-defined (cannot be deleted)
    """

    __tablename__ = "roles"

    name = Column(
        String(100), nullable=False, unique=True, index=True, comment="Role name"
    )
    code = Column(
        String(50), nullable=False, unique=True, index=True, comment="Role code"
    )
    description = Column(Text, nullable=True, comment="Role description")
    is_active = Column(Boolean, default=True, nullable=False, comment="Active status")
    is_system = Column(
        Boolean, default=False, nullable=False, comment="System-defined role"
    )

    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="select",
    )

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}')>"

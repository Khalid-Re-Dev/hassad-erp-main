"""
User model for authentication and authorization.

Users are associated with a company and branch, with role-based access control.
"""

import bcrypt
from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base, BaseModel

# Many-to-many association table for users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(BaseModel):
    """
    User model for system authentication and authorization.

    Attributes:
        company_id: Foreign key to company
        branch_id: Foreign key to default branch
        username: Unique username for login
        email: User email address
        password_hash: Bcrypt hashed password
        first_name: User first name
        last_name: User last name
        phone: Contact phone number
        is_active: Whether user account is active
        is_superuser: Whether user has superuser privileges
        last_login: Last login timestamp
    """

    __tablename__ = "users"

    # Foreign Keys
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Company ID",
    )

    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Default branch ID",
    )

    # Authentication
    username = Column(
        String(100), nullable=False, unique=True, index=True, comment="Unique username"
    )
    email = Column(String(255), nullable=False, unique=True, index=True, comment="Email address")
    password_hash = Column(String(255), nullable=False, comment="Bcrypt password hash")

    # Personal Information
    first_name = Column(String(100), nullable=False, comment="First name")
    last_name = Column(String(100), nullable=False, comment="Last name")
    phone = Column(String(50), nullable=True, comment="Phone number")

    # Status
    is_active = Column(Boolean, default=True, nullable=False, comment="Active status")
    is_superuser = Column(
        Boolean, default=False, nullable=False, comment="Superuser privileges"
    )

    # Relationships
    branch = relationship("Branch", back_populates="users")

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="select",
    )

    sales_as_cashier = relationship(
        "Sale",
        foreign_keys="Sale.cashier_user_id",
        back_populates="cashier",
        lazy="select",
    )

    sales_posted = relationship(
        "Sale",
        foreign_keys="Sale.posted_by_user_id",
        back_populates="posted_by",
        lazy="select",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str) -> None:
        """
        Hash and set user password.

        Args:
            password: Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username='{self.username}')>"

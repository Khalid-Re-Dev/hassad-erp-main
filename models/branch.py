"""
Branch model for multi-location support.

Each branch represents a physical location or department within a company.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Branch(BaseModel):
    """
    Branch model representing a company location or department.

    Attributes:
        company_id: Foreign key to parent company
        name: Branch name
        code: Unique branch code
        email: Branch contact email
        phone: Branch contact phone
        address: Physical address
        city: City
        state: State/province
        country: Country
        postal_code: Postal/ZIP code
        is_active: Whether branch is active
        is_main: Whether this is the main/headquarters branch
        manager_name: Branch manager name
        notes: Additional notes
    """

    __tablename__ = "branches"

    # Foreign Keys
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent company ID",
    )

    # Basic Information
    name = Column(String(255), nullable=False, comment="Branch name")
    code = Column(String(50), nullable=False, unique=True, comment="Unique branch code")

    # Contact Information
    email = Column(String(255), nullable=True, comment="Branch email")
    phone = Column(String(50), nullable=True, comment="Branch phone")
    address = Column(Text, nullable=True, comment="Physical address")
    city = Column(String(100), nullable=True, comment="City")
    state = Column(String(100), nullable=True, comment="State/Province")
    country = Column(String(100), nullable=False, default="US", comment="Country code")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")

    # Status
    is_active = Column(Boolean, default=True, nullable=False, comment="Active status")
    is_main = Column(
        Boolean, default=False, nullable=False, comment="Is main/headquarters branch"
    )

    # Management
    manager_name = Column(String(255), nullable=True, comment="Branch manager name")
    notes = Column(Text, nullable=True, comment="Additional notes")

    # Relationships
    company = relationship("Company", back_populates="branches")

    users = relationship(
        "User",
        back_populates="branch",
        lazy="select",
    )

    sales = relationship(
        "Sale",
        back_populates="branch",
        lazy="select",
    )

    pos_settings = relationship(
        "POSSettings",
        back_populates="branch",
        uselist=False,
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Branch(id={self.id}, name='{self.name}', code='{self.code}')>"

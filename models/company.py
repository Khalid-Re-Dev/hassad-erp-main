"""
Company model for multi-company support.

Each company represents a separate legal entity with its own
financial records, branches, and users.
"""

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Company(BaseModel):
    """
    Company model representing a legal business entity.

    Attributes:
        name: Company legal name
        trade_name: Trading/commercial name
        tax_id: Tax identification number
        registration_number: Business registration number
        email: Primary contact email
        phone: Primary contact phone
        address: Physical address
        city: City
        state: State/province
        country: Country
        postal_code: Postal/ZIP code
        currency: Default currency code (ISO 4217)
        fiscal_year_start: Fiscal year start month (1-12)
        is_active: Whether company is active
        logo_url: URL to company logo
        website: Company website
        notes: Additional notes
    """

    __tablename__ = "companies"

    # Basic Information
    name = Column(String(255), nullable=False, unique=True, comment="Company legal name")
    trade_name = Column(String(255), nullable=True, comment="Trading name")
    tax_id = Column(String(50), nullable=True, unique=True, comment="Tax ID number")
    registration_number = Column(
        String(50), nullable=True, unique=True, comment="Business registration number"
    )

    # Contact Information
    email = Column(String(255), nullable=True, comment="Primary email")
    phone = Column(String(50), nullable=True, comment="Primary phone")
    address = Column(Text, nullable=True, comment="Physical address")
    city = Column(String(100), nullable=True, comment="City")
    state = Column(String(100), nullable=True, comment="State/Province")
    country = Column(String(100), nullable=False, default="US", comment="Country code")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")

    # Financial Settings
    currency = Column(
        String(3), nullable=False, default="USD", comment="Default currency (ISO 4217)"
    )
    fiscal_year_start = Column(
        String(2), nullable=False, default="01", comment="Fiscal year start month (01-12)"
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False, comment="Active status")

    # Additional Information
    logo_url = Column(String(500), nullable=True, comment="Company logo URL")
    website = Column(String(255), nullable=True, comment="Company website")
    notes = Column(Text, nullable=True, comment="Additional notes")

    # Relationships
    branches = relationship(
        "Branch",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="select",
    )

    settings = relationship(
        "Settings",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="select",
    )

    accounts = relationship(
        "Account",
        back_populates="company",
        lazy="select",
    )

    sales = relationship(
        "Sale",
        back_populates="company",
        lazy="select",
    )

    pos_settings = relationship(
        "POSSettings",
        back_populates="company",
        lazy="select",
    )

    customers = relationship(
        "Customer",
        back_populates="company",
        lazy="select",
    )

    suppliers = relationship(
        "Supplier",
        back_populates="company",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Company(id={self.id}, name='{self.name}')>"

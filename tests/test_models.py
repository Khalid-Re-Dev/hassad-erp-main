"""
Model validation and business logic tests.

Tests model methods, properties, and validation logic.
"""

import pytest

from models import Branch, Company, User


def test_company_repr(db_session):
    """Test Company string representation."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    repr_str = repr(company)
    assert "Test Company" in repr_str
    assert str(company.id) in repr_str


def test_user_full_name(db_session):
    """Test User full_name property."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    branch = Branch(
        company_id=company.id,
        name="Test Branch",
        code="TEST-01",
        country="US",
    )
    db_session.add(branch)
    db_session.commit()

    user = User(
        company_id=company.id,
        branch_id=branch.id,
        username="testuser",
        email="test@user.com",
        first_name="John",
        last_name="Doe",
    )
    user.set_password("TestPassword123!")
    db_session.add(user)
    db_session.commit()

    assert user.full_name == "John Doe"


def test_model_to_dict(db_session):
    """Test BaseModel to_dict method."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    company_dict = company.to_dict()

    assert isinstance(company_dict, dict)
    assert "id" in company_dict
    assert "name" in company_dict
    assert company_dict["name"] == "Test Company"
    assert "created_at" in company_dict


def test_version_hash_generation(db_session):
    """Test version hash generation."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    version_hash = company.generate_version_hash()

    assert version_hash is not None
    assert len(version_hash) == 64  # SHA-256 produces 64 character hex string

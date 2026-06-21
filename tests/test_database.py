"""
Database connection and model tests.

Tests basic database connectivity and model operations.
"""

import pytest
from sqlalchemy import inspect

from models import AuditLog, Branch, Company, Permission, Role, Settings, User


def test_database_connection(db_session):
    """Test database connection is working."""
    assert db_session is not None
    assert db_session.bind is not None


def test_all_tables_exist(test_engine):
    """Test that all expected tables are created."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    expected_tables = [
        "companies",
        "branches",
        "users",
        "roles",
        "permissions",
        "user_roles",
        "role_permissions",
        "audit_logs",
        "settings",
    ]

    for table in expected_tables:
        assert table in tables, f"Table '{table}' not found in database"


def test_create_company(db_session):
    """Test creating a company."""
    company = Company(
        name="Test Company",
        trade_name="Test Co",
        tax_id="12-3456789",
        email="test@company.com",
        country="US",
        currency="USD",
    )

    db_session.add(company)
    db_session.commit()

    assert company.id is not None
    assert company.created_at is not None
    assert company.is_active is True


def test_create_branch(db_session):
    """Test creating a branch."""
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

    assert branch.id is not None
    assert branch.company_id == company.id
    assert branch.is_active is True


def test_create_user_with_password(db_session):
    """Test creating a user with password hashing."""
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
        first_name="Test",
        last_name="User",
    )
    user.set_password("TestPassword123!")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.password_hash is not None
    assert user.check_password("TestPassword123!") is True
    assert user.check_password("WrongPassword") is False


def test_role_permission_relationship(db_session):
    """Test role-permission many-to-many relationship."""
    # Create permissions
    perm1 = Permission(
        name="View Users",
        code="users.view",
        module="users",
    )
    perm2 = Permission(
        name="Create Users",
        code="users.create",
        module="users",
    )
    db_session.add_all([perm1, perm2])
    db_session.commit()

    # Create role with permissions
    role = Role(
        name="User Manager",
        code="user_manager",
        description="Manages users",
    )
    role.permissions = [perm1, perm2]
    db_session.add(role)
    db_session.commit()

    # Verify relationship
    assert len(role.permissions) == 2
    assert perm1 in role.permissions
    assert perm2 in role.permissions


def test_user_role_relationship(db_session):
    """Test user-role many-to-many relationship."""
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

    # Create roles
    role1 = Role(name="Admin", code="admin")
    role2 = Role(name="Manager", code="manager")
    db_session.add_all([role1, role2])
    db_session.commit()

    # Create user with roles
    user = User(
        company_id=company.id,
        branch_id=branch.id,
        username="testuser",
        email="test@user.com",
        first_name="Test",
        last_name="User",
    )
    user.set_password("TestPassword123!")
    user.roles = [role1, role2]
    db_session.add(user)
    db_session.commit()

    # Verify relationship
    assert len(user.roles) == 2
    assert role1 in user.roles
    assert role2 in user.roles


def test_soft_delete(db_session):
    """Test soft delete functionality."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    # Soft delete
    company.soft_delete()
    db_session.commit()

    assert company.deleted_at is not None
    assert company.is_deleted() is True


def test_audit_log_creation(db_session):
    """Test creating audit log entries."""
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
        first_name="Test",
        last_name="User",
    )
    user.set_password("TestPassword123!")
    db_session.add(user)
    db_session.commit()

    # Create audit log
    audit = AuditLog(
        user_id=user.id,
        action="CREATE",
        entity_type="company",
        entity_id=company.id,
        new_values={"name": "Test Company"},
        ip_address="127.0.0.1",
    )
    db_session.add(audit)
    db_session.commit()

    assert audit.id is not None
    assert audit.user_id == user.id
    assert audit.action == "CREATE"


def test_settings_creation(db_session):
    """Test creating settings."""
    company = Company(
        name="Test Company",
        email="test@company.com",
        country="US",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()

    # System setting
    system_setting = Settings(
        company_id=None,
        category="system",
        key="app_version",
        value="0.1.0",
        data_type="string",
        is_system="true",
    )
    db_session.add(system_setting)

    # Company setting
    company_setting = Settings(
        company_id=company.id,
        category="accounting",
        key="decimal_places",
        value="2",
        data_type="integer",
        is_system="false",
    )
    db_session.add(company_setting)
    db_session.commit()

    assert system_setting.id is not None
    assert system_setting.company_id is None
    assert company_setting.company_id == company.id

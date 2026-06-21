"""
Seed database with initial test data.

This script populates the database with sample data for development
and testing purposes.

Usage:
    python scripts/seed_data.py
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from models import AuditLog, Branch, Company, Permission, Role, Settings, User


def seed_companies(db: SessionLocal) -> dict:
    """Seed companies."""
    print("Seeding companies...")

    companies = [
        Company(
            id=uuid4(),
            name="Acme Corporation",
            trade_name="Acme Corp",
            tax_id="12-3456789",
            registration_number="REG-001",
            email="info@acmecorp.com",
            phone="+1-555-0100",
            address="123 Business St",
            city="New York",
            state="NY",
            country="US",
            postal_code="10001",
            currency="USD",
            fiscal_year_start="01",
            is_active=True,
        ),
        Company(
            id=uuid4(),
            name="Global Traders LLC",
            trade_name="Global Traders",
            tax_id="98-7654321",
            registration_number="REG-002",
            email="contact@globaltraders.com",
            phone="+1-555-0200",
            address="456 Commerce Ave",
            city="Los Angeles",
            state="CA",
            country="US",
            postal_code="90001",
            currency="USD",
            fiscal_year_start="01",
            is_active=True,
        ),
    ]

    for company in companies:
        db.add(company)

    db.commit()
    print(f"✓ Created {len(companies)} companies")

    return {c.name: c for c in companies}


def seed_branches(db: SessionLocal, companies: dict) -> dict:
    """Seed branches."""
    print("Seeding branches...")

    acme = companies["Acme Corporation"]
    global_traders = companies["Global Traders LLC"]

    branches = [
        Branch(
            id=uuid4(),
            company_id=acme.id,
            name="Acme HQ",
            code="ACME-HQ",
            email="hq@acmecorp.com",
            phone="+1-555-0101",
            address="123 Business St",
            city="New York",
            state="NY",
            country="US",
            postal_code="10001",
            is_active=True,
            is_main=True,
            manager_name="John Smith",
        ),
        Branch(
            id=uuid4(),
            company_id=acme.id,
            name="Acme West",
            code="ACME-WEST",
            email="west@acmecorp.com",
            phone="+1-555-0102",
            address="789 West Blvd",
            city="San Francisco",
            state="CA",
            country="US",
            postal_code="94102",
            is_active=True,
            is_main=False,
            manager_name="Jane Doe",
        ),
        Branch(
            id=uuid4(),
            company_id=global_traders.id,
            name="Global HQ",
            code="GT-HQ",
            email="hq@globaltraders.com",
            phone="+1-555-0201",
            address="456 Commerce Ave",
            city="Los Angeles",
            state="CA",
            country="US",
            postal_code="90001",
            is_active=True,
            is_main=True,
            manager_name="Robert Johnson",
        ),
    ]

    for branch in branches:
        db.add(branch)

    db.commit()
    print(f"✓ Created {len(branches)} branches")

    return {b.code: b for b in branches}


def seed_permissions(db: SessionLocal) -> dict:
    """Seed permissions."""
    print("Seeding permissions...")

    permission_data = [
        # User Management
        ("View Users", "users.view", "users", "View user list and details"),
        ("Create Users", "users.create", "users", "Create new users"),
        ("Edit Users", "users.edit", "users", "Edit existing users"),
        ("Delete Users", "users.delete", "users", "Delete users"),
        # Role Management
        ("View Roles", "roles.view", "roles", "View roles and permissions"),
        ("Manage Roles", "roles.manage", "roles", "Create and edit roles"),
        # Company Management
        ("View Companies", "companies.view", "companies", "View company information"),
        ("Edit Companies", "companies.edit", "companies", "Edit company settings"),
        # Branch Management
        ("View Branches", "branches.view", "branches", "View branch information"),
        ("Manage Branches", "branches.manage", "branches", "Create and edit branches"),
        # Settings
        ("View Settings", "settings.view", "settings", "View system settings"),
        ("Edit Settings", "settings.edit", "settings", "Modify system settings"),
        # Audit Logs
        ("View Audit Logs", "audit.view", "audit", "View audit trail"),
        # Future modules (placeholders)
        ("View Sales", "sales.view", "sales", "View sales transactions"),
        ("Create Sales", "sales.create", "sales", "Create sales transactions"),
        ("View Inventory", "inventory.view", "inventory", "View inventory"),
        ("Manage Inventory", "inventory.manage", "inventory", "Manage inventory"),
        ("View Reports", "reports.view", "reports", "View reports"),
        ("Generate Reports", "reports.generate", "reports", "Generate reports"),
    ]

    permissions = []
    for name, code, module, description in permission_data:
        perm = Permission(
            id=uuid4(),
            name=name,
            code=code,
            module=module,
            description=description,
        )
        permissions.append(perm)
        db.add(perm)

    db.commit()
    print(f"✓ Created {len(permissions)} permissions")

    return {p.code: p for p in permissions}


def seed_roles(db: SessionLocal, permissions: dict) -> dict:
    """Seed roles with permissions."""
    print("Seeding roles...")

    # Admin role - all permissions
    admin_role = Role(
        id=uuid4(),
        name="Administrator",
        code="admin",
        description="Full system access",
        is_active=True,
        is_system=True,
    )
    admin_role.permissions = list(permissions.values())
    db.add(admin_role)

    # Manager role - most permissions except user/role management
    manager_role = Role(
        id=uuid4(),
        name="Manager",
        code="manager",
        description="Branch manager with elevated privileges",
        is_active=True,
        is_system=True,
    )
    manager_perms = [
        "users.view",
        "companies.view",
        "branches.view",
        "settings.view",
        "audit.view",
        "sales.view",
        "sales.create",
        "inventory.view",
        "inventory.manage",
        "reports.view",
        "reports.generate",
    ]
    manager_role.permissions = [permissions[code] for code in manager_perms]
    db.add(manager_role)

    # Cashier role - basic sales permissions
    cashier_role = Role(
        id=uuid4(),
        name="Cashier",
        code="cashier",
        description="Point of sale operator",
        is_active=True,
        is_system=True,
    )
    cashier_perms = ["sales.view", "sales.create", "inventory.view"]
    cashier_role.permissions = [permissions[code] for code in cashier_perms]
    db.add(cashier_role)

    # Accountant role - financial permissions
    accountant_role = Role(
        id=uuid4(),
        name="Accountant",
        code="accountant",
        description="Financial and accounting access",
        is_active=True,
        is_system=True,
    )
    accountant_perms = [
        "companies.view",
        "branches.view",
        "settings.view",
        "audit.view",
        "sales.view",
        "reports.view",
        "reports.generate",
    ]
    accountant_role.permissions = [permissions[code] for code in accountant_perms]
    db.add(accountant_role)

    db.commit()
    print("✓ Created 4 roles with permissions")

    return {
        "admin": admin_role,
        "manager": manager_role,
        "cashier": cashier_role,
        "accountant": accountant_role,
    }


def seed_users(db: SessionLocal, branches: dict, roles: dict) -> None:
    """Seed users."""
    print("Seeding users...")

    acme_hq = branches["ACME-HQ"]
    acme_west = branches["ACME-WEST"]
    gt_hq = branches["GT-HQ"]

    users_data = [
        {
            "username": "admin",
            "email": "admin@acmecorp.com",
            "password": "Admin123!",
            "first_name": "System",
            "last_name": "Administrator",
            "branch": acme_hq,
            "roles": [roles["admin"]],
            "is_superuser": True,
        },
        {
            "username": "jsmith",
            "email": "jsmith@acmecorp.com",
            "password": "Manager123!",
            "first_name": "John",
            "last_name": "Smith",
            "branch": acme_hq,
            "roles": [roles["manager"]],
            "is_superuser": False,
        },
        {
            "username": "jdoe",
            "email": "jdoe@acmecorp.com",
            "password": "Manager123!",
            "first_name": "Jane",
            "last_name": "Doe",
            "branch": acme_west,
            "roles": [roles["manager"]],
            "is_superuser": False,
        },
        {
            "username": "cashier1",
            "email": "cashier1@acmecorp.com",
            "password": "Cashier123!",
            "first_name": "Alice",
            "last_name": "Williams",
            "branch": acme_hq,
            "roles": [roles["cashier"]],
            "is_superuser": False,
        },
        {
            "username": "accountant1",
            "email": "accountant@acmecorp.com",
            "password": "Account123!",
            "first_name": "Bob",
            "last_name": "Anderson",
            "branch": acme_hq,
            "roles": [roles["accountant"]],
            "is_superuser": False,
        },
    ]

    for user_data in users_data:
        user = User(
            id=uuid4(),
            company_id=user_data["branch"].company_id,
            branch_id=user_data["branch"].id,
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_active=True,
            is_superuser=user_data["is_superuser"],
        )
        user.set_password(user_data["password"])
        user.roles = user_data["roles"]
        db.add(user)

    db.commit()
    print(f"✓ Created {len(users_data)} users")


def seed_settings(db: SessionLocal, companies: dict) -> None:
    """Seed system and company settings."""
    print("Seeding settings...")

    acme = companies["Acme Corporation"]

    settings_data = [
        # System settings (company_id = None)
        {
            "company_id": None,
            "category": "system",
            "key": "app_version",
            "value": "0.1.0",
            "data_type": "string",
            "description": "Application version",
            "is_system": "true",
        },
        {
            "company_id": None,
            "category": "system",
            "key": "maintenance_mode",
            "value": "false",
            "data_type": "boolean",
            "description": "Maintenance mode flag",
            "is_system": "false",
        },
        # Company-specific settings
        {
            "company_id": acme.id,
            "category": "accounting",
            "key": "posting_mode",
            "value": "manual",
            "data_type": "string",
            "description": "Transaction posting mode (manual/automatic)",
            "is_system": "false",
        },
        {
            "company_id": acme.id,
            "category": "accounting",
            "key": "decimal_places",
            "value": "2",
            "data_type": "integer",
            "description": "Decimal places for amounts",
            "is_system": "false",
        },
        {
            "company_id": acme.id,
            "category": "inventory",
            "key": "low_stock_threshold",
            "value": "10",
            "data_type": "integer",
            "description": "Low stock alert threshold",
            "is_system": "false",
        },
    ]

    for setting_data in settings_data:
        setting = Settings(
            id=uuid4(),
            company_id=setting_data["company_id"],
            category=setting_data["category"],
            key=setting_data["key"],
            value=setting_data["value"],
            data_type=setting_data["data_type"],
            description=setting_data["description"],
            is_system=setting_data["is_system"],
        )
        db.add(setting)

    db.commit()
    print(f"✓ Created {len(settings_data)} settings")


def seed_audit_log_sample(db: SessionLocal) -> None:
    """Seed sample audit log entry."""
    print("Seeding sample audit log...")

    # Get admin user
    admin = db.query(User).filter(User.username == "admin").first()

    if admin:
        audit = AuditLog(
            id=uuid4(),
            user_id=admin.id,
            action="SEED_DATA",
            entity_type="system",
            entity_id=None,
            old_values=None,
            new_values={"message": "Database seeded with initial data"},
            ip_address="127.0.0.1",
            user_agent="seed_data.py script",
            notes="Initial database seeding completed",
        )
        db.add(audit)
        db.commit()
        print("✓ Created sample audit log entry")


def main() -> None:
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("HASSAD ERP - DATABASE SEEDING")
    print("=" * 60 + "\n")

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_companies = db.query(Company).count()
        if existing_companies > 0:
            print("⚠ Database already contains data!")
            response = input("Do you want to continue? This may create duplicates (y/N): ")
            if response.lower() != "y":
                print("Seeding cancelled.")
                return

        # Seed data in order
        companies = seed_companies(db)
        branches = seed_branches(db, companies)
        permissions = seed_permissions(db)
        roles = seed_roles(db, permissions)
        seed_users(db, branches, roles)
        seed_settings(db, companies)
        seed_audit_log_sample(db)

        print("\n" + "=" * 60)
        print("✓ DATABASE SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nTest Credentials:")
        print("-" * 60)
        print("Administrator:")
        print("  Username: admin")
        print("  Password: Admin123!")
        print("\nManager (HQ):")
        print("  Username: jsmith")
        print("  Password: Manager123!")
        print("\nCashier:")
        print("  Username: cashier1")
        print("  Password: Cashier123!")
        print("\nAccountant:")
        print("  Username: accountant1")
        print("  Password: Account123!")
        print("-" * 60)
        print("\n⚠ IMPORTANT: Change these passwords in production!\n")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

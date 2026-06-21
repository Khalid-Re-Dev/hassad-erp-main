"""Quick seed for minimal app launch."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Company
from models.branch import Branch
from models.user import User
from models.role import Role
from models.permission import Permission

# Database connection
DATABASE_URL = "postgresql+psycopg2://postgres:admin@localhost:5432/hassad_local"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("Creating minimal data for app launch...")
    
    # Create company
    company = Company(
        id=uuid4(),
        name="Test Company",
        currency="USD",
        country="US",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(company)
    db.flush()
    print(f"✓ Created company: {company.name}")
    
    # Create branch
    branch = Branch(
        id=uuid4(),
        company_id=company.id,
        name="Main Branch",
        code="MAIN",
        country="US",
        is_active=True,
        is_main=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(branch)
    db.flush()
    print(f"✓ Created branch: {branch.name}")
    
    # Create permission
    perm = Permission(
        id=uuid4(),
        name="Admin Access",
        code="admin.all",
        module="admin",
        description="Full admin access",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(perm)
    db.flush()
    print(f"✓ Created permission: {perm.name}")
    
    # Create admin role
    role = Role(
        id=uuid4(),
        name="Administrator",
        code="admin",
        description="System administrator",
        is_active=True,
        is_system=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    role.permissions = [perm]
    db.add(role)
    db.flush()
    print(f"✓ Created role: {role.name}")
    
    # Create admin user
    user = User(
        id=uuid4(),
        company_id=company.id,
        branch_id=branch.id,
        username="admin",
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_superuser=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.set_password("admin123")
    user.roles = [role]
    db.add(user)
    
    db.commit()
    print(f"✓ Created user: {user.username}")
    print("\n✅ Minimal data created successfully!")
    print(f"\nLogin credentials:")
    print(f"  Username: admin")
    print(f"  Password: admin123")
    
except Exception as e:
    db.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

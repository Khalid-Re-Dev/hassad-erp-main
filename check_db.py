#!/usr/bin/env python
"""Quick database connectivity and user check."""

from core.database import SessionLocal
from models import User

try:
    db = SessionLocal()
    
    # Check admin user
    admin = db.query(User).filter(User.username == 'admin').first()
    
    if admin:
        print("✅ Database connected successfully!")
        print(f"✅ Admin user exists: {admin.username}")
        print(f"✅ Admin email: {admin.email}")
        print(f"✅ Admin full name: {admin.full_name}")
        print(f"✅ Is superuser: {admin.is_superuser}")
        print(f"✅ Roles: {', '.join([r.name for r in admin.roles])}")
        print("\n🔐 Default credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("❌ Admin user not found!")
        print("   Run: python scripts/quick_seed.py")
    
    # Count total users
    user_count = db.query(User).count()
    print(f"\n📊 Total users in database: {user_count}")
    
    db.close()
    print("\n✅ Database check complete!")
    
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)

from models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql+psycopg2://postgres:admin@localhost:5432/hassad_local')
Session = sessionmaker(bind=engine)
db = Session()

admin = db.query(User).filter_by(username='admin').first()
print(f'Admin user: {admin.username}')
print(f'Password check (admin123): {admin.check_password("admin123")}')
print(f'Password check (Admin123!): {admin.check_password("Admin123!")}')
print(f'Is active: {admin.is_active}')
print(f'Is superuser: {admin.is_superuser}')
db.close()
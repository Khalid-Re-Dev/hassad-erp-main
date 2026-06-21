# Development Guide

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Git
- Poetry (recommended) or pip

### Initial Setup

1. **Clone the repository**
   \`\`\`bash
   cd hassad
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   poetry install  # or: pip install -r requirements.txt
   \`\`\`

4. **Configure environment**
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your settings
   \`\`\`

5. **Create database**
   \`\`\`bash
   ./scripts/create_test_db.sh  # or .ps1 on Windows
   \`\`\`

6. **Run migrations**
   \`\`\`bash
   ./scripts/run_migrations.sh  # or .ps1 on Windows
   \`\`\`

7. **Seed data**
   \`\`\`bash
   python scripts/seed_data.py
   \`\`\`

## Project Structure

\`\`\`
hassad/
├── core/               # Core configuration and utilities
│   ├── config.py      # Pydantic settings
│   └── database.py    # Database connection
├── models/            # SQLAlchemy ORM models
│   ├── base.py       # Base model class
│   ├── company.py    # Company model
│   ├── branch.py     # Branch model
│   ├── user.py       # User model
│   └── ...
├── services/          # Business logic (future)
├── api/              # REST API endpoints (future)
├── ui/               # Desktop UI (future)
├── migrations/       # Alembic migrations
├── scripts/          # Utility scripts
├── tests/            # Test suite
└── docs/             # Documentation
\`\`\`

## Development Workflow

### 1. Create Feature Branch

\`\`\`bash
git checkout -b feature/your-feature-name
\`\`\`

### 2. Make Changes

Follow coding standards:
- Use type hints
- Write docstrings
- Follow PEP8
- Add tests

### 3. Run Tests

\`\`\`bash
pytest
pytest --cov=. --cov-report=html
\`\`\`

### 4. Format Code

\`\`\`bash
./scripts/format_and_lint.sh  # or .ps1 on Windows
\`\`\`

### 5. Commit Changes

\`\`\`bash
git add .
git commit -m "feat: add new feature"
\`\`\`

Use conventional commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

### 6. Push and Create PR

\`\`\`bash
git push origin feature/your-feature-name
\`\`\`

## Database Migrations

### Create New Migration

\`\`\`bash
alembic revision --autogenerate -m "description"
\`\`\`

### Apply Migrations

\`\`\`bash
alembic upgrade head
\`\`\`

### Rollback Migration

\`\`\`bash
alembic downgrade -1
\`\`\`

### View History

\`\`\`bash
alembic history
alembic current
\`\`\`

## Testing

### Run All Tests

\`\`\`bash
pytest
\`\`\`

### Run Specific Test

\`\`\`bash
pytest tests/test_database.py
pytest tests/test_database.py::test_create_company
\`\`\`

### Run with Coverage

\`\`\`bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
\`\`\`

### Test Database

Tests use in-memory SQLite for speed. For PostgreSQL testing:

\`\`\`python
# In conftest.py
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine("postgresql://...")
    # ...
\`\`\`

## Code Style

### Black (Formatter)

\`\`\`bash
black .
black --check .  # Check without modifying
\`\`\`

### isort (Import Sorter)

\`\`\`bash
isort .
isort --check-only .
\`\`\`

### Flake8 (Linter)

\`\`\`bash
flake8 .
\`\`\`

### mypy (Type Checker)

\`\`\`bash
mypy .
\`\`\`

## Adding New Models

1. **Create model file** in `models/`
2. **Import in** `models/__init__.py`
3. **Create migration**:
   \`\`\`bash
   alembic revision --autogenerate -m "add new model"
   \`\`\`
4. **Review migration** in `migrations/versions/`
5. **Apply migration**:
   \`\`\`bash
   alembic upgrade head
   \`\`\`
6. **Add tests** in `tests/`

## Environment Variables

Required variables in `.env`:

\`\`\`env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hassad_erp
DB_USER=hassad_user
DB_PASSWORD=your_password

# Application
APP_ENV=development
APP_DEBUG=true
SECRET_KEY=your_secret_key
\`\`\`

## Debugging

### Enable SQL Logging

In `.env`:
\`\`\`env
APP_DEBUG=true
\`\`\`

Or in code:
\`\`\`python
engine = create_engine(url, echo=True)
\`\`\`

### Database Inspection

\`\`\`bash
psql -U hassad_user -d hassad_erp

\dt          # List tables
\d users     # Describe table
SELECT * FROM users LIMIT 5;
\`\`\`

### Python Debugger

\`\`\`python
import pdb; pdb.set_trace()
\`\`\`

Or use IDE debugger (VSCode, PyCharm).

## Common Issues

### Database Connection Error

- Check PostgreSQL is running
- Verify `.env` credentials
- Test connection:
  \`\`\`bash
  psql -U hassad_user -d hassad_erp
  \`\`\`

### Migration Conflicts

- Pull latest changes
- Resolve conflicts in migration files
- Or reset migrations (⚠️ destroys data):
  \`\`\`bash
  alembic downgrade base
  alembic upgrade head
  \`\`\`

### Import Errors

- Ensure virtual environment is activated
- Reinstall dependencies:
  \`\`\`bash
  pip install -r requirements.txt
  \`\`\`

## Best Practices

1. **Always use type hints**
2. **Write docstrings for public APIs**
3. **Add tests for new features**
4. **Keep functions small and focused**
5. **Use meaningful variable names**
6. **Don't commit `.env` file**
7. **Run tests before committing**
8. **Format code before committing**
9. **Write clear commit messages**
10. **Review your own PR before requesting review**

## Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://pep8.org/)

## Next Steps

After completing Phase 1 setup:

1. Familiarize yourself with the codebase
2. Run all tests to ensure everything works
3. Review database schema documentation
4. Prepare for Phase 2: Core Accounting Engine

## Support

For questions or issues:
1. Check documentation in `docs/`
2. Review existing issues
3. Contact development team

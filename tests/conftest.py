"""
Pytest configuration and fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# ---------------------------------------------------------------------------
# SQLite compatibility for PostgreSQL UUID columns.
#
# Production runs on PostgreSQL, where models use the native postgresql.UUID
# type. The test suite uses an in-memory SQLite engine for speed, and SQLite
# has no native UUID type, so the default compiler raises
# UnsupportedCompilationError. Registering a SQLite-only compilation rule lets
# the same models create their tables on SQLite (stored as CHAR(32)) WITHOUT
# changing any production model definition or PostgreSQL behaviour. The UUID
# type's own bind/result processing still returns uuid.UUID objects.
# ---------------------------------------------------------------------------
@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_on_sqlite(element, compiler, **kw):  # pragma: no cover - DDL hook
    return "CHAR(32)"


from models.base import Base
from models.inventory import Product
from models.purchases import Supplier, PurchaseOrder, PurchaseOrderLine, PurchaseInvoice, PurchaseInvoiceLine, POStatus, InvoiceStatus
from models.accounting import Account, AccountType
import uuid
from datetime import datetime, timezone, timedelta


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test."""
    TestSessionLocal = sessionmaker(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_company(db_session):
    """Create a test company"""
    from models.company import Company
    
    company = Company(
        id=uuid.uuid4(),
        name="Test Company Ltd",
        legal_name="Test Company Limited",
        tax_id="300123456700003",
        currency="SAR",
        fiscal_year_start=1,
        is_active=True
    )
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def test_branch(db_session, test_company):
    """Create a test branch"""
    from models.branch import Branch
    
    branch = Branch(
        id=uuid.uuid4(),
        company_id=test_company.id,
        name="Main Branch",
        code="MAIN",
        is_active=True
    )
    db_session.add(branch)
    db_session.commit()
    return branch


@pytest.fixture
def test_user(db_session, test_company):
    """Create a test user"""
    from models.user import User
    
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_products(db_session, test_company):
    """Create test products"""
    import uuid
    
    products = []
    for i in range(3):
        product = Product(
            id=uuid.uuid4(),
            company_id=test_company.id,
            sku=f"TEST-PROD-{i+1:03d}",
            barcode=f"123456789{i:03d}",
            name_en=f"Test Product {i+1}",
            name_ar=f"منتج تجريبي {i+1}",
            track_batches=False,
            track_expiry=False
        )
        products.append(product)
        db_session.add(product)
    
    db_session.commit()
    return products


@pytest.fixture
def test_supplier(db_session, test_company):
    """Create a test supplier"""
    from decimal import Decimal
    
    supplier = Supplier(
        id=uuid.uuid4(),
        company_id=test_company.id,
        name="Test Supplier Ltd",
        tax_id="300987654300003",
        contact_name="John Doe",
        email="john@testsupplier.com",
        phone="+966501234567",
        default_payment_terms=Decimal("30"),
        is_active=True
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


@pytest.fixture
def test_purchase_order(db_session, test_company, test_branch, test_supplier, test_user, test_products):
    """Create a test purchase order"""
    from decimal import Decimal
    
    po = PurchaseOrder(
        id=uuid.uuid4(),
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        po_number="PO-TEST-001",
        status=POStatus.DRAFT,
        subtotal=Decimal("2550.00"),
        tax_total=Decimal("382.50"),
        total_amount=Decimal("2932.50"),
        created_by=test_user.id
    )
    db_session.add(po)
    db_session.flush()
    
    # Add PO line
    po_line = PurchaseOrderLine(
        id=uuid.uuid4(),
        purchase_order_id=po.id,
        product_id=test_products[0].id,
        description="Test Product 1",
        ordered_qty=Decimal("100"),
        received_qty=Decimal("0"),
        unit_price=Decimal("25.50"),
        tax_rate=Decimal("15"),
        line_subtotal=Decimal("2550.00"),
        line_tax=Decimal("382.50"),
        line_total=Decimal("2932.50")
    )
    db_session.add(po_line)
    db_session.commit()
    
    return po


@pytest.fixture
def test_purchase_invoice(db_session, test_company, test_branch, test_supplier, test_products):
    """Create a test purchase invoice"""
    from datetime import datetime, timezone, timedelta
    from decimal import Decimal
    
    invoice = PurchaseInvoice(
        id=uuid.uuid4(),
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        invoice_number="INV-TEST-001",
        internal_reference="PI-TEST-001",
        status=InvoiceStatus.DRAFT,
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        subtotal=Decimal("2550.00"),
        tax_total=Decimal("382.50"),
        total_amount=Decimal("2932.50"),
        paid_amount=Decimal("0")
    )
    db_session.add(invoice)
    db_session.flush()
    
    # Add invoice line
    invoice_line = PurchaseInvoiceLine(
        id=uuid.uuid4(),
        purchase_invoice_id=invoice.id,
        product_id=test_products[0].id,
        description="Test Product 1",
        quantity=Decimal("100"),
        unit_price=Decimal("25.50"),
        tax_rate=Decimal("15"),
        line_subtotal=Decimal("2550.00"),
        line_tax=Decimal("382.50"),
        line_total=Decimal("2932.50")
    )
    db_session.add(invoice_line)
    db_session.commit()
    
    return invoice


@pytest.fixture
def test_bank_account(db_session, test_company):
    """Create a test bank account"""
    from models.accounting import AccountType
    
    account = Account(
        id=uuid.uuid4(),
        company_id=test_company.id,
        code="1010",
        name_en="Bank Account",
        name_ar="حساب بنكي",
        account_type=AccountType.ASSET,
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_expense_account(db_session, test_company):
    """Create a test expense account"""
    from models.accounting import AccountType
    
    account = Account(
        id=uuid.uuid4(),
        company_id=test_company.id,
        code="5010",
        name_en="General Expenses",
        name_ar="مصروفات عامة",
        account_type=AccountType.EXPENSE,
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account

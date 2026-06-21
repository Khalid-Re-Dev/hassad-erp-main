"""
Integration tests for POS sale creation and posting
"""
import pytest
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from core.database import SessionLocal, engine
from models.base import Base
from models.pos import Sale, SaleLine, Payment, POSSettings, SaleStatus
from models.inventory import Product, StockMovement
from core.pos.schemas import POSCreateRequest, POSItemLine, POSTender, PaymentMethodEnum
from core.pos.pos_service import create_pos_sale


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    
    session.close()
    # Drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def setup_test_data(db_session):
    """Setup test data for POS tests"""
    # Create company, branch, user, accounts, product, etc.
    # This is a simplified version - full implementation would seed all required data
    
    company_id = uuid.uuid4()
    branch_id = uuid.uuid4()
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    
    # Create POS settings
    pos_settings = POSSettings(
        id=uuid.uuid4(),
        company_id=company_id,
        branch_id=branch_id,
        auto_stock_deduct=True,
        auto_post_journal=False,
        default_tax_rate=Decimal('15.00'),
    )
    db_session.add(pos_settings)
    db_session.commit()
    
    return {
        'company_id': company_id,
        'branch_id': branch_id,
        'user_id': user_id,
        'product_id': product_id,
    }


def test_create_pos_sale_pending(db_session, setup_test_data):
    """Test creating a POS sale in pending status"""
    data = setup_test_data
    
    # Create POS request
    request = POSCreateRequest(
        company_id=data['company_id'],
        branch_id=data['branch_id'],
        cashier_user_id=data['user_id'],
        lines=[
            POSItemLine(
                product_id=data['product_id'],
                sku="PROD-001",
                name="Test Product",
                quantity=Decimal('2.0000'),
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('15.00'),
            )
        ],
        tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('230.00'),
            )
        ],
    )
    
    # Create sale
    response = create_pos_sale(db_session, request, auto_post=False)
    
    # Verify response
    assert response.sale_id is not None
    assert response.invoice_no.startswith("INV-")
    assert response.status == "PENDING"
    assert response.totals.subtotal == Decimal('200.00')
    assert response.totals.tax_total == Decimal('30.00')
    assert response.totals.grand_total == Decimal('230.00')
    assert response.totals.change_due == Decimal('0.00')
    
    # Verify database records
    sale = db_session.query(Sale).filter(Sale.id == response.sale_id).first()
    assert sale is not None
    assert sale.status == SaleStatus.PENDING
    assert len(sale.lines) == 1
    assert len(sale.payments) == 1


def test_create_pos_sale_with_auto_post(db_session, setup_test_data):
    """Test creating and auto-posting a POS sale"""
    data = setup_test_data
    
    request = POSCreateRequest(
        company_id=data['company_id'],
        branch_id=data['branch_id'],
        cashier_user_id=data['user_id'],
        lines=[
            POSItemLine(
                product_id=data['product_id'],
                sku="PROD-001",
                name="Test Product",
                quantity=Decimal('1.0000'),
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('15.00'),
            )
        ],
        tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('115.00'),
            )
        ],
    )
    
    # Create and post sale
    response = create_pos_sale(db_session, request, auto_post=True)
    
    # Verify posted status
    assert response.status == "POSTED"
    assert response.journal_entry_id is not None
    
    # Verify database
    sale = db_session.query(Sale).filter(Sale.id == response.sale_id).first()
    assert sale.status == SaleStatus.POSTED
    assert sale.posted_at is not None
    assert sale.journal_entry_id is not None


def test_create_pos_sale_with_multi_payment(db_session, setup_test_data):
    """Test creating a sale with split payment"""
    data = setup_test_data
    
    request = POSCreateRequest(
        company_id=data['company_id'],
        branch_id=data['branch_id'],
        cashier_user_id=data['user_id'],
        lines=[
            POSItemLine(
                product_id=data['product_id'],
                sku="PROD-001",
                name="Test Product",
                quantity=Decimal('1.0000'),
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('15.00'),
            )
        ],
        tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('50.00'),
            ),
            POSTender(
                method=PaymentMethodEnum.CARD,
                amount=Decimal('65.00'),
                card_reference="CARD-123",
            ),
        ],
    )
    
    response = create_pos_sale(db_session, request)
    
    # Verify payments
    sale = db_session.query(Sale).filter(Sale.id == response.sale_id).first()
    assert len(sale.payments) == 2
    
    cash_payment = [p for p in sale.payments if p.method.value == "CASH"][0]
    card_payment = [p for p in sale.payments if p.method.value == "CARD"][0]
    
    assert cash_payment.amount == Decimal('50.00')
    assert card_payment.amount == Decimal('65.00')
    assert card_payment.card_reference == "CARD-123"

"""
Acceptance tests for Phase 4 - POS Module
End-to-end scenarios validating complete POS functionality
"""
import pytest
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from core.database import SessionLocal, engine
from models.base import Base
from models.company import Company, Branch
from models.user import User
from models.accounting import Account, AccountType
from models.inventory import Product, Category, Unit, StockMovement, MovementType
from models.pos import Sale, SaleLine, Payment, POSSettings, Customer, SaleStatus
from core.pos.schemas import POSCreateRequest, POSItemLine, POSTender, PaymentMethodEnum
from core.pos.pos_service import create_pos_sale, process_return
from core.pos.receipt import ReceiptRenderer


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def complete_pos_setup(db_session):
    """Setup complete POS environment with all dependencies"""
    # Create company
    company = Company(
        id=uuid.uuid4(),
        name="Test Company",
        name_ar="شركة اختبار",
        tax_id="123456789",
        currency="SAR",
    )
    db_session.add(company)
    
    # Create branch
    branch = Branch(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Main Branch",
        name_ar="الفرع الرئيسي",
    )
    db_session.add(branch)
    
    # Create user
    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        username="cashier1",
        email="cashier@test.com",
        password_hash="hashed",
        is_active=True,
    )
    db_session.add(user)
    
    # Create accounts
    accounts = {
        'cash': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="1010",
            name="Cash",
            account_type=AccountType.ASSET,
            is_active=True,
        ),
        'card': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="1020",
            name="Bank - Card",
            account_type=AccountType.ASSET,
            is_active=True,
        ),
        'receivable': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="1200",
            name="Accounts Receivable",
            account_type=AccountType.ASSET,
            is_active=True,
        ),
        'inventory': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="1300",
            name="Inventory",
            account_type=AccountType.ASSET,
            is_active=True,
        ),
        'vat': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="2100",
            name="VAT Payable",
            account_type=AccountType.LIABILITY,
            is_active=True,
        ),
        'revenue': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="4000",
            name="Sales Revenue",
            account_type=AccountType.REVENUE,
            is_active=True,
        ),
        'cogs': Account(
            id=uuid.uuid4(),
            company_id=company.id,
            code="5000",
            name="COGS",
            account_type=AccountType.EXPENSE,
            is_active=True,
        ),
    }
    
    for account in accounts.values():
        db_session.add(account)
    
    # Create POS settings
    pos_settings = POSSettings(
        id=uuid.uuid4(),
        company_id=company.id,
        branch_id=branch.id,
        auto_stock_deduct=True,
        auto_post_journal=True,
        default_cash_account_id=accounts['cash'].id,
        default_card_account_id=accounts['card'].id,
        default_receivable_account_id=accounts['receivable'].id,
        default_revenue_account_id=accounts['revenue'].id,
        default_vat_account_id=accounts['vat'].id,
        default_cogs_account_id=accounts['cogs'].id,
        default_inventory_account_id=accounts['inventory'].id,
        default_tax_rate=Decimal('15.00'),
    )
    db_session.add(pos_settings)
    
    # Create category and unit
    category = Category(
        id=uuid.uuid4(),
        company_id=company.id,
        name_en="General",
        name_ar="عام",
    )
    db_session.add(category)
    
    unit = Unit(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Piece",
        symbol="PC",
        conversion_to_base=Decimal('1.0000'),
    )
    db_session.add(unit)
    
    # Create products with stock
    products = []
    for i in range(3):
        product = Product(
            id=uuid.uuid4(),
            company_id=company.id,
            sku=f"PROD-00{i+1}",
            barcode=f"123456789012{i}",
            name_en=f"Product {chr(65+i)}",
            name_ar=f"منتج {chr(65+i)}",
            category_id=category.id,
            base_unit_id=unit.id,
            default_sales_account_id=accounts['revenue'].id,
            default_stock_account_id=accounts['inventory'].id,
            is_active=True,
        )
        db_session.add(product)
        products.append(product)
        
        # Add stock
        stock = StockMovement(
            id=uuid.uuid4(),
            product_id=product.id,
            branch_id=branch.id,
            movement_type=MovementType.IN,
            quantity=Decimal('100.0000'),
            unit_cost=Decimal(f'{50 + i*10}.0000'),
            total_cost=Decimal(f'{(50 + i*10) * 100}.00'),
            reference_type="INITIAL",
            reference_id=uuid.uuid4(),
        )
        db_session.add(stock)
    
    # Create customer
    customer = Customer(
        id=uuid.uuid4(),
        company_id=company.id,
        code="CUST-001",
        name="Test Customer",
        name_ar="عميل اختبار",
        credit_limit=Decimal('10000.00'),
        is_active=True,
    )
    db_session.add(customer)
    
    db_session.commit()
    
    return {
        'company': company,
        'branch': branch,
        'user': user,
        'accounts': accounts,
        'pos_settings': pos_settings,
        'products': products,
        'customer': customer,
    }


def test_complete_pos_sale_workflow(db_session, complete_pos_setup):
    """
    Test complete POS sale workflow:
    1. Create sale with multiple items
    2. Apply discount
    3. Split payment (cash + card)
    4. Verify stock updated
    5. Verify journal posted
    6. Generate receipt
    """
    setup = complete_pos_setup
    
    # Create POS sale request
    request = POSCreateRequest(
        company_id=setup['company'].id,
        branch_id=setup['branch'].id,
        cashier_user_id=setup['user'].id,
        lines=[
            POSItemLine(
                product_id=setup['products'][0].id,
                sku=setup['products'][0].sku,
                name=setup['products'][0].name_en,
                quantity=Decimal('2.0000'),
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('15.00'),
            ),
            POSItemLine(
                product_id=setup['products'][1].id,
                sku=setup['products'][1].sku,
                name=setup['products'][1].name_en,
                quantity=Decimal('1.0000'),
                unit_price=Decimal('60.00'),
                tax_rate=Decimal('15.00'),
            ),
        ],
        tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('150.00'),
            ),
            POSTender(
                method=PaymentMethodEnum.CARD,
                amount=Decimal('150.00'),
                card_reference="CARD-TEST-123",
            ),
        ],
        global_discount_percent=Decimal('5.00'),
        notes="Test sale with split payment",
    )
    
    # Create sale
    response = create_pos_sale(db_session, request, auto_post=True)
    
    # Verify response
    assert response.sale_id is not None
    assert response.invoice_no.startswith("INV-")
    assert response.status == "POSTED"
    assert response.totals.subtotal == Decimal('260.00')
    assert response.totals.discount_total == Decimal('13.00')  # 5% of 260
    assert response.totals.grand_total > Decimal('280.00')  # With tax
    assert response.journal_entry_id is not None
    
    # Verify sale in database
    sale = db_session.query(Sale).filter(Sale.id == response.sale_id).first()
    assert sale is not None
    assert sale.status == SaleStatus.POSTED
    assert sale.posted_at is not None
    assert len(sale.lines) == 2
    assert len(sale.payments) == 2
    
    # Verify payments
    cash_payment = [p for p in sale.payments if p.method == PaymentMethod.CASH][0]
    card_payment = [p for p in sale.payments if p.method == PaymentMethod.CARD][0]
    assert cash_payment.amount == Decimal('150.00')
    assert card_payment.amount == Decimal('150.00')
    assert card_payment.card_reference == "CARD-TEST-123"
    
    # Verify stock movements
    stock_movements = db_session.query(StockMovement).filter(
        StockMovement.reference_type == "SALE",
        StockMovement.reference_id == sale.id
    ).all()
    assert len(stock_movements) == 2
    
    # Verify journal entry exists
    assert sale.journal_entry is not None
    assert len(sale.journal_entry.lines) >= 6  # Cash, Card, Revenue, VAT, COGS, Inventory
    
    # Generate receipt
    renderer = ReceiptRenderer(paper_width="80mm")
    receipt_text = renderer.render_text_receipt(
        sale=sale,
        lines=sale.lines,
        payments=sale.payments,
        company_info={
            'name': setup['company'].name,
            'name_ar': setup['company'].name_ar,
            'tax_id': setup['company'].tax_id,
            'cashier_name': setup['user'].username,
        },
        totals={
            'subtotal': response.totals.subtotal,
            'discount_total': response.totals.discount_total,
            'tax_total': response.totals.tax_total,
            'grand_total': response.totals.grand_total,
            'change_due': response.totals.change_due,
        }
    )
    
    assert receipt_text is not None
    assert sale.invoice_no in receipt_text
    assert "Test Company" in receipt_text


def test_pos_return_workflow(db_session, complete_pos_setup):
    """
    Test POS return workflow:
    1. Create original sale
    2. Process return
    3. Verify stock restored
    4. Verify reverse journal created
    """
    setup = complete_pos_setup
    
    # Create original sale
    original_request = POSCreateRequest(
        company_id=setup['company'].id,
        branch_id=setup['branch'].id,
        cashier_user_id=setup['user'].id,
        lines=[
            POSItemLine(
                product_id=setup['products'][0].id,
                sku=setup['products'][0].sku,
                name=setup['products'][0].name_en,
                quantity=Decimal('2.0000'),
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('15.00'),
            ),
        ],
        tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('230.00'),
            ),
        ],
    )
    
    original_response = create_pos_sale(db_session, original_request, auto_post=True)
    original_sale = db_session.query(Sale).filter(Sale.id == original_response.sale_id).first()
    
    # Get stock before return
    stock_before = db_session.query(StockMovement).filter(
        StockMovement.product_id == setup['products'][0].id
    ).all()
    
    # Process return
    from core.pos.schemas import POSReturnRequest, POSReturnLineItem
    
    return_request = POSReturnRequest(
        original_sale_id=original_sale.id,
        branch_id=setup['branch'].id,
        cashier_user_id=setup['user'].id,
        lines_to_return=[
            POSReturnLineItem(
                sale_line_id=original_sale.lines[0].id,
                quantity_to_return=Decimal('1.0000'),  # Return 1 out of 2
            ),
        ],
        refund_tenders=[
            POSTender(
                method=PaymentMethodEnum.CASH,
                amount=Decimal('115.00'),  # Half of original
            ),
        ],
        reason="Customer requested return",
    )
    
    return_response = process_return(db_session, return_request)
    
    # Verify return response
    assert return_response.return_sale_id is not None
    assert return_response.return_invoice_no.startswith("RET-")
    assert return_response.original_invoice_no == original_sale.invoice_no
    assert return_response.refund_total > Decimal('0.00')
    
    # Verify return sale in database
    return_sale = db_session.query(Sale).filter(Sale.id == return_response.return_sale_id).first()
    assert return_sale is not None
    assert return_sale.is_return is True
    assert return_sale.original_sale_id == original_sale.id
    
    # Verify stock restored
    stock_after = db_session.query(StockMovement).filter(
        StockMovement.product_id == setup['products'][0].id,
        StockMovement.movement_type == MovementType.RETURN
    ).all()
    assert len(stock_after) > 0
    
    # Verify reverse journal
    assert return_sale.journal_entry is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

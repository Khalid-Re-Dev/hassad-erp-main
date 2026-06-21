"""
Tests for Purchase Invoice creation and posting
Tests invoice lifecycle and accounting integration
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from core.purchases.services import (
    create_purchase_invoice,
    verify_purchase_invoice,
    post_purchase_invoice,
    get_purchase_invoice,
)
from core.purchases.schemas import InvoiceCreate, InvoiceLineSchema
from core.purchases.exceptions import PurchaseError
from models.purchases import InvoiceStatus


def test_create_purchase_invoice(db_session: Session, test_company, test_branch, test_supplier, test_products):
    """Test creating a purchase invoice"""
    # Arrange
    lines = [
        InvoiceLineSchema(
            product_id=test_products[0].id,
            description="Test Product 1",
            quantity=Decimal("100"),
            unit_price=Decimal("25.50"),
            tax_rate=Decimal("15")
        ),
        InvoiceLineSchema(
            product_id=test_products[1].id,
            description="Test Product 2",
            quantity=Decimal("50"),
            unit_price=Decimal("30.00"),
            tax_rate=Decimal("15")
        ),
    ]
    
    invoice_dto = InvoiceCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        invoice_number="INV-2025-001",
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        lines=lines,
        notes="Test invoice"
    )
    
    # Act
    invoice = create_purchase_invoice(db_session, invoice_dto)
    
    # Assert
    assert invoice.id is not None
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.internal_reference.startswith("PI-")
    assert len(invoice.lines) == 2
    
    # Check totals
    expected_subtotal = (Decimal("100") * Decimal("25.50")) + (Decimal("50") * Decimal("30.00"))
    expected_tax = expected_subtotal * Decimal("0.15")
    expected_total = expected_subtotal + expected_tax
    
    assert invoice.subtotal == expected_subtotal.quantize(Decimal("0.01"))
    assert invoice.tax_total == expected_tax.quantize(Decimal("0.01"))
    assert invoice.total_amount == expected_total.quantize(Decimal("0.01"))


def test_duplicate_invoice_number_rejected(db_session: Session, test_company, test_branch, test_supplier, test_products):
    """Test that duplicate invoice numbers from same supplier are rejected"""
    # Arrange
    invoice_number = "INV-2025-DUPLICATE"
    
    lines = [
        InvoiceLineSchema(
            product_id=test_products[0].id,
            description="Test Product",
            quantity=Decimal("100"),
            unit_price=Decimal("25.50"),
            tax_rate=Decimal("15")
        )
    ]
    
    invoice_dto = InvoiceCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        invoice_number=invoice_number,
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        lines=lines
    )
    
    # Act - create first invoice
    create_purchase_invoice(db_session, invoice_dto)
    
    # Act & Assert - try to create duplicate
    with pytest.raises(PurchaseError, match="already exists"):
        create_purchase_invoice(db_session, invoice_dto)


def test_verify_purchase_invoice(db_session: Session, test_purchase_invoice, test_user):
    """Test verifying a purchase invoice"""
    # Act
    invoice = verify_purchase_invoice(db_session, test_purchase_invoice.id, test_user.id)
    
    # Assert
    assert invoice.status == InvoiceStatus.VERIFIED


def test_post_purchase_invoice(db_session: Session, test_purchase_invoice, test_user):
    """Test posting a purchase invoice"""
    # Act
    invoice = post_purchase_invoice(db_session, test_purchase_invoice.id, test_user.id)
    
    # Assert
    assert invoice.status == InvoiceStatus.POSTED
    assert invoice.posted_at is not None
    assert invoice.posted_by == test_user.id


def test_cannot_post_already_posted_invoice(db_session: Session, test_purchase_invoice, test_user):
    """Test that already posted invoice cannot be posted again"""
    # Arrange - post first time
    post_purchase_invoice(db_session, test_purchase_invoice.id, test_user.id)
    
    # Act & Assert
    with pytest.raises(PurchaseError):
        post_purchase_invoice(db_session, test_purchase_invoice.id, test_user.id)


def test_invoice_with_expense_items(db_session: Session, test_company, test_branch, test_supplier, test_expense_account):
    """Test invoice with non-inventory expense items"""
    # Arrange
    lines = [
        InvoiceLineSchema(
            product_id=None,  # No product for expense items
            description="Consulting Services",
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
            tax_rate=Decimal("15"),
            expense_account_id=test_expense_account.id
        )
    ]
    
    invoice_dto = InvoiceCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        invoice_number="INV-2025-EXPENSE",
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        lines=lines
    )
    
    # Act
    invoice = create_purchase_invoice(db_session, invoice_dto)
    
    # Assert
    assert invoice.id is not None
    assert invoice.lines[0].product_id is None
    assert invoice.lines[0].expense_account_id == test_expense_account.id


def test_invoice_line_totals_calculation(db_session: Session, test_company, test_branch, test_supplier, test_products):
    """Test that invoice line totals are calculated correctly"""
    # Arrange
    qty = Decimal("100")
    price = Decimal("25.50")
    tax_rate = Decimal("15")
    
    lines = [
        InvoiceLineSchema(
            product_id=test_products[0].id,
            description="Test Product",
            quantity=qty,
            unit_price=price,
            tax_rate=tax_rate
        )
    ]
    
    invoice_dto = InvoiceCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        invoice_number="INV-2025-CALC",
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        lines=lines
    )
    
    # Act
    invoice = create_purchase_invoice(db_session, invoice_dto)
    
    # Assert
    line = invoice.lines[0]
    expected_subtotal = (qty * price).quantize(Decimal("0.01"))
    expected_tax = (expected_subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    expected_total = expected_subtotal + expected_tax
    
    assert line.line_subtotal == expected_subtotal
    assert line.line_tax == expected_tax
    assert line.line_total == expected_total

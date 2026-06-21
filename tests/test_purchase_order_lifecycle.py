"""
Tests for Purchase Order lifecycle
Tests PO creation, submission, approval, and rejection
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.purchases.services import (
    create_purchase_order,
    submit_purchase_order,
    approve_purchase_order,
    reject_purchase_order,
    cancel_purchase_order,
    get_purchase_order,
)
from core.purchases.schemas import POCreate, POLineSchema
from core.purchases.exceptions import InvalidPOStatusError
from models.purchases import POStatus, ApprovalStatus


def test_create_purchase_order(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test creating a purchase order"""
    # Arrange
    lines = [
        POLineSchema(
            product_id=test_products[0].id,
            description="Test Product 1",
            ordered_qty=Decimal("100"),
            unit_price=Decimal("25.50"),
            tax_rate=Decimal("15")
        ),
        POLineSchema(
            product_id=test_products[1].id,
            description="Test Product 2",
            ordered_qty=Decimal("50"),
            unit_price=Decimal("30.00"),
            tax_rate=Decimal("15")
        ),
    ]
    
    po_dto = POCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        created_by=test_user.id,
        lines=lines,
        notes="Test PO"
    )
    
    # Act
    po = create_purchase_order(db_session, po_dto)
    
    # Assert
    assert po.id is not None
    assert po.status == POStatus.DRAFT
    assert po.po_number.startswith("PO-")
    assert len(po.lines) == 2
    
    # Check totals calculation
    expected_subtotal = (Decimal("100") * Decimal("25.50")) + (Decimal("50") * Decimal("30.00"))
    expected_tax = expected_subtotal * Decimal("0.15")
    expected_total = expected_subtotal + expected_tax
    
    assert po.subtotal == expected_subtotal.quantize(Decimal("0.01"))
    assert po.tax_total == expected_tax.quantize(Decimal("0.01"))
    assert po.total_amount == expected_total.quantize(Decimal("0.01"))


def test_submit_purchase_order(db_session: Session, test_purchase_order, test_user):
    """Test submitting a PO for approval"""
    # Act
    po = submit_purchase_order(db_session, test_purchase_order.id, test_user.id, require_approval=True)
    
    # Assert
    assert po.status == POStatus.SUBMITTED
    
    # Check approval request was created
    from models.purchases import ApprovalRequest
    approval = db_session.query(ApprovalRequest).filter(
        ApprovalRequest.entity_id == po.id
    ).first()
    assert approval is not None
    assert approval.status == ApprovalStatus.PENDING


def test_approve_purchase_order(db_session: Session, test_purchase_order, test_user):
    """Test approving a submitted PO"""
    # Arrange - submit first
    submit_purchase_order(db_session, test_purchase_order.id, test_user.id)
    
    # Act
    po = approve_purchase_order(db_session, test_purchase_order.id, test_user.id, "Approved for testing")
    
    # Assert
    assert po.status == POStatus.APPROVED
    assert po.approved_by == test_user.id
    assert po.approved_at is not None


def test_reject_purchase_order(db_session: Session, test_purchase_order, test_user):
    """Test rejecting a submitted PO"""
    # Arrange - submit first
    submit_purchase_order(db_session, test_purchase_order.id, test_user.id)
    
    # Act
    po = reject_purchase_order(db_session, test_purchase_order.id, test_user.id, "Insufficient budget")
    
    # Assert
    assert po.status == POStatus.REJECTED


def test_cannot_approve_draft_po(db_session: Session, test_purchase_order, test_user):
    """Test that draft PO cannot be approved directly"""
    # Act & Assert
    with pytest.raises(InvalidPOStatusError):
        approve_purchase_order(db_session, test_purchase_order.id, test_user.id)


def test_cancel_purchase_order(db_session: Session, test_purchase_order, test_user):
    """Test cancelling a PO"""
    # Act
    po = cancel_purchase_order(db_session, test_purchase_order.id, test_user.id)
    
    # Assert
    assert po.status == POStatus.CANCELLED


def test_po_line_totals_calculation(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test that PO line totals are calculated correctly"""
    # Arrange
    qty = Decimal("100")
    price = Decimal("25.50")
    tax_rate = Decimal("15")
    
    lines = [
        POLineSchema(
            product_id=test_products[0].id,
            description="Test Product",
            ordered_qty=qty,
            unit_price=price,
            tax_rate=tax_rate
        )
    ]
    
    po_dto = POCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        created_by=test_user.id,
        lines=lines
    )
    
    # Act
    po = create_purchase_order(db_session, po_dto)
    
    # Assert
    line = po.lines[0]
    expected_subtotal = (qty * price).quantize(Decimal("0.01"))
    expected_tax = (expected_subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    expected_total = expected_subtotal + expected_tax
    
    assert line.line_subtotal == expected_subtotal
    assert line.line_tax == expected_tax
    assert line.line_total == expected_total

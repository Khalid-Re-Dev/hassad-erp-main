"""
Acceptance Tests for Phase 5 - Purchases Module
End-to-end scenarios testing complete purchase workflows
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from core.purchases.services import (
    create_supplier,
    create_purchase_order,
    submit_purchase_order,
    approve_purchase_order,
    create_goods_receipt,
    create_purchase_invoice,
    post_purchase_invoice,
    record_supplier_payment,
)
from core.purchases.schemas import (
    SupplierCreate,
    POCreate,
    POLineSchema,
    GRNCreate,
    GRNLineSchema,
    InvoiceCreate,
    InvoiceLineSchema,
    PaymentCreate,
)
from models.purchases import POStatus, GRNStatus, InvoiceStatus


def test_complete_purchase_workflow(db_session: Session, test_company, test_branch, test_user, test_products, test_bank_account):
    """
    Test complete purchase workflow:
    1. Create supplier
    2. Create and approve PO
    3. Receive goods (GRN)
    4. Create and post invoice
    5. Record payment
    """
    # Step 1: Create supplier
    supplier_dto = SupplierCreate(
        company_id=test_company.id,
        name="Test Supplier Ltd",
        tax_id="300111222300003",
        contact_name="John Doe",
        email="john@testsupplier.com",
        phone="+966501111111",
        default_payment_terms=Decimal("30")
    )
    supplier = create_supplier(db_session, supplier_dto)
    assert supplier.id is not None
    
    # Step 2: Create and approve PO
    po_lines = [
        POLineSchema(
            product_id=test_products[0].id,
            description=test_products[0].name_en,
            ordered_qty=Decimal("100"),
            unit_price=Decimal("25.00"),
            tax_rate=Decimal("15")
        )
    ]
    
    po_dto = POCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=supplier.id,
        created_by=test_user.id,
        lines=po_lines
    )
    
    po = create_purchase_order(db_session, po_dto)
    assert po.status == POStatus.DRAFT
    
    # Submit and approve
    po = submit_purchase_order(db_session, po.id, test_user.id, require_approval=False)
    po = approve_purchase_order(db_session, po.id, test_user.id)
    assert po.status == POStatus.APPROVED
    
    # Step 3: Receive goods
    grn_lines = [
        GRNLineSchema(
            product_id=test_products[0].id,
            po_line_id=po.lines[0].id,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("100"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.00")
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=supplier.id,
        related_po_id=po.id,
        received_by=test_user.id,
        lines=grn_lines
    )
    
    grn = create_goods_receipt(db_session, grn_dto)
    assert grn.status == GRNStatus.RECEIVED
    
    # Verify stock movement was created
    from models.inventory import StockMovement
    stock_movement = db_session.query(StockMovement).filter(
        StockMovement.reference_id == grn.id
    ).first()
    assert stock_movement is not None
    assert stock_movement.quantity == Decimal("100")
    
    # Step 4: Create and post invoice
    invoice_lines = [
        InvoiceLineSchema(
            product_id=test_products[0].id,
            description=test_products[0].name_en,
            quantity=Decimal("100"),
            unit_price=Decimal("25.00"),
            tax_rate=Decimal("15")
        )
    ]
    
    invoice_dto = InvoiceCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=supplier.id,
        invoice_number="SUP-INV-001",
        related_po_id=po.id,
        invoice_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        lines=invoice_lines
    )
    
    invoice = create_purchase_invoice(db_session, invoice_dto)
    assert invoice.status == InvoiceStatus.DRAFT
    
    invoice = post_purchase_invoice(db_session, invoice.id, test_user.id)
    assert invoice.status == InvoiceStatus.POSTED
    
    # Step 5: Record payment
    payment_dto = PaymentCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=supplier.id,
        purchase_invoice_id=invoice.id,
        payment_date=datetime.now(timezone.utc),
        amount=invoice.total_amount,
        payment_method="BANK_TRANSFER",
        reference_number="TRF-001",
        bank_account_id=test_bank_account.id,
        paid_by=test_user.id
    )
    
    payment = record_supplier_payment(db_session, payment_dto)
    assert payment.id is not None
    
    # Verify invoice is marked as paid
    db_session.refresh(invoice)
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.paid_amount == invoice.total_amount
    
    print("✅ Complete purchase workflow test passed!")


def test_partial_goods_receipt_workflow(db_session: Session, test_company, test_branch, test_user, test_supplier, test_products):
    """Test workflow with partial goods receipt"""
    # Create PO
    po_lines = [
        POLineSchema(
            product_id=test_products[0].id,
            description=test_products[0].name_en,
            ordered_qty=Decimal("100"),
            unit_price=Decimal("25.00"),
            tax_rate=Decimal("15")
        )
    ]
    
    po_dto = POCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        created_by=test_user.id,
        lines=po_lines
    )
    
    po = create_purchase_order(db_session, po_dto)
    po = submit_purchase_order(db_session, po.id, test_user.id, require_approval=False)
    po = approve_purchase_order(db_session, po.id, test_user.id)
    
    # First partial receipt
    grn_lines_1 = [
        GRNLineSchema(
            product_id=test_products[0].id,
            po_line_id=po.lines[0].id,
            received_qty=Decimal("60"),
            accepted_qty=Decimal("60"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.00")
        )
    ]
    
    grn_dto_1 = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        related_po_id=po.id,
        received_by=test_user.id,
        lines=grn_lines_1
    )
    
    grn1 = create_goods_receipt(db_session, grn_dto_1)
    
    # Check PO line received quantity
    db_session.refresh(po.lines[0])
    assert po.lines[0].received_qty == Decimal("60")
    
    # Second partial receipt
    grn_lines_2 = [
        GRNLineSchema(
            product_id=test_products[0].id,
            po_line_id=po.lines[0].id,
            received_qty=Decimal("40"),
            accepted_qty=Decimal("40"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.00")
        )
    ]
    
    grn_dto_2 = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        related_po_id=po.id,
        received_by=test_user.id,
        lines=grn_lines_2
    )
    
    grn2 = create_goods_receipt(db_session, grn_dto_2)
    
    # Check total received quantity
    db_session.refresh(po.lines[0])
    assert po.lines[0].received_qty == Decimal("100")
    assert po.lines[0].received_qty == po.lines[0].ordered_qty
    
    print("✅ Partial goods receipt workflow test passed!")


def test_purchase_with_rejections(db_session: Session, test_company, test_branch, test_user, test_supplier, test_products):
    """Test purchase workflow with rejected items"""
    # Create and approve PO
    po_lines = [
        POLineSchema(
            product_id=test_products[0].id,
            description=test_products[0].name_en,
            ordered_qty=Decimal("100"),
            unit_price=Decimal("25.00"),
            tax_rate=Decimal("15")
        )
    ]
    
    po_dto = POCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        created_by=test_user.id,
        lines=po_lines
    )
    
    po = create_purchase_order(db_session, po_dto)
    po = submit_purchase_order(db_session, po.id, test_user.id, require_approval=False)
    po = approve_purchase_order(db_session, po.id, test_user.id)
    
    # Receive with rejections
    grn_lines = [
        GRNLineSchema(
            product_id=test_products[0].id,
            po_line_id=po.lines[0].id,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("85"),
            rejected_qty=Decimal("15"),
            unit_cost=Decimal("25.00"),
            notes="15 units damaged during shipping"
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        related_po_id=po.id,
        received_by=test_user.id,
        lines=grn_lines
    )
    
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Verify GRN status is PARTIAL
    assert grn.status == GRNStatus.PARTIAL
    
    # Verify only accepted quantity added to stock
    from models.inventory import StockMovement
    stock_movement = db_session.query(StockMovement).filter(
        StockMovement.reference_id == grn.id
    ).first()
    assert stock_movement.quantity == Decimal("85")
    
    print("✅ Purchase with rejections workflow test passed!")

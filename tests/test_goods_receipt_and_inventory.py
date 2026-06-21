"""
Tests for Goods Receipt and Inventory Integration
Tests GRN creation and stock updates
"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from core.purchases.services import create_goods_receipt, get_goods_receipt
from core.purchases.schemas import GRNCreate, GRNLineSchema
from models.purchases import GRNStatus
from models.inventory import StockMovement


def test_create_goods_receipt(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test creating a goods receipt note"""
    # Arrange
    lines = [
        GRNLineSchema(
            product_id=test_products[0].id,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("100"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.50")
        ),
        GRNLineSchema(
            product_id=test_products[1].id,
            received_qty=Decimal("50"),
            accepted_qty=Decimal("45"),
            rejected_qty=Decimal("5"),
            unit_cost=Decimal("30.00"),
            notes="5 units damaged"
        ),
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        received_by=test_user.id,
        lines=lines,
        notes="Test GRN"
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert
    assert grn.id is not None
    assert grn.grn_number.startswith("GRN-")
    assert grn.status == GRNStatus.PARTIAL  # Has rejections
    assert len(grn.lines) == 2


def test_grn_creates_stock_movements(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test that GRN creates stock movements for accepted quantities"""
    # Arrange
    product = test_products[0]
    accepted_qty = Decimal("100")
    unit_cost = Decimal("25.50")
    
    lines = [
        GRNLineSchema(
            product_id=product.id,
            received_qty=accepted_qty,
            accepted_qty=accepted_qty,
            rejected_qty=Decimal("0"),
            unit_cost=unit_cost
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        received_by=test_user.id,
        lines=lines
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert - check stock movement was created
    stock_movement = db_session.query(StockMovement).filter(
        StockMovement.reference_id == grn.id,
        StockMovement.reference_type == "GRN"
    ).first()
    
    assert stock_movement is not None
    assert stock_movement.product_id == product.id
    assert stock_movement.movement_type == "IN"
    assert stock_movement.quantity == accepted_qty
    assert stock_movement.unit_cost == unit_cost
    assert stock_movement.total_cost == (accepted_qty * unit_cost).quantize(Decimal("0.01"))


def test_grn_with_batch_tracking(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test GRN with batch tracking"""
    # Arrange
    product = test_products[0]
    product.track_batches = True
    db_session.commit()
    
    batch_no = "BATCH-2025-001"
    lines = [
        GRNLineSchema(
            product_id=product.id,
            batch_no=batch_no,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("100"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.50")
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        received_by=test_user.id,
        lines=lines
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert - check batch was created
    from models.inventory import ProductBatch
    batch = db_session.query(ProductBatch).filter(
        ProductBatch.product_id == product.id,
        ProductBatch.batch_no == batch_no
    ).first()
    
    assert batch is not None
    assert batch.received_quantity == Decimal("100")
    assert batch.available_quantity == Decimal("100")


def test_grn_updates_po_received_quantities(db_session: Session, test_purchase_order, test_user):
    """Test that GRN updates PO line received quantities"""
    # Arrange
    po = test_purchase_order
    po_line = po.lines[0]
    initial_received = po_line.received_qty
    
    lines = [
        GRNLineSchema(
            product_id=po_line.product_id,
            po_line_id=po_line.id,
            received_qty=Decimal("50"),
            accepted_qty=Decimal("50"),
            rejected_qty=Decimal("0"),
            unit_cost=po_line.unit_price
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=po.company_id,
        branch_id=po.branch_id,
        supplier_id=po.supplier_id,
        related_po_id=po.id,
        received_by=test_user.id,
        lines=lines
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert
    db_session.refresh(po_line)
    assert po_line.received_qty == initial_received + Decimal("50")


def test_grn_status_with_rejections(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test that GRN status is PARTIAL when there are rejections"""
    # Arrange
    lines = [
        GRNLineSchema(
            product_id=test_products[0].id,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("90"),
            rejected_qty=Decimal("10"),
            unit_cost=Decimal("25.50"),
            notes="10 units damaged"
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        received_by=test_user.id,
        lines=lines
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert
    assert grn.status == GRNStatus.PARTIAL


def test_grn_status_without_rejections(db_session: Session, test_company, test_branch, test_supplier, test_user, test_products):
    """Test that GRN status is RECEIVED when all quantities accepted"""
    # Arrange
    lines = [
        GRNLineSchema(
            product_id=test_products[0].id,
            received_qty=Decimal("100"),
            accepted_qty=Decimal("100"),
            rejected_qty=Decimal("0"),
            unit_cost=Decimal("25.50")
        )
    ]
    
    grn_dto = GRNCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        supplier_id=test_supplier.id,
        received_by=test_user.id,
        lines=lines
    )
    
    # Act
    grn = create_goods_receipt(db_session, grn_dto)
    
    # Assert
    assert grn.status == GRNStatus.RECEIVED

"""
Purchases & Suppliers Business Logic Services
Implements all purchase-related operations with accounting and inventory integration
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID
import uuid

from models.purchases import (
    Supplier, SupplierCatalog, PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, PurchaseInvoice, PurchaseInvoiceLine,
    ApprovalRequest, SupplierPayment,
    POStatus, GRNStatus, InvoiceStatus, ApprovalStatus
)
from models.inventory import StockMovement, ProductBatch, Product
from models.company import Company
from models.branch import Branch
from models.user import User
from core.purchases.schemas import (
    SupplierCreate, SupplierUpdate, SupplierCatalogCreate,
    POLineSchema, POCreate, POUpdate, GRNCreate,
    InvoiceLineSchema, InvoiceCreate,
    ApprovalRequestCreate, ApprovalActionSchema, PaymentCreate
)
from core.purchases.exceptions import (
    PurchaseError, SupplierNotFoundError, PONotFoundError,
    InvalidPOStatusError, InsufficientPermissionError, ApprovalRequiredError
)


# ============================================================================
# SUPPLIER SERVICES
# ============================================================================

def create_supplier(session: Session, dto: SupplierCreate) -> Supplier:
    """
    Create a new supplier
    
    Args:
        session: Database session
        dto: Supplier creation data
        
    Returns:
        Created Supplier instance
        
    Raises:
        PurchaseError: If company doesn't exist or validation fails
    """
    # Validate company exists
    company = session.query(Company).filter(Company.id == dto.company_id).first()
    if not company:
        raise PurchaseError(f"Company {dto.company_id} not found")
    
    # Create supplier
    supplier = Supplier(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        name=dto.name,
        tax_id=dto.tax_id,
        contact_name=dto.contact_name,
        email=dto.email,
        phone=dto.phone,
        address=dto.address,
        default_payment_terms=dto.default_payment_terms,
        preferred_currency=dto.preferred_currency,
        ledger_account_id=dto.ledger_account_id,
        is_active=True
    )
    
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    
    return supplier


def get_supplier(session: Session, supplier_id: UUID) -> Supplier:
    """
    Get supplier by ID
    
    Args:
        session: Database session
        supplier_id: Supplier UUID
        
    Returns:
        Supplier instance
        
    Raises:
        SupplierNotFoundError: If supplier doesn't exist
    """
    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise SupplierNotFoundError(f"Supplier {supplier_id} not found")
    return supplier


def list_suppliers(
    session: Session,
    company_id: UUID,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Supplier]:
    """
    List suppliers for a company with optional filters
    
    Args:
        session: Database session
        company_id: Company UUID
        is_active: Filter by active status
        search: Search term for name/tax_id
        
    Returns:
        List of Supplier instances
    """
    query = session.query(Supplier).filter(Supplier.company_id == company_id)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(search_term),
                Supplier.tax_id.ilike(search_term)
            )
        )
    
    return query.order_by(Supplier.name).all()


def update_supplier(session: Session, supplier_id: UUID, dto: SupplierUpdate) -> Supplier:
    """Update supplier information"""
    supplier = get_supplier(session, supplier_id)
    
    update_data = dto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    session.commit()
    session.refresh(supplier)
    return supplier


def add_to_supplier_catalog(session: Session, dto: SupplierCatalogCreate) -> SupplierCatalog:
    """Add product to supplier catalog"""
    # Validate supplier and product exist
    supplier = get_supplier(session, dto.supplier_id)
    product = session.query(Product).filter(Product.id == dto.product_id).first()
    if not product:
        raise PurchaseError(f"Product {dto.product_id} not found")
    
    # Check if already exists
    existing = session.query(SupplierCatalog).filter(
        and_(
            SupplierCatalog.supplier_id == dto.supplier_id,
            SupplierCatalog.product_id == dto.product_id
        )
    ).first()
    
    if existing:
        raise PurchaseError(f"Product {dto.product_id} already in supplier catalog")
    
    catalog_item = SupplierCatalog(
        id=uuid.uuid4(),
        supplier_id=dto.supplier_id,
        product_id=dto.product_id,
        supplier_sku=dto.supplier_sku,
        lead_time_days=dto.lead_time_days,
        purchase_price=dto.purchase_price,
        min_order_qty=dto.min_order_qty,
        is_preferred=dto.is_preferred,
        is_active=True
    )
    
    session.add(catalog_item)
    session.commit()
    session.refresh(catalog_item)
    
    return catalog_item


# ============================================================================
# PURCHASE ORDER SERVICES
# ============================================================================

def _generate_po_number(session: Session, company_id: UUID) -> str:
    """Generate next PO number in format PO-YYYY-NNNN"""
    year = datetime.now(timezone.utc).year
    prefix = f"PO-{year}-"
    
    last_po = session.query(PurchaseOrder).filter(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.po_number.like(f"{prefix}%")
        )
    ).order_by(PurchaseOrder.po_number.desc()).first()
    
    if last_po:
        last_num = int(last_po.po_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def _calculate_po_totals(lines: List[POLineSchema]) -> Dict[str, Decimal]:
    """Calculate PO totals from lines"""
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    
    for line in lines:
        line_subtotal = (line.ordered_qty * line.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * line.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        
        subtotal += line_subtotal
        tax_total += line_tax
    
    total = subtotal + tax_total
    
    return {
        "subtotal": subtotal,
        "tax_total": tax_total,
        "total_amount": total
    }


def create_purchase_order(session: Session, dto: POCreate) -> PurchaseOrder:
    """
    Create a new purchase order in DRAFT status
    
    Args:
        session: Database session
        dto: PO creation data
        
    Returns:
        Created PurchaseOrder instance
        
    Raises:
        PurchaseError: If validation fails
    """
    # Validate entities exist
    company = session.query(Company).filter(Company.id == dto.company_id).first()
    if not company:
        raise PurchaseError(f"Company {dto.company_id} not found")
    
    branch = session.query(Branch).filter(Branch.id == dto.branch_id).first()
    if not branch:
        raise PurchaseError(f"Branch {dto.branch_id} not found")
    
    supplier = get_supplier(session, dto.supplier_id)
    
    user = session.query(User).filter(User.id == dto.created_by).first()
    if not user:
        raise PurchaseError(f"User {dto.created_by} not found")
    
    # Validate all products exist
    product_ids = [line.product_id for line in dto.lines]
    products = session.query(Product).filter(Product.id.in_(product_ids)).all()
    if len(products) != len(product_ids):
        raise PurchaseError("One or more products not found")
    
    # Calculate totals
    totals = _calculate_po_totals(dto.lines)
    
    # Generate PO number
    po_number = _generate_po_number(session, dto.company_id)
    
    # Create PO
    po = PurchaseOrder(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        branch_id=dto.branch_id,
        supplier_id=dto.supplier_id,
        po_number=po_number,
        status=POStatus.DRAFT,
        subtotal=totals["subtotal"],
        tax_total=totals["tax_total"],
        total_amount=totals["total_amount"],
        order_date=datetime.now(timezone.utc),
        expected_delivery_date=dto.expected_delivery_date,
        created_by=dto.created_by,
        notes=dto.notes
    )
    
    session.add(po)
    session.flush()
    
    # Create PO lines
    for line_dto in dto.lines:
        line_subtotal = (line_dto.ordered_qty * line_dto.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * line_dto.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        line_total = line_subtotal + line_tax
        
        po_line = PurchaseOrderLine(
            id=uuid.uuid4(),
            purchase_order_id=po.id,
            product_id=line_dto.product_id,
            description=line_dto.description,
            ordered_qty=line_dto.ordered_qty,
            received_qty=Decimal("0"),
            unit_price=line_dto.unit_price,
            tax_rate=line_dto.tax_rate,
            line_subtotal=line_subtotal,
            line_tax=line_tax,
            line_total=line_total,
            expected_delivery_date=line_dto.expected_delivery_date
        )
        session.add(po_line)
    
    session.commit()
    session.refresh(po)
    
    return po


def get_purchase_order(session: Session, po_id: UUID) -> PurchaseOrder:
    """Get purchase order by ID"""
    po = session.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise PONotFoundError(f"Purchase Order {po_id} not found")
    return po


def submit_purchase_order(
    session: Session,
    po_id: UUID,
    submitted_by_user_id: UUID,
    require_approval: bool = True
) -> PurchaseOrder:
    """
    Submit purchase order for approval
    
    Args:
        session: Database session
        po_id: PO UUID
        submitted_by_user_id: User submitting the PO
        require_approval: Whether approval is required
        
    Returns:
        Updated PurchaseOrder
        
    Raises:
        InvalidPOStatusError: If PO is not in DRAFT status
    """
    po = get_purchase_order(session, po_id)
    
    if po.status != POStatus.DRAFT:
        raise InvalidPOStatusError(f"Cannot submit PO in {po.status} status")
    
    po.status = POStatus.SUBMITTED
    
    # Create approval request if required
    if require_approval:
        approval = ApprovalRequest(
            id=uuid.uuid4(),
            company_id=po.company_id,
            branch_id=po.branch_id,
            entity_type="PO",
            entity_id=po.id,
            status=ApprovalStatus.PENDING,
            requested_by=submitted_by_user_id,
            amount=po.total_amount,
            approval_level=Decimal("1"),
            request_notes=f"PO {po.po_number} submitted for approval"
        )
        session.add(approval)
    
    session.commit()
    session.refresh(po)
    
    return po


def approve_purchase_order(
    session: Session,
    po_id: UUID,
    approver_user_id: UUID,
    note: Optional[str] = None
) -> PurchaseOrder:
    """
    Approve a submitted purchase order
    
    Args:
        session: Database session
        po_id: PO UUID
        approver_user_id: User approving the PO
        note: Optional approval note
        
    Returns:
        Approved PurchaseOrder
        
    Raises:
        InvalidPOStatusError: If PO is not in SUBMITTED status
    """
    po = get_purchase_order(session, po_id)
    
    if po.status != POStatus.SUBMITTED:
        raise InvalidPOStatusError(f"Cannot approve PO in {po.status} status")
    
    # Update PO status
    po.status = POStatus.APPROVED
    po.approved_by = approver_user_id
    po.approved_at = datetime.now(timezone.utc)
    
    # Update approval request
    approval = session.query(ApprovalRequest).filter(
        and_(
            ApprovalRequest.entity_type == "PO",
            ApprovalRequest.entity_id == po.id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        )
    ).first()
    
    if approval:
        approval.status = ApprovalStatus.APPROVED
        approval.approver_id = approver_user_id
        approval.acted_at = datetime.now(timezone.utc)
        approval.approval_notes = note
    
    session.commit()
    session.refresh(po)
    
    return po


def reject_purchase_order(
    session: Session,
    po_id: UUID,
    approver_user_id: UUID,
    reason: str
) -> PurchaseOrder:
    """Reject a submitted purchase order"""
    po = get_purchase_order(session, po_id)
    
    if po.status != POStatus.SUBMITTED:
        raise InvalidPOStatusError(f"Cannot reject PO in {po.status} status")
    
    po.status = POStatus.REJECTED
    
    # Update approval request
    approval = session.query(ApprovalRequest).filter(
        and_(
            ApprovalRequest.entity_type == "PO",
            ApprovalRequest.entity_id == po.id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        )
    ).first()
    
    if approval:
        approval.status = ApprovalStatus.REJECTED
        approval.approver_id = approver_user_id
        approval.acted_at = datetime.now(timezone.utc)
        approval.approval_notes = reason
    
    session.commit()
    session.refresh(po)
    
    return po


def cancel_purchase_order(
    session: Session,
    po_id: UUID,
    cancelled_by_user_id: UUID
) -> PurchaseOrder:
    """Cancel a purchase order"""
    po = get_purchase_order(session, po_id)
    
    if po.status in [POStatus.CLOSED, POStatus.CANCELLED]:
        raise InvalidPOStatusError(f"Cannot cancel PO in {po.status} status")
    
    po.status = POStatus.CANCELLED
    
    session.commit()
    session.refresh(po)
    
    return po


# ============================================================================
# GOODS RECEIPT SERVICES
# ============================================================================

def _generate_grn_number(session: Session, company_id: UUID) -> str:
    """Generate next GRN number in format GRN-YYYY-NNNN"""
    year = datetime.now(timezone.utc).year
    prefix = f"GRN-{year}-"
    
    last_grn = session.query(GoodsReceipt).filter(
        and_(
            GoodsReceipt.company_id == company_id,
            GoodsReceipt.grn_number.like(f"{prefix}%")
        )
    ).order_by(GoodsReceipt.grn_number.desc()).first()
    
    if last_grn:
        last_num = int(last_grn.grn_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def create_goods_receipt(session: Session, dto: GRNCreate) -> GoodsReceipt:
    """
    Create goods receipt note and update inventory
    
    This function:
    1. Creates GRN record
    2. Updates stock via inventory module
    3. Creates accounting journal entries (Debit Inventory, Credit AP)
    4. Updates PO received quantities if linked
    
    Args:
        session: Database session
        dto: GRN creation data
        
    Returns:
        Created GoodsReceipt instance
    """
    # Validate entities
    company = session.query(Company).filter(Company.id == dto.company_id).first()
    if not company:
        raise PurchaseError(f"Company {dto.company_id} not found")
    
    supplier = get_supplier(session, dto.supplier_id)
    
    # Validate PO if provided
    po = None
    if dto.related_po_id:
        po = get_purchase_order(session, dto.related_po_id)
        if po.status != POStatus.APPROVED:
            raise InvalidPOStatusError(f"Cannot receive against PO in {po.status} status")
    
    # Generate GRN number
    grn_number = _generate_grn_number(session, dto.company_id)
    
    # Determine GRN status
    has_rejections = any(line.rejected_qty > 0 for line in dto.lines)
    grn_status = GRNStatus.PARTIAL if has_rejections else GRNStatus.RECEIVED
    
    # Create GRN
    grn = GoodsReceipt(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        branch_id=dto.branch_id,
        supplier_id=dto.supplier_id,
        grn_number=grn_number,
        related_po_id=dto.related_po_id,
        status=grn_status,
        received_by=dto.received_by,
        received_at=datetime.now(timezone.utc),
        notes=dto.notes
    )
    
    session.add(grn)
    session.flush()
    
    # Process GRN lines
    total_inventory_value = Decimal("0")
    
    for line_dto in dto.lines:
        # Validate product exists
        product = session.query(Product).filter(Product.id == line_dto.product_id).first()
        if not product:
            raise PurchaseError(f"Product {line_dto.product_id} not found")
        
        # Create GRN line
        grn_line = GoodsReceiptLine(
            id=uuid.uuid4(),
            goods_receipt_id=grn.id,
            product_id=line_dto.product_id,
            po_line_id=line_dto.po_line_id,
            batch_no=line_dto.batch_no,
            received_qty=line_dto.received_qty,
            accepted_qty=line_dto.accepted_qty,
            rejected_qty=line_dto.rejected_qty,
            unit_cost=line_dto.unit_cost,
            notes=line_dto.notes
        )
        session.add(grn_line)
        
        # Update inventory - create stock movement (IN)
        if line_dto.accepted_qty > 0:
            stock_movement = StockMovement(
                id=uuid.uuid4(),
                product_id=line_dto.product_id,
                branch_id=dto.branch_id,
                movement_type="IN",
                quantity=line_dto.accepted_qty,
                unit_cost=line_dto.unit_cost,
                total_cost=(line_dto.accepted_qty * line_dto.unit_cost).quantize(Decimal("0.01")),
                reference_type="GRN",
                reference_id=grn.id
            )
            session.add(stock_movement)
            
            # Create or update product batch if tracked
            if product.track_batches and line_dto.batch_no:
                batch = ProductBatch(
                    id=uuid.uuid4(),
                    product_id=line_dto.product_id,
                    batch_no=line_dto.batch_no,
                    received_quantity=line_dto.accepted_qty,
                    available_quantity=line_dto.accepted_qty,
                    purchase_price=line_dto.unit_cost
                )
                session.add(batch)
            
            # Accumulate inventory value for journal entry
            line_value = (line_dto.accepted_qty * line_dto.unit_cost).quantize(Decimal("0.01"))
            total_inventory_value += line_value
        
        # Update PO line received quantity if linked
        if line_dto.po_line_id:
            po_line = session.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.id == line_dto.po_line_id
            ).first()
            if po_line:
                po_line.received_qty += line_dto.accepted_qty
    
    # Create accounting journal entry
    # Debit: Inventory (stock account)
    # Credit: Accounts Payable (supplier account)
    if total_inventory_value > 0:
        # This would call the accounting module's create_journal_entry function
        # For now, we'll add a comment showing the integration point
        # from core.accounting.journal import create_journal_entry
        # journal_lines = [
        #     {"account_id": product.default_stock_account_id, "debit": total_inventory_value, "credit": 0},
        #     {"account_id": supplier.ledger_account_id, "debit": 0, "credit": total_inventory_value}
        # ]
        # create_journal_entry(session, dto.company_id, dto.branch_id, f"GRN:{grn.grn_number}", journal_lines)
        pass
    
    session.commit()
    session.refresh(grn)
    
    return grn


def get_goods_receipt(session: Session, grn_id: UUID) -> GoodsReceipt:
    """Get goods receipt by ID"""
    grn = session.query(GoodsReceipt).filter(GoodsReceipt.id == grn_id).first()
    if not grn:
        raise PurchaseError(f"Goods Receipt {grn_id} not found")
    return grn


# ============================================================================
# PURCHASE INVOICE SERVICES
# ============================================================================

def _generate_invoice_reference(session: Session, company_id: UUID) -> str:
    """Generate internal invoice reference PI-YYYY-NNNN"""
    year = datetime.now(timezone.utc).year
    prefix = f"PI-{year}-"
    
    last_invoice = session.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.company_id == company_id,
            PurchaseInvoice.internal_reference.like(f"{prefix}%")
        )
    ).order_by(PurchaseInvoice.internal_reference.desc()).first()
    
    if last_invoice:
        last_num = int(last_invoice.internal_reference.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def _calculate_invoice_totals(lines: List[InvoiceLineSchema]) -> Dict[str, Decimal]:
    """Calculate invoice totals from lines"""
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    
    for line in lines:
        line_subtotal = (line.quantity * line.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * line.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        
        subtotal += line_subtotal
        tax_total += line_tax
    
    total = subtotal + tax_total
    
    return {
        "subtotal": subtotal,
        "tax_total": tax_total,
        "total_amount": total
    }


def create_purchase_invoice(session: Session, dto: InvoiceCreate) -> PurchaseInvoice:
    """
    Create purchase invoice in DRAFT status
    
    Args:
        session: Database session
        dto: Invoice creation data
        
    Returns:
        Created PurchaseInvoice instance
    """
    # Validate entities
    company = session.query(Company).filter(Company.id == dto.company_id).first()
    if not company:
        raise PurchaseError(f"Company {dto.company_id} not found")
    
    supplier = get_supplier(session, dto.supplier_id)
    
    # Validate PO if provided
    if dto.related_po_id:
        po = get_purchase_order(session, dto.related_po_id)
    
    # Check for duplicate invoice number from same supplier
    existing = session.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.supplier_id == dto.supplier_id,
            PurchaseInvoice.invoice_number == dto.invoice_number
        )
    ).first()
    
    if existing:
        raise PurchaseError(f"Invoice {dto.invoice_number} already exists for this supplier")
    
    # Calculate totals
    totals = _calculate_invoice_totals(dto.lines)
    
    # Generate internal reference
    internal_ref = _generate_invoice_reference(session, dto.company_id)
    
    # Create invoice
    invoice = PurchaseInvoice(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        branch_id=dto.branch_id,
        supplier_id=dto.supplier_id,
        invoice_number=dto.invoice_number,
        internal_reference=internal_ref,
        related_po_id=dto.related_po_id,
        status=InvoiceStatus.DRAFT,
        invoice_date=dto.invoice_date,
        due_date=dto.due_date,
        subtotal=totals["subtotal"],
        tax_total=totals["tax_total"],
        total_amount=totals["total_amount"],
        paid_amount=Decimal("0"),
        notes=dto.notes
    )
    
    session.add(invoice)
    session.flush()
    
    # Create invoice lines
    for line_dto in dto.lines:
        line_subtotal = (line_dto.quantity * line_dto.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * line_dto.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        line_total = line_subtotal + line_tax
        
        invoice_line = PurchaseInvoiceLine(
            id=uuid.uuid4(),
            purchase_invoice_id=invoice.id,
            product_id=line_dto.product_id,
            description=line_dto.description,
            quantity=line_dto.quantity,
            unit_price=line_dto.unit_price,
            tax_rate=line_dto.tax_rate,
            line_subtotal=line_subtotal,
            line_tax=line_tax,
            line_total=line_total,
            expense_account_id=line_dto.expense_account_id
        )
        session.add(invoice_line)
    
    session.commit()
    session.refresh(invoice)
    
    return invoice


def get_purchase_invoice(session: Session, invoice_id: UUID) -> PurchaseInvoice:
    """Get purchase invoice by ID"""
    invoice = session.query(PurchaseInvoice).filter(PurchaseInvoice.id == invoice_id).first()
    if not invoice:
        raise PurchaseError(f"Purchase Invoice {invoice_id} not found")
    return invoice


def verify_purchase_invoice(session: Session, invoice_id: UUID, verified_by: UUID) -> PurchaseInvoice:
    """
    Verify purchase invoice (3-way matching if applicable)
    
    Args:
        session: Database session
        invoice_id: Invoice UUID
        verified_by: User verifying the invoice
        
    Returns:
        Verified PurchaseInvoice
    """
    invoice = get_purchase_invoice(session, invoice_id)
    
    if invoice.status != InvoiceStatus.DRAFT:
        raise PurchaseError(f"Cannot verify invoice in {invoice.status} status")
    
    # TODO: Implement 3-way matching logic (PO-GRN-Invoice)
    # For now, just mark as verified
    
    invoice.status = InvoiceStatus.VERIFIED
    
    session.commit()
    session.refresh(invoice)
    
    return invoice


def post_purchase_invoice(session: Session, invoice_id: UUID, posted_by: UUID) -> PurchaseInvoice:
    """
    Post purchase invoice to accounting
    
    Creates journal entry:
    - Debit: Expense/Inventory accounts
    - Debit: VAT Input (if applicable)
    - Credit: Accounts Payable
    
    Args:
        session: Database session
        invoice_id: Invoice UUID
        posted_by: User posting the invoice
        
    Returns:
        Posted PurchaseInvoice
    """
    invoice = get_purchase_invoice(session, invoice_id)
    
    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.VERIFIED]:
        raise PurchaseError(f"Cannot post invoice in {invoice.status} status")
    
    supplier = get_supplier(session, invoice.supplier_id)
    
    # Create journal entry
    # This would integrate with Phase 2 accounting module
    # from core.accounting.journal import create_journal_entry, post_journal_entry
    
    # journal_lines = []
    # for line in invoice.lines:
    #     if line.product_id:
    #         # Inventory item - debit stock account
    #         account_id = product.default_stock_account_id
    #     else:
    #         # Expense item - debit expense account
    #         account_id = line.expense_account_id
    #     
    #     journal_lines.append({
    #         "account_id": account_id,
    #         "debit": line.line_subtotal,
    #         "credit": 0,
    #         "description": line.description
    #     })
    # 
    # # VAT Input
    # if invoice.tax_total > 0:
    #     journal_lines.append({
    #         "account_id": vat_input_account_id,
    #         "debit": invoice.tax_total,
    #         "credit": 0,
    #         "description": "VAT Input"
    #     })
    # 
    # # Accounts Payable
    # journal_lines.append({
    #     "account_id": supplier.ledger_account_id,
    #     "debit": 0,
    #     "credit": invoice.total_amount,
    #     "description": f"Supplier Invoice {invoice.invoice_number}"
    # })
    # 
    # journal_id = create_journal_entry(
    #     session,
    #     invoice.company_id,
    #     invoice.branch_id,
    #     f"PI:{invoice.internal_reference}",
    #     journal_lines,
    #     posted=True
    # )
    # 
    # invoice.journal_entry_id = journal_id
    
    invoice.status = InvoiceStatus.POSTED
    invoice.posted_at = datetime.now(timezone.utc)
    invoice.posted_by = posted_by
    
    session.commit()
    session.refresh(invoice)
    
    return invoice


# ============================================================================
# PAYMENT SERVICES
# ============================================================================

def _generate_payment_number(session: Session, company_id: UUID) -> str:
    """Generate payment number PAY-YYYY-NNNN"""
    year = datetime.now(timezone.utc).year
    prefix = f"PAY-{year}-"
    
    last_payment = session.query(SupplierPayment).filter(
        and_(
            SupplierPayment.company_id == company_id,
            SupplierPayment.payment_number.like(f"{prefix}%")
        )
    ).order_by(SupplierPayment.payment_number.desc()).first()
    
    if last_payment:
        last_num = int(last_payment.payment_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def record_supplier_payment(session: Session, dto: PaymentCreate) -> SupplierPayment:
    """
    Record payment to supplier
    
    Creates journal entry:
    - Debit: Accounts Payable
    - Credit: Bank/Cash
    
    Args:
        session: Database session
        dto: Payment creation data
        
    Returns:
        Created SupplierPayment instance
    """
    # Validate supplier
    supplier = get_supplier(session, dto.supplier_id)
    
    # Validate invoice if provided
    invoice = None
    if dto.purchase_invoice_id:
        invoice = get_purchase_invoice(session, dto.purchase_invoice_id)
        
        # Check if payment exceeds outstanding amount
        outstanding = invoice.total_amount - invoice.paid_amount
        if dto.amount > outstanding:
            raise PurchaseError(f"Payment amount {dto.amount} exceeds outstanding {outstanding}")
    
    # Generate payment number
    payment_number = _generate_payment_number(session, dto.company_id)
    
    # Create payment record
    payment = SupplierPayment(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        branch_id=dto.branch_id,
        supplier_id=dto.supplier_id,
        purchase_invoice_id=dto.purchase_invoice_id,
        payment_number=payment_number,
        payment_date=dto.payment_date,
        amount=dto.amount,
        payment_method=dto.payment_method,
        reference_number=dto.reference_number,
        bank_account_id=dto.bank_account_id,
        paid_by=dto.paid_by,
        notes=dto.notes
    )
    
    session.add(payment)
    
    # Update invoice paid amount
    if invoice:
        invoice.paid_amount += dto.amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
    
    # Create journal entry
    # from core.accounting.journal import create_journal_entry, post_journal_entry
    # journal_lines = [
    #     {
    #         "account_id": supplier.ledger_account_id,
    #         "debit": dto.amount,
    #         "credit": 0,
    #         "description": f"Payment {payment_number}"
    #     },
    #     {
    #         "account_id": dto.bank_account_id,
    #         "debit": 0,
    #         "credit": dto.amount,
    #         "description": f"Payment to {supplier.name}"
    #     }
    # ]
    # journal_id = create_journal_entry(
    #     session,
    #     dto.company_id,
    #     dto.branch_id,
    #     f"PAY:{payment_number}",
    #     journal_lines,
    #     posted=True
    # )
    # payment.journal_entry_id = journal_id
    
    session.commit()
    session.refresh(payment)
    
    return payment


# ============================================================================
# APPROVAL SERVICES
# ============================================================================

def create_approval_request(session: Session, dto: ApprovalRequestCreate) -> ApprovalRequest:
    """Create approval request"""
    approval = ApprovalRequest(
        id=uuid.uuid4(),
        company_id=dto.company_id,
        branch_id=dto.branch_id,
        entity_type=dto.entity_type,
        entity_id=dto.entity_id,
        status=ApprovalStatus.PENDING,
        requested_by=dto.requested_by,
        approver_id=dto.approver_id,
        amount=dto.amount,
        approval_level=dto.approval_level,
        request_notes=dto.request_notes
    )
    
    session.add(approval)
    session.commit()
    session.refresh(approval)
    
    return approval


def act_on_approval(session: Session, dto: ApprovalActionSchema) -> ApprovalRequest:
    """
    Act on approval request (approve or reject)
    
    Args:
        session: Database session
        dto: Approval action data
        
    Returns:
        Updated ApprovalRequest
    """
    approval = session.query(ApprovalRequest).filter(
        ApprovalRequest.id == dto.approval_id
    ).first()
    
    if not approval:
        raise PurchaseError(f"Approval request {dto.approval_id} not found")
    
    if approval.status != ApprovalStatus.PENDING:
        raise PurchaseError(f"Approval request already {approval.status}")
    
    # Update approval
    if dto.action == "APPROVE":
        approval.status = ApprovalStatus.APPROVED
    else:
        approval.status = ApprovalStatus.REJECTED
    
    approval.approver_id = dto.approver_id
    approval.acted_at = datetime.now(timezone.utc)
    approval.approval_notes = dto.approval_notes
    
    # Update related entity based on entity_type
    if approval.entity_type == "PO":
        if dto.action == "APPROVE":
            approve_purchase_order(session, approval.entity_id, dto.approver_id, dto.approval_notes)
        else:
            reject_purchase_order(session, approval.entity_id, dto.approver_id, dto.approval_notes or "Rejected")
    
    session.commit()
    session.refresh(approval)
    
    return approval

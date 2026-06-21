"""
Purchases & Suppliers Models
Implements Purchase Orders, Goods Receipts, Purchase Invoices, Suppliers, and Approval Workflows
"""
from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text, Boolean, Enum as SQLEnum, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from .base import Base


class POStatus(str, enum.Enum):
    """Purchase Order Status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


class GRNStatus(str, enum.Enum):
    """Goods Receipt Note Status"""
    RECEIVED = "RECEIVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"


class InvoiceStatus(str, enum.Enum):
    """Purchase Invoice Status"""
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    POSTED = "POSTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class ApprovalStatus(str, enum.Enum):
    """Approval Request Status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Supplier(Base):
    """
    Supplier/Vendor Master
    Represents suppliers from whom the company purchases goods/services
    """
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=True)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Payment Terms
    default_payment_terms = Column(Numeric(10, 0), default=30, comment="Payment terms in days")
    preferred_currency = Column(String(3), default="SAR")
    
    # Accounting Integration
    ledger_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, 
                               comment="Accounts Payable account for this supplier")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="suppliers")
    ledger_account = relationship("Account", foreign_keys=[ledger_account_id])
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    catalog_items = relationship("SupplierCatalog", back_populates="supplier")
    
    __table_args__ = (
        Index("idx_supplier_company", "company_id"),
        Index("idx_supplier_tax_id", "tax_id"),
    )


class SupplierCatalog(Base):
    """
    Supplier Product Catalog
    Maps products to suppliers with supplier-specific pricing and lead times
    """
    __tablename__ = "supplier_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Supplier-specific details
    supplier_sku = Column(String(100), nullable=True, comment="Supplier's SKU for this product")
    lead_time_days = Column(Numeric(10, 0), default=0, comment="Lead time in days")
    purchase_price = Column(Numeric(18, 4), nullable=False, comment="Purchase price from supplier")
    min_order_qty = Column(Numeric(18, 4), default=1, comment="Minimum order quantity")
    
    # Status
    is_preferred = Column(Boolean, default=False, comment="Is this the preferred supplier for this product")
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="catalog_items")
    product = relationship("Product")
    
    __table_args__ = (
        Index("idx_catalog_supplier_product", "supplier_id", "product_id"),
    )


class PurchaseOrder(Base):
    """
    Purchase Order
    Represents an order placed with a supplier
    """
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # PO Details
    po_number = Column(String(50), nullable=False, unique=True, comment="PO-YYYY-NNNN")
    status = Column(SQLEnum(POStatus), default=POStatus.DRAFT, nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(18, 2), default=0, nullable=False)
    tax_total = Column(Numeric(18, 2), default=0, nullable=False)
    total_amount = Column(Numeric(18, 2), default=0, nullable=False)
    
    # Dates
    order_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Workflow
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")
    invoices = relationship("PurchaseInvoice", back_populates="purchase_order")
    
    __table_args__ = (
        Index("idx_po_company_branch", "company_id", "branch_id"),
        Index("idx_po_supplier", "supplier_id"),
        Index("idx_po_status", "status"),
        Index("idx_po_number", "po_number"),
    )


class PurchaseOrderLine(Base):
    """
    Purchase Order Line Item
    Individual products/items in a purchase order
    """
    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Line Details
    description = Column(String(500), nullable=True)
    ordered_qty = Column(Numeric(18, 4), nullable=False)
    received_qty = Column(Numeric(18, 4), default=0, nullable=False, comment="Quantity received via GRNs")
    unit_price = Column(Numeric(18, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False, comment="Tax rate as percentage")
    
    # Calculated
    line_subtotal = Column(Numeric(18, 2), nullable=False)
    line_tax = Column(Numeric(18, 2), nullable=False)
    line_total = Column(Numeric(18, 2), nullable=False)
    
    # Delivery
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")
    
    __table_args__ = (
        Index("idx_po_line_po", "purchase_order_id"),
        Index("idx_po_line_product", "product_id"),
    )


class GoodsReceipt(Base):
    """
    Goods Receipt Note (GRN)
    Records receipt of goods from supplier
    """
    __tablename__ = "goods_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # GRN Details
    grn_number = Column(String(50), nullable=False, unique=True, comment="GRN-YYYY-NNNN")
    related_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    status = Column(SQLEnum(GRNStatus), default=GRNStatus.RECEIVED, nullable=False)
    
    # Receipt Info
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
    receiver = relationship("User", foreign_keys=[received_by])
    lines = relationship("GoodsReceiptLine", back_populates="goods_receipt", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_grn_company_branch", "company_id", "branch_id"),
        Index("idx_grn_supplier", "supplier_id"),
        Index("idx_grn_po", "related_po_id"),
        Index("idx_grn_number", "grn_number"),
    )


class GoodsReceiptLine(Base):
    """
    Goods Receipt Line Item
    Individual items received in a GRN
    """
    __tablename__ = "goods_receipt_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goods_receipt_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipts.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    
    # Receipt Details
    batch_no = Column(String(100), nullable=True, comment="Batch/Lot number if tracked")
    received_qty = Column(Numeric(18, 4), nullable=False, comment="Quantity received")
    accepted_qty = Column(Numeric(18, 4), nullable=False, comment="Quantity accepted into stock")
    rejected_qty = Column(Numeric(18, 4), default=0, nullable=False, comment="Quantity rejected")
    unit_cost = Column(Numeric(18, 4), nullable=False, comment="Unit cost for this receipt")
    
    # Notes
    notes = Column(Text, nullable=True, comment="Rejection reason or other notes")
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    goods_receipt = relationship("GoodsReceipt", back_populates="lines")
    product = relationship("Product")
    po_line = relationship("PurchaseOrderLine")
    
    __table_args__ = (
        Index("idx_grn_line_grn", "goods_receipt_id"),
        Index("idx_grn_line_product", "product_id"),
    )


class PurchaseInvoice(Base):
    """
    Purchase Invoice
    Supplier invoice for goods/services purchased
    """
    __tablename__ = "purchase_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # Invoice Details
    invoice_number = Column(String(100), nullable=False, comment="Supplier's invoice number")
    internal_reference = Column(String(50), nullable=True, comment="Internal reference PI-YYYY-NNNN")
    related_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(18, 2), default=0, nullable=False)
    tax_total = Column(Numeric(18, 2), default=0, nullable=False)
    total_amount = Column(Numeric(18, 2), default=0, nullable=False)
    paid_amount = Column(Numeric(18, 2), default=0, nullable=False)
    
    # Accounting
    journal_entry_id = Column(UUID(as_uuid=True), nullable=True, comment="Related journal entry when posted")
    posted_at = Column(DateTime(timezone=True), nullable=True)
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    poster = relationship("User", foreign_keys=[posted_by])
    lines = relationship("PurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("SupplierPayment", back_populates="invoice")
    
    __table_args__ = (
        Index("idx_pi_company_branch", "company_id", "branch_id"),
        Index("idx_pi_supplier", "supplier_id"),
        Index("idx_pi_po", "related_po_id"),
        Index("idx_pi_status", "status"),
        Index("idx_pi_invoice_number", "supplier_id", "invoice_number"),
    )


class PurchaseInvoiceLine(Base):
    """
    Purchase Invoice Line Item
    Individual items/services on a purchase invoice
    """
    __tablename__ = "purchase_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_invoice_id = Column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, 
                       comment="Null for service/expense items")
    
    # Line Details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False)
    
    # Calculated
    line_subtotal = Column(Numeric(18, 2), nullable=False)
    line_tax = Column(Numeric(18, 2), nullable=False)
    line_total = Column(Numeric(18, 2), nullable=False)
    
    # Accounting
    expense_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True,
                               comment="Expense account for non-inventory items")
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="lines")
    product = relationship("Product")
    expense_account = relationship("Account")
    
    __table_args__ = (
        Index("idx_pi_line_invoice", "purchase_invoice_id"),
        Index("idx_pi_line_product", "product_id"),
    )


class ApprovalRequest(Base):
    """
    Approval Request
    Generic approval workflow for POs, Invoices, and other entities
    """
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    
    # Entity Reference
    entity_type = Column(String(50), nullable=False, comment="PO, INVOICE, PAYMENT, etc.")
    entity_id = Column(UUID(as_uuid=True), nullable=False, comment="ID of the entity requiring approval")
    
    # Approval Details
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Threshold
    amount = Column(Numeric(18, 2), nullable=True, comment="Amount requiring approval")
    approval_level = Column(Numeric(2, 0), default=1, comment="Approval level/tier")
    
    # Comments
    request_notes = Column(Text, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approver_id])
    
    __table_args__ = (
        Index("idx_approval_entity", "entity_type", "entity_id"),
        Index("idx_approval_status", "status"),
        Index("idx_approval_approver", "approver_id"),
    )


class SupplierPayment(Base):
    """
    Supplier Payment
    Records payments made to suppliers
    """
    __tablename__ = "supplier_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    purchase_invoice_id = Column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"), nullable=True)
    
    # Payment Details
    payment_number = Column(String(50), nullable=False, unique=True, comment="PAY-YYYY-NNNN")
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    payment_method = Column(String(50), nullable=False, comment="CASH, BANK_TRANSFER, CHECK, etc.")
    
    # Reference
    reference_number = Column(String(100), nullable=True, comment="Check number, transfer reference, etc.")
    
    # Accounting
    journal_entry_id = Column(UUID(as_uuid=True), nullable=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    # Workflow
    paid_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    supplier = relationship("Supplier")
    invoice = relationship("PurchaseInvoice", back_populates="payments")
    bank_account = relationship("Account")
    payer = relationship("User", foreign_keys=[paid_by])
    
    __table_args__ = (
        Index("idx_payment_supplier", "supplier_id"),
        Index("idx_payment_invoice", "purchase_invoice_id"),
        Index("idx_payment_date", "payment_date"),
    )

"""
POS and Sales Models
Represents sales transactions, payment records, and POS configuration
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Column, String, DateTime, Boolean, Numeric, Integer, ForeignKey, 
    Text, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.base import Base, TimestampMixin


class PaymentMethod(str, enum.Enum):
    """Payment method types"""
    CASH = "CASH"
    CARD = "CARD"
    CREDIT = "CREDIT"  # Accounts receivable


class SaleStatus(str, enum.Enum):
    """Sale transaction status"""
    PENDING = "PENDING"  # Created but not posted
    POSTED = "POSTED"    # Posted to accounting
    VOIDED = "VOIDED"    # Cancelled/voided
    RETURNED = "RETURNED"  # Fully returned


class Sale(Base, TimestampMixin):
    """
    Main sales transaction record
    Represents a complete POS sale with multiple line items
    """
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    
    # Invoice identification
    invoice_no = Column(String(50), nullable=False, unique=True, index=True)
    invoice_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Customer info (optional for POS)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(200), nullable=True)
    
    # Cashier/user
    cashier_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Financial totals (all in company currency)
    subtotal = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    discount_total = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    tax_total = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    grand_total = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    # Global discount (applied to entire invoice)
    global_discount_percent = Column(Numeric(5, 2), nullable=True)
    global_discount_amount = Column(Numeric(18, 2), nullable=True)
    
    # Status and posting
    status = Column(SQLEnum(SaleStatus), nullable=False, default=SaleStatus.PENDING)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    posted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Accounting integration
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)
    
    # Return/refund tracking
    original_sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=True)
    is_return = Column(Boolean, default=False, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Version for conflict detection
    version = Column(String(64), nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    company = relationship("Company", back_populates="sales")
    branch = relationship("Branch", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    cashier = relationship("User", foreign_keys=[cashier_user_id], back_populates="sales_as_cashier")
    posted_by = relationship("User", foreign_keys=[posted_by_user_id], back_populates="sales_posted")
    lines = relationship("SaleLine", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")
    journal_entry = relationship("JournalEntry", back_populates="sales")
    original_sale = relationship("Sale", remote_side=[id], back_populates="returns")
    returns = relationship("Sale", back_populates="original_sale")
    
    # Indexes
    __table_args__ = (
        Index('idx_sales_company_branch', 'company_id', 'branch_id'),
        Index('idx_sales_invoice_date', 'invoice_date'),
        Index('idx_sales_status', 'status'),
        Index('idx_sales_cashier', 'cashier_user_id'),
        CheckConstraint('grand_total >= 0', name='check_grand_total_positive'),
    )

    def __repr__(self):
        return f"<Sale(invoice_no='{self.invoice_no}', grand_total={self.grand_total}, status='{self.status}')>"


class SaleLine(Base, TimestampMixin):
    """
    Individual line item in a sale
    Represents one product with quantity, price, discount, and tax
    """
    __tablename__ = "sale_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    
    # Product reference
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku = Column(String(100), nullable=False)  # Denormalized for reporting
    product_name = Column(String(200), nullable=False)  # Denormalized
    
    # Batch tracking (optional)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("product_batches.id"), nullable=True)
    
    # Quantity and pricing
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 2), nullable=False)
    
    # Line-level discount
    discount_percent = Column(Numeric(5, 2), nullable=True)
    discount_amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    # Tax
    tax_rate = Column(Numeric(5, 2), nullable=False, default=Decimal('0.00'))
    tax_amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    # Line total (after discount, before tax)
    line_total = Column(Numeric(18, 2), nullable=False)
    
    # Cost tracking (for COGS calculation)
    unit_cost = Column(Numeric(18, 4), nullable=False)  # Weighted average cost at time of sale
    total_cost = Column(Numeric(18, 2), nullable=False)  # quantity * unit_cost
    
    # Relationships
    sale = relationship("Sale", back_populates="lines")
    product = relationship("Product", back_populates="sale_lines")
    batch = relationship("ProductBatch", back_populates="sale_lines")
    
    # Indexes
    __table_args__ = (
        Index('idx_sale_lines_sale', 'sale_id'),
        Index('idx_sale_lines_product', 'product_id'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
    )

    def __repr__(self):
        return f"<SaleLine(product='{self.product_name}', qty={self.quantity}, total={self.line_total})>"


class Payment(Base, TimestampMixin):
    """
    Payment record for a sale
    Supports multi-payment (split payments)
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    
    # Payment details
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    
    # Card payment details (optional)
    card_reference = Column(String(100), nullable=True)  # Transaction ID or last 4 digits
    card_type = Column(String(50), nullable=True)  # VISA, MASTERCARD, etc.
    
    # Credit payment (accounts receivable)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    
    # Accounting integration
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    account = relationship("Account", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index('idx_payments_sale', 'sale_id'),
        Index('idx_payments_method', 'method'),
        CheckConstraint('amount > 0', name='check_payment_amount_positive'),
    )

    def __repr__(self):
        return f"<Payment(method='{self.method}', amount={self.amount})>"


class POSSettings(Base, TimestampMixin):
    """
    POS configuration settings per branch
    Controls POS behavior, receipt formatting, and integration options
    """
    __tablename__ = "pos_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, unique=True)
    
    # Stock management
    auto_stock_deduct = Column(Boolean, default=True, nullable=False)  # Deduct on sale or on post
    allow_negative_stock = Column(Boolean, default=False, nullable=False)
    
    # Accounting integration
    auto_post_journal = Column(Boolean, default=False, nullable=False)  # Auto-post to accounting
    
    # Default accounts for POS transactions
    default_cash_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_card_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_receivable_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_revenue_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_vat_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_cogs_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_inventory_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    rounding_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    # Receipt settings
    receipt_paper_width = Column(String(10), default="80mm", nullable=False)  # 58mm or 80mm
    receipt_header_text = Column(Text, nullable=True)
    receipt_footer_text = Column(Text, nullable=True)
    print_receipt_auto = Column(Boolean, default=True, nullable=False)
    
    # Tax settings
    default_tax_rate = Column(Numeric(5, 2), default=Decimal('15.00'), nullable=False)  # VAT %
    tax_inclusive = Column(Boolean, default=False, nullable=False)  # Tax included in price
    
    # Payment settings
    allow_partial_payment = Column(Boolean, default=False, nullable=False)
    allow_overpayment = Column(Boolean, default=True, nullable=False)
    
    # Return settings
    allow_returns = Column(Boolean, default=True, nullable=False)
    return_window_days = Column(Integer, default=30, nullable=False)
    
    # Printer configuration
    printer_device_path = Column(String(200), nullable=True)  # e.g., /dev/usb/lp0 or COM1
    
    # Relationships
    company = relationship("Company", back_populates="pos_settings")
    branch = relationship("Branch", back_populates="pos_settings")
    
    # Indexes
    __table_args__ = (
        Index('idx_pos_settings_company', 'company_id'),
    )

    def __repr__(self):
        return f"<POSSettings(branch_id='{self.branch_id}', auto_post={self.auto_post_journal})>"


class Customer(Base, TimestampMixin):
    """
    Customer master data
    Used for credit sales and customer tracking
    """
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Customer identification
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    
    # Contact info
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    
    # Tax info
    tax_id = Column(String(50), nullable=True)
    
    # Credit settings
    credit_limit = Column(Numeric(18, 2), nullable=True)
    credit_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="customers")
    sales = relationship("Sale", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    
    # Indexes
    __table_args__ = (
        Index('idx_customers_company', 'company_id'),
        Index('idx_customers_code', 'code'),
    )

    def __repr__(self):
        return f"<Customer(code='{self.code}', name='{self.name}')>"

"""
SQLAlchemy ORM models for Hassad ERP System.

This module exports all database models and provides database session access.
"""

from models.audit_log import AuditLog
from models.base import Base
from models.branch import Branch
from models.company import Company
from models.permission import Permission
from models.role import Role
from models.session_log import SessionLog
from models.settings import Settings
from models.user import User

from models.accounting import Account, JournalEntry, JournalLine, AccountType

from models.inventory import (
    Product, Category, Unit, ProductBatch, StockMovement, MovementType
)

from models.pos import Sale, SaleLine, Payment, POSSettings, Customer, SaleStatus, PaymentMethod

from models.purchases import (
    Supplier, SupplierCatalog, PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, PurchaseInvoice, PurchaseInvoiceLine,
    ApprovalRequest, SupplierPayment,
    POStatus, GRNStatus, InvoiceStatus, ApprovalStatus
)

__all__ = [
    # Phase 1 - Core
    "Base",
    "Company",
    "Branch",
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "SessionLog",
    "Settings",
    # Phase 2 - Accounting
    "Account",
    "JournalEntry",
    "JournalLine",
    "AccountType",
    # Phase 3 - Inventory
    "Product",
    "Category",
    "Unit",
    "ProductBatch",
    "StockMovement",
    "MovementType",
    # Phase 4 - POS
    "Sale",
    "SaleLine",
    "Payment",
    "POSSettings",
    "Customer",
    "SaleStatus",
    "PaymentMethod",
    # Phase 5 - Purchases
    "Supplier",
    "SupplierCatalog",
    "PurchaseOrder",
    "PurchaseOrderLine",
    "GoodsReceipt",
    "GoodsReceiptLine",
    "PurchaseInvoice",
    "PurchaseInvoiceLine",
    "ApprovalRequest",
    "SupplierPayment",
    "POStatus",
    "GRNStatus",
    "InvoiceStatus",
    "ApprovalStatus",
]

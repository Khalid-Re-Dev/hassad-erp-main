"""
Pydantic Schemas for Purchases & Suppliers Module
Type-safe contracts for all purchase-related operations
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from models.purchases import POStatus, GRNStatus, InvoiceStatus, ApprovalStatus


# ============================================================================
# SUPPLIER SCHEMAS
# ============================================================================

class SupplierCreate(BaseModel):
    """Schema for creating a new supplier"""
    company_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    default_payment_terms: Decimal = Field(default=Decimal("30"), ge=0)
    preferred_currency: str = Field(default="SAR", max_length=3)
    ledger_account_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "ABC Suppliers Ltd",
                "tax_id": "300123456700003",
                "contact_name": "Ahmed Ali",
                "email": "ahmed@abcsuppliers.com",
                "phone": "+966501234567",
                "default_payment_terms": 30,
                "preferred_currency": "SAR"
            }
        }


class SupplierUpdate(BaseModel):
    """Schema for updating supplier information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    default_payment_terms: Optional[Decimal] = Field(None, ge=0)
    preferred_currency: Optional[str] = Field(None, max_length=3)
    ledger_account_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class SupplierRead(BaseModel):
    """Schema for reading supplier data"""
    id: UUID
    company_id: UUID
    name: str
    tax_id: Optional[str]
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    default_payment_terms: Decimal
    preferred_currency: str
    ledger_account_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SupplierCatalogCreate(BaseModel):
    """Schema for adding product to supplier catalog"""
    supplier_id: UUID
    product_id: UUID
    supplier_sku: Optional[str] = Field(None, max_length=100)
    lead_time_days: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_price: Decimal = Field(..., gt=0, decimal_places=4)
    min_order_qty: Decimal = Field(default=Decimal("1"), gt=0)
    is_preferred: bool = False
    
    @field_validator("purchase_price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))


# ============================================================================
# PURCHASE ORDER SCHEMAS
# ============================================================================

class POLineSchema(BaseModel):
    """Schema for purchase order line item"""
    product_id: UUID
    description: Optional[str] = Field(None, max_length=500)
    ordered_qty: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("15"), ge=0, le=100)
    expected_delivery_date: Optional[datetime] = None
    
    @field_validator("ordered_qty", "unit_price")
    @classmethod
    def validate_decimals(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174001",
                "description": "Premium Coffee Beans 1kg",
                "ordered_qty": 100,
                "unit_price": 25.50,
                "tax_rate": 15
            }
        }


class POCreate(BaseModel):
    """Schema for creating a purchase order"""
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    created_by: UUID
    lines: List[POLineSchema] = Field(..., min_length=1)
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_lines(self):
        if not self.lines:
            raise ValueError("Purchase order must have at least one line item")
        return self


class POUpdate(BaseModel):
    """Schema for updating purchase order"""
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: Optional[List[POLineSchema]] = None


class PORead(BaseModel):
    """Schema for reading purchase order data"""
    id: UUID
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    po_number: str
    status: POStatus
    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal
    order_date: datetime
    expected_delivery_date: Optional[datetime]
    created_by: UUID
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# GOODS RECEIPT SCHEMAS
# ============================================================================

class GRNLineSchema(BaseModel):
    """Schema for goods receipt line item"""
    product_id: UUID
    po_line_id: Optional[UUID] = None
    batch_no: Optional[str] = Field(None, max_length=100)
    received_qty: Decimal = Field(..., gt=0)
    accepted_qty: Decimal = Field(..., ge=0)
    rejected_qty: Decimal = Field(default=Decimal("0"), ge=0)
    unit_cost: Decimal = Field(..., gt=0, decimal_places=4)
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_quantities(self):
        if self.accepted_qty + self.rejected_qty != self.received_qty:
            raise ValueError("Accepted + Rejected quantities must equal Received quantity")
        return self
    
    @field_validator("received_qty", "accepted_qty", "rejected_qty", "unit_cost")
    @classmethod
    def validate_decimals(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))


class GRNCreate(BaseModel):
    """Schema for creating goods receipt note"""
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    related_po_id: Optional[UUID] = None
    received_by: UUID
    lines: List[GRNLineSchema] = Field(..., min_length=1)
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_lines(self):
        if not self.lines:
            raise ValueError("GRN must have at least one line item")
        return self


class GRNRead(BaseModel):
    """Schema for reading goods receipt data"""
    id: UUID
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    grn_number: str
    related_po_id: Optional[UUID]
    status: GRNStatus
    received_by: UUID
    received_at: datetime
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PURCHASE INVOICE SCHEMAS
# ============================================================================

class InvoiceLineSchema(BaseModel):
    """Schema for purchase invoice line item"""
    product_id: Optional[UUID] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("15"), ge=0, le=100)
    expense_account_id: Optional[UUID] = Field(None, description="For non-inventory items")
    
    @field_validator("quantity", "unit_price")
    @classmethod
    def validate_decimals(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))


class InvoiceCreate(BaseModel):
    """Schema for creating purchase invoice"""
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    invoice_number: str = Field(..., min_length=1, max_length=100)
    related_po_id: Optional[UUID] = None
    invoice_date: datetime
    due_date: datetime
    lines: List[InvoiceLineSchema] = Field(..., min_length=1)
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date < self.invoice_date:
            raise ValueError("Due date cannot be before invoice date")
        if not self.lines:
            raise ValueError("Invoice must have at least one line item")
        return self


class InvoiceRead(BaseModel):
    """Schema for reading purchase invoice data"""
    id: UUID
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    invoice_number: str
    internal_reference: Optional[str]
    related_po_id: Optional[UUID]
    status: InvoiceStatus
    invoice_date: datetime
    due_date: datetime
    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    journal_entry_id: Optional[UUID]
    posted_at: Optional[datetime]
    posted_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# APPROVAL SCHEMAS
# ============================================================================

class ApprovalRequestCreate(BaseModel):
    """Schema for creating approval request"""
    company_id: UUID
    branch_id: UUID
    entity_type: str = Field(..., pattern="^(PO|INVOICE|PAYMENT)$")
    entity_id: UUID
    requested_by: UUID
    approver_id: Optional[UUID] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    approval_level: Decimal = Field(default=Decimal("1"), ge=1)
    request_notes: Optional[str] = None


class ApprovalActionSchema(BaseModel):
    """Schema for acting on approval request"""
    approval_id: UUID
    approver_id: UUID
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    approval_notes: Optional[str] = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentCreate(BaseModel):
    """Schema for creating supplier payment"""
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    purchase_invoice_id: Optional[UUID] = None
    payment_date: datetime
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(..., pattern="^(CASH|BANK_TRANSFER|CHECK|CARD)$")
    reference_number: Optional[str] = Field(None, max_length=100)
    bank_account_id: Optional[UUID] = None
    paid_by: UUID
    notes: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class PaymentRead(BaseModel):
    """Schema for reading payment data"""
    id: UUID
    company_id: UUID
    branch_id: UUID
    supplier_id: UUID
    purchase_invoice_id: Optional[UUID]
    payment_number: str
    payment_date: datetime
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    journal_entry_id: Optional[UUID]
    bank_account_id: Optional[UUID]
    paid_by: UUID
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

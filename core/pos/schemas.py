"""
Pydantic schemas for POS operations
Defines typed contracts for sales, payments, and receipts
"""
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class PaymentMethodEnum(str, Enum):
    """Payment method types"""
    CASH = "CASH"
    CARD = "CARD"
    CREDIT = "CREDIT"


class POSItemLine(BaseModel):
    """
    Single line item in a POS sale
    
    Example:
        {
            "product_id": "123e4567-e89b-12d3-a456-426614174000",
            "sku": "PROD-001",
            "name": "Product Name",
            "quantity": 2.0,
            "unit_price": 100.50,
            "discount_percent": 10.0,
            "tax_rate": 15.0
        }
    """
    product_id: UUID
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    discount_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=100, decimal_places=2)
    
    # Optional batch tracking
    batch_id: Optional[UUID] = None
    
    @field_validator('quantity', 'unit_price', 'discount_percent', 'discount_amount', 'tax_rate')
    @classmethod
    def quantize_decimals(cls, v):
        """Ensure proper decimal precision"""
        if v is not None:
            return v.quantize(Decimal('0.01'))
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "sku": "PROD-001",
                "name": "Sample Product",
                "quantity": "2.0000",
                "unit_price": "100.50",
                "discount_percent": "10.00",
                "tax_rate": "15.00"
            }
        }


class POSTender(BaseModel):
    """
    Payment tender (cash, card, credit)
    
    Example:
        {
            "method": "CASH",
            "amount": 200.00,
            "card_reference": null
        }
    """
    method: PaymentMethodEnum
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    card_reference: Optional[str] = Field(None, max_length=100)
    card_type: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[UUID] = None  # Required for CREDIT method
    
    @field_validator('amount')
    @classmethod
    def quantize_amount(cls, v):
        """Ensure proper decimal precision"""
        return v.quantize(Decimal('0.01'))
    
    @model_validator(mode='after')
    def validate_credit_payment(self):
        """Ensure customer_id is provided for credit payments"""
        if self.method == PaymentMethodEnum.CREDIT and not self.customer_id:
            raise ValueError("customer_id is required for CREDIT payment method")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "method": "CASH",
                "amount": "200.00"
            }
        }


class POSCreateRequest(BaseModel):
    """
    Request to create a new POS sale
    
    Example:
        {
            "company_id": "...",
            "branch_id": "...",
            "cashier_user_id": "...",
            "lines": [...],
            "tenders": [...],
            "global_discount_percent": 5.0,
            "notes": "Customer requested discount"
        }
    """
    company_id: UUID
    branch_id: UUID
    cashier_user_id: UUID
    lines: List[POSItemLine] = Field(..., min_length=1)
    tenders: List[POSTender] = Field(..., min_length=1)
    
    # Optional customer
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = Field(None, max_length=200)
    
    # Global discount (applied to entire invoice)
    global_discount_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    global_discount_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    # Notes
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_discount(self):
        """Ensure only one type of global discount is provided"""
        if self.global_discount_percent and self.global_discount_amount:
            raise ValueError("Cannot specify both global_discount_percent and global_discount_amount")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "branch_id": "123e4567-e89b-12d3-a456-426614174001",
                "cashier_user_id": "123e4567-e89b-12d3-a456-426614174002",
                "lines": [
                    {
                        "product_id": "123e4567-e89b-12d3-a456-426614174003",
                        "sku": "PROD-001",
                        "name": "Product 1",
                        "quantity": "2.0000",
                        "unit_price": "100.00",
                        "tax_rate": "15.00"
                    }
                ],
                "tenders": [
                    {
                        "method": "CASH",
                        "amount": "230.00"
                    }
                ],
                "global_discount_percent": "5.00"
            }
        }


class TotalsBreakdown(BaseModel):
    """Breakdown of sale totals"""
    subtotal: Decimal = Field(..., decimal_places=2)
    discount_total: Decimal = Field(..., decimal_places=2)
    tax_total: Decimal = Field(..., decimal_places=2)
    grand_total: Decimal = Field(..., decimal_places=2)
    total_paid: Decimal = Field(..., decimal_places=2)
    change_due: Decimal = Field(..., decimal_places=2)


class POSCreateResponse(BaseModel):
    """
    Response after creating a POS sale
    
    Example:
        {
            "sale_id": "...",
            "invoice_no": "INV-2024-00001",
            "invoice_date": "2024-01-15T10:30:00Z",
            "totals": {...},
            "status": "POSTED"
        }
    """
    sale_id: UUID
    invoice_no: str
    invoice_date: datetime
    totals: TotalsBreakdown
    status: str  # PENDING or POSTED
    journal_entry_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sale_id": "123e4567-e89b-12d3-a456-426614174000",
                "invoice_no": "INV-2024-00001",
                "invoice_date": "2024-01-15T10:30:00Z",
                "totals": {
                    "subtotal": "200.00",
                    "discount_total": "10.00",
                    "tax_total": "28.50",
                    "grand_total": "218.50",
                    "total_paid": "220.00",
                    "change_due": "1.50"
                },
                "status": "POSTED"
            }
        }


class POSReturnLineItem(BaseModel):
    """Line item to return from original sale"""
    sale_line_id: UUID
    quantity_to_return: Decimal = Field(..., gt=0, decimal_places=4)


class POSReturnRequest(BaseModel):
    """Request to process a return/refund"""
    original_sale_id: UUID
    branch_id: UUID
    cashier_user_id: UUID
    lines_to_return: List[POSReturnLineItem] = Field(..., min_length=1)
    refund_tenders: List[POSTender] = Field(..., min_length=1)
    reason: Optional[str] = None


class POSReturnResponse(BaseModel):
    """Response after processing a return"""
    return_sale_id: UUID
    return_invoice_no: str
    original_invoice_no: str
    refund_total: Decimal
    status: str
    journal_entry_id: Optional[UUID] = None

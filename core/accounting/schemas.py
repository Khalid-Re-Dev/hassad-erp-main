"""
Pydantic schemas for accounting operations.
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import date


class JournalLineSchema(BaseModel):
    """Schema for journal entry line"""
    account_id: UUID
    debit: Decimal = Field(default=Decimal('0.00'), ge=0)
    credit: Decimal = Field(default=Decimal('0.00'), ge=0)
    description: Optional[str] = None

    @field_validator('debit', 'credit')
    @classmethod
    def quantize_amounts(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal('0.01'))

    @field_validator('debit', 'credit')
    @classmethod
    def validate_not_both(cls, v: Decimal, info) -> Decimal:
        """Ensure either debit or credit is zero"""
        if info.data.get('debit', Decimal('0')) > 0 and info.data.get('credit', Decimal('0')) > 0:
            raise ValueError("Cannot have both debit and credit on same line")
        return v


class JournalCreateSchema(BaseModel):
    """Schema for creating journal entry"""
    company_id: UUID
    branch_id: UUID
    reference: str = Field(..., min_length=1, max_length=255)
    entry_date: date
    description: Optional[str] = None
    lines: List[JournalLineSchema] = Field(..., min_length=2)
    created_by: UUID

    @field_validator('lines')
    @classmethod
    def validate_balanced(cls, lines: List[JournalLineSchema]) -> List[JournalLineSchema]:
        """Ensure debits equal credits"""
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        
        if total_debit != total_credit:
            raise ValueError(
                f"Journal entry not balanced: Debits={total_debit}, Credits={total_credit}"
            )
        
        return lines


class PostJournalSchema(BaseModel):
    """Schema for posting journal entry"""
    journal_id: UUID
    posted_by: UUID

"""
Pydantic schemas for reporting requests and responses.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReportType(str, Enum):
    """Available report types."""
    TRIAL_BALANCE = "trial_balance"
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    SALES_BY_DAY = "sales_by_day"
    SALES_BY_PRODUCT = "sales_by_product"
    PURCHASES_SUMMARY = "purchases_summary"
    STOCK_MOVEMENT = "stock_movement"
    INVENTORY_VALUATION = "inventory_valuation"
    CUSTOMER_LEDGER = "customer_ledger"
    SUPPLIER_LEDGER = "supplier_ledger"
    DASHBOARD_METRICS = "dashboard_metrics"


class ReportFormat(str, Enum):
    """Output format for reports."""
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ReportRequest(BaseModel):
    """Request schema for report generation."""
    report_type: ReportType
    format: ReportFormat = ReportFormat.EXCEL
    company_id: UUID
    branch_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    as_of_date: Optional[date] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    language: str = Field(default="ar", description="ar or en")
    include_zero_balances: bool = False

    @field_validator('date_from', 'date_to', 'as_of_date')
    @classmethod
    def validate_dates(cls, v):
        """Ensure dates are not in the future."""
        if v and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "trial_balance",
                "format": "excel",
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "as_of_date": "2025-10-26",
                "language": "ar",
                "include_zero_balances": False
            }
        }


class ReportResult(BaseModel):
    """Result of report generation."""
    report_type: ReportType
    format: ReportFormat
    filename: str
    content: bytes
    mime_type: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class TrialBalanceRow(BaseModel):
    """Single row in trial balance report."""
    account_code: str
    account_name_en: str
    account_name_ar: str
    account_type: str
    debit: Decimal = Field(decimal_places=2)
    credit: Decimal = Field(decimal_places=2)


class BalanceSheetSection(BaseModel):
    """Section in balance sheet (Assets, Liabilities, Equity)."""
    section_name_en: str
    section_name_ar: str
    accounts: List[Dict[str, Any]]
    total: Decimal = Field(decimal_places=2)


class IncomeStatementSection(BaseModel):
    """Section in income statement (Revenue, Expenses)."""
    section_name_en: str
    section_name_ar: str
    accounts: List[Dict[str, Any]]
    total: Decimal = Field(decimal_places=2)


class SalesReportRow(BaseModel):
    """Single row in sales report."""
    date: date
    invoice_no: str
    customer_name: Optional[str] = None
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal


class DashboardMetrics(BaseModel):
    """Dashboard summary metrics."""
    sales_today: Decimal = Field(decimal_places=2)
    sales_this_month: Decimal = Field(decimal_places=2)
    ar_outstanding: Decimal = Field(decimal_places=2)
    ap_outstanding: Decimal = Field(decimal_places=2)
    low_stock_count: int
    pending_approvals: int
    cash_balance: Decimal = Field(decimal_places=2)
    inventory_value: Decimal = Field(decimal_places=2)

"""
Core report generation logic.
Integrates with Accounting (Phase 2), Inventory (Phase 3), POS (Phase 4), and Purchases (Phase 5).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from models.accounting import Account, JournalEntry, JournalLine
from models.inventory import Product, StockMovement
from models.pos import Sale, SaleLine
from models.purchases import PurchaseInvoice, PurchaseInvoiceLine, Supplier
from .schemas import (
    ReportRequest, ReportResult, ReportType, ReportFormat,
    TrialBalanceRow, DashboardMetrics
)
from .excel import ExcelReportGenerator
from .pdf import PDFReportGenerator


class ReportGenerator:
    """Main report generation service."""

    def __init__(self, session: Session):
        self.session = session
        self.excel_gen = ExcelReportGenerator()
        self.pdf_gen = PDFReportGenerator()

    def generate(self, request: ReportRequest) -> ReportResult:
        """
        Generate report based on request.
        
        Args:
            request: ReportRequest with type, format, and parameters
            
        Returns:
            ReportResult with file content and metadata
            
        Raises:
            ValueError: If report type or format not supported
        """
        # Get report data
        data = self._get_report_data(request)
        
        # Generate output in requested format
        if request.format == ReportFormat.EXCEL:
            content, filename = self.excel_gen.generate(
                request.report_type, data, request.language
            )
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif request.format == ReportFormat.PDF:
            content, filename = self.pdf_gen.generate(
                request.report_type, data, request.language
            )
            mime_type = "application/pdf"
        elif request.format == ReportFormat.CSV:
            content, filename = self._generate_csv(request.report_type, data)
            mime_type = "text/csv"
        elif request.format == ReportFormat.JSON:
            import json
            content = json.dumps(data, default=str, ensure_ascii=False).encode('utf-8')
            filename = f"{request.report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            mime_type = "application/json"
        else:
            raise ValueError(f"Unsupported format: {request.format}")
        
        return ReportResult(
            report_type=request.report_type,
            format=request.format,
            filename=filename,
            content=content,
            mime_type=mime_type,
            metadata={
                "company_id": str(request.company_id),
                "branch_id": str(request.branch_id) if request.branch_id else None,
                "date_from": str(request.date_from) if request.date_from else None,
                "date_to": str(request.date_to) if request.date_to else None,
                "language": request.language
            }
        )

    def _get_report_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Route to appropriate data gathering method."""
        handlers = {
            ReportType.TRIAL_BALANCE: self._get_trial_balance_data,
            ReportType.BALANCE_SHEET: self._get_balance_sheet_data,
            ReportType.INCOME_STATEMENT: self._get_income_statement_data,
            ReportType.SALES_BY_DAY: self._get_sales_by_day_data,
            ReportType.SALES_BY_PRODUCT: self._get_sales_by_product_data,
            ReportType.PURCHASES_SUMMARY: self._get_purchases_summary_data,
            ReportType.STOCK_MOVEMENT: self._get_stock_movement_data,
            ReportType.INVENTORY_VALUATION: self._get_inventory_valuation_data,
            ReportType.SUPPLIER_LEDGER: self._get_supplier_ledger_data,
            ReportType.DASHBOARD_METRICS: self._get_dashboard_metrics_data,
        }
        
        handler = handlers.get(request.report_type)
        if not handler:
            raise ValueError(f"Unsupported report type: {request.report_type}")
        
        return handler(request)

    def _get_trial_balance_data(self, request: ReportRequest) -> Dict[str, Any]:
        """
        Generate trial balance data.
        Shows all accounts with debit/credit totals.
        """
        as_of = request.as_of_date or date.today()
        
        # Get all accounts for company
        accounts = self.session.query(Account).filter(
            Account.company_id == request.company_id,
            Account.deleted_at.is_(None)
        ).order_by(Account.code).all()
        
        rows = []
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        
        for account in accounts:
            # Calculate balance from journal lines
            debit_sum = self.session.query(
                func.coalesce(func.sum(JournalLine.debit), 0)
            ).join(JournalEntry).filter(
                JournalLine.account_id == account.id,
                JournalEntry.posted == True,
                JournalEntry.entry_date <= as_of
            ).scalar() or Decimal('0.00')
            
            credit_sum = self.session.query(
                func.coalesce(func.sum(JournalLine.credit), 0)
            ).join(JournalEntry).filter(
                JournalLine.account_id == account.id,
                JournalEntry.posted == True,
                JournalEntry.entry_date <= as_of
            ).scalar() or Decimal('0.00')
            
            if not request.include_zero_balances and debit_sum == credit_sum == Decimal('0.00'):
                continue
            
            rows.append({
                'account_code': account.code,
                'account_name_en': account.name_en,
                'account_name_ar': account.name_ar,
                'account_type': account.account_type,
                'debit': debit_sum,
                'credit': credit_sum
            })
            
            total_debits += debit_sum
            total_credits += credit_sum
        
        return {
            'title_en': 'Trial Balance',
            'title_ar': 'ميزان المراجعة',
            'as_of_date': as_of,
            'rows': rows,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'balanced': total_debits == total_credits
        }

    def _get_balance_sheet_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate balance sheet data (Assets = Liabilities + Equity)."""
        as_of = request.as_of_date or date.today()
        
        # Get accounts by type
        accounts = self.session.query(Account).filter(
            Account.company_id == request.company_id,
            Account.deleted_at.is_(None)
        ).all()
        
        assets = []
        liabilities = []
        equity = []
        
        for account in accounts:
            balance = self._calculate_account_balance(account.id, as_of)
            
            if balance == Decimal('0.00') and not request.include_zero_balances:
                continue
            
            account_data = {
                'code': account.code,
                'name_en': account.name_en,
                'name_ar': account.name_ar,
                'balance': balance
            }
            
            if account.account_type == 'ASSET':
                assets.append(account_data)
            elif account.account_type == 'LIABILITY':
                liabilities.append(account_data)
            elif account.account_type == 'EQUITY':
                equity.append(account_data)
        
        total_assets = sum(a['balance'] for a in assets)
        total_liabilities = sum(l['balance'] for l in liabilities)
        total_equity = sum(e['balance'] for e in equity)
        
        return {
            'title_en': 'Balance Sheet',
            'title_ar': 'الميزانية العمومية',
            'as_of_date': as_of,
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal('0.01')
        }

    def _get_income_statement_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate income statement (P&L) data."""
        date_from = request.date_from or date(date.today().year, 1, 1)
        date_to = request.date_to or date.today()
        
        accounts = self.session.query(Account).filter(
            Account.company_id == request.company_id,
            Account.deleted_at.is_(None),
            Account.account_type.in_(['REVENUE', 'EXPENSE'])
        ).all()
        
        revenue = []
        expenses = []
        
        for account in accounts:
            balance = self._calculate_account_balance(
                account.id, date_to, date_from
            )
            
            if balance == Decimal('0.00') and not request.include_zero_balances:
                continue
            
            account_data = {
                'code': account.code,
                'name_en': account.name_en,
                'name_ar': account.name_ar,
                'balance': balance
            }
            
            if account.account_type == 'REVENUE':
                revenue.append(account_data)
            else:
                expenses.append(account_data)
        
        total_revenue = sum(r['balance'] for r in revenue)
        total_expenses = sum(e['balance'] for e in expenses)
        net_income = total_revenue - total_expenses
        
        return {
            'title_en': 'Income Statement',
            'title_ar': 'قائمة الدخل',
            'date_from': date_from,
            'date_to': date_to,
            'revenue': revenue,
            'expenses': expenses,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income
        }

    def _get_sales_by_day_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate sales summary by day."""
        date_from = request.date_from or date.today()
        date_to = request.date_to or date.today()
        
        query = self.session.query(
            func.date(Sale.created_at).label('sale_date'),
            func.count(Sale.id).label('transaction_count'),
            func.sum(Sale.total_amount).label('total_sales'),
            func.sum(Sale.tax_total).label('total_tax')
        ).filter(
            Sale.company_id == request.company_id,
            func.date(Sale.created_at).between(date_from, date_to)
        )
        
        if request.branch_id:
            query = query.filter(Sale.branch_id == request.branch_id)
        
        results = query.group_by(func.date(Sale.created_at)).order_by('sale_date').all()
        
        rows = [
            {
                'date': r.sale_date,
                'transaction_count': r.transaction_count,
                'total_sales': r.total_sales or Decimal('0.00'),
                'total_tax': r.total_tax or Decimal('0.00')
            }
            for r in results
        ]
        
        return {
            'title_en': 'Sales by Day',
            'title_ar': 'المبيعات حسب اليوم',
            'date_from': date_from,
            'date_to': date_to,
            'rows': rows,
            'grand_total': sum(r['total_sales'] for r in rows)
        }

    def _get_sales_by_product_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate sales summary by product."""
        date_from = request.date_from or date.today()
        date_to = request.date_to or date.today()
        
        query = self.session.query(
            Product.sku,
            Product.name_en,
            Product.name_ar,
            func.sum(SaleLine.quantity).label('total_quantity'),
            func.sum(SaleLine.line_total).label('total_sales')
        ).join(SaleLine.product).join(SaleLine.sale).filter(
            Sale.company_id == request.company_id,
            func.date(Sale.created_at).between(date_from, date_to)
        )
        
        if request.branch_id:
            query = query.filter(Sale.branch_id == request.branch_id)
        
        results = query.group_by(
            Product.sku, Product.name_en, Product.name_ar
        ).order_by(func.sum(SaleLine.line_total).desc()).all()
        
        rows = [
            {
                'sku': r.sku,
                'product_name_en': r.name_en,
                'product_name_ar': r.name_ar,
                'quantity': r.total_quantity or Decimal('0.00'),
                'total_sales': r.total_sales or Decimal('0.00')
            }
            for r in results
        ]
        
        return {
            'title_en': 'Sales by Product',
            'title_ar': 'المبيعات حسب المنتج',
            'date_from': date_from,
            'date_to': date_to,
            'rows': rows,
            'grand_total': sum(r['total_sales'] for r in rows)
        }

    def _get_purchases_summary_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate purchases summary."""
        date_from = request.date_from or date.today()
        date_to = request.date_to or date.today()
        
        query = self.session.query(
            Supplier.name.label('supplier_name'),
            func.count(PurchaseInvoice.id).label('invoice_count'),
            func.sum(PurchaseInvoice.total_amount).label('total_amount'),
            func.sum(PurchaseInvoice.tax_total).label('total_tax')
        ).join(PurchaseInvoice.supplier).filter(
            PurchaseInvoice.company_id == request.company_id,
            PurchaseInvoice.invoice_date.between(date_from, date_to)
        )
        
        if request.branch_id:
            query = query.filter(PurchaseInvoice.branch_id == request.branch_id)
        
        results = query.group_by(Supplier.name).order_by(
            func.sum(PurchaseInvoice.total_amount).desc()
        ).all()
        
        rows = [
            {
                'supplier_name': r.supplier_name,
                'invoice_count': r.invoice_count,
                'total_amount': r.total_amount or Decimal('0.00'),
                'total_tax': r.total_tax or Decimal('0.00')
            }
            for r in results
        ]
        
        return {
            'title_en': 'Purchases Summary',
            'title_ar': 'ملخص المشتريات',
            'date_from': date_from,
            'date_to': date_to,
            'rows': rows,
            'grand_total': sum(r['total_amount'] for r in rows)
        }

    def _get_stock_movement_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate stock movement report."""
        date_from = request.date_from or date.today()
        date_to = request.date_to or date.today()
        
        query = self.session.query(StockMovement).join(
            StockMovement.product
        ).filter(
            Product.company_id == request.company_id,
            func.date(StockMovement.created_at).between(date_from, date_to)
        )
        
        if request.branch_id:
            query = query.filter(StockMovement.branch_id == request.branch_id)
        
        movements = query.order_by(StockMovement.created_at.desc()).all()
        
        rows = [
            {
                'date': m.created_at.date(),
                'product_sku': m.product.sku,
                'product_name_en': m.product.name_en,
                'product_name_ar': m.product.name_ar,
                'movement_type': m.movement_type,
                'quantity': m.quantity,
                'unit_cost': m.unit_cost,
                'total_cost': m.total_cost,
                'reference_type': m.reference_type,
                'reference_id': str(m.reference_id) if m.reference_id else None
            }
            for m in movements
        ]
        
        return {
            'title_en': 'Stock Movement',
            'title_ar': 'حركة المخزون',
            'date_from': date_from,
            'date_to': date_to,
            'rows': rows
        }

    def _get_inventory_valuation_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate inventory valuation report."""
        # Get current stock levels and costs
        products = self.session.query(Product).filter(
            Product.company_id == request.company_id,
            Product.deleted_at.is_(None)
        ).all()
        
        rows = []
        total_value = Decimal('0.00')
        
        for product in products:
            # Calculate current stock from movements
            in_qty = self.session.query(
                func.coalesce(func.sum(StockMovement.quantity), 0)
            ).filter(
                StockMovement.product_id == product.id,
                StockMovement.movement_type.in_(['IN', 'RETURN'])
            ).scalar() or Decimal('0.00')
            
            out_qty = self.session.query(
                func.coalesce(func.sum(StockMovement.quantity), 0)
            ).filter(
                StockMovement.product_id == product.id,
                StockMovement.movement_type.in_(['OUT', 'SALE', 'ADJUSTMENT'])
            ).scalar() or Decimal('0.00')
            
            current_qty = in_qty - out_qty
            
            if current_qty <= 0 and not request.include_zero_balances:
                continue
            
            # Get weighted average cost
            avg_cost = self.session.query(
                func.avg(StockMovement.unit_cost)
            ).filter(
                StockMovement.product_id == product.id,
                StockMovement.movement_type == 'IN'
            ).scalar() or Decimal('0.0000')
            
            value = current_qty * avg_cost
            total_value += value
            
            rows.append({
                'sku': product.sku,
                'product_name_en': product.name_en,
                'product_name_ar': product.name_ar,
                'quantity': current_qty,
                'avg_cost': avg_cost,
                'total_value': value
            })
        
        return {
            'title_en': 'Inventory Valuation',
            'title_ar': 'تقييم المخزون',
            'as_of_date': request.as_of_date or date.today(),
            'rows': rows,
            'total_value': total_value
        }

    def _get_supplier_ledger_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate supplier ledger (accounts payable)."""
        suppliers = self.session.query(Supplier).filter(
            Supplier.company_id == request.company_id,
            Supplier.deleted_at.is_(None)
        ).all()
        
        rows = []
        total_outstanding = Decimal('0.00')
        
        for supplier in suppliers:
            # Get total invoices
            total_invoiced = self.session.query(
                func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)
            ).filter(
                PurchaseInvoice.supplier_id == supplier.id,
                PurchaseInvoice.status.in_(['VERIFIED', 'POSTED'])
            ).scalar() or Decimal('0.00')
            
            # Get total payments (placeholder - would come from payment records)
            total_paid = Decimal('0.00')  # TODO: Implement payment tracking
            
            outstanding = total_invoiced - total_paid
            
            if outstanding == Decimal('0.00') and not request.include_zero_balances:
                continue
            
            rows.append({
                'supplier_name': supplier.name,
                'tax_id': supplier.tax_id,
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'outstanding': outstanding
            })
            
            total_outstanding += outstanding
        
        return {
            'title_en': 'Supplier Ledger',
            'title_ar': 'دفتر الموردين',
            'as_of_date': request.as_of_date or date.today(),
            'rows': rows,
            'total_outstanding': total_outstanding
        }

    def _get_dashboard_metrics_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate dashboard summary metrics."""
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        # Sales today
        sales_today = self.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).filter(
            Sale.company_id == request.company_id,
            func.date(Sale.created_at) == today
        ).scalar() or Decimal('0.00')
        
        # Sales this month
        sales_month = self.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).filter(
            Sale.company_id == request.company_id,
            func.date(Sale.created_at) >= month_start
        ).scalar() or Decimal('0.00')
        
        # AR outstanding (placeholder)
        ar_outstanding = Decimal('0.00')
        
        # AP outstanding
        ap_outstanding = self.session.query(
            func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)
        ).filter(
            PurchaseInvoice.company_id == request.company_id,
            PurchaseInvoice.status.in_(['VERIFIED', 'POSTED'])
        ).scalar() or Decimal('0.00')
        
        # Low stock count (products with qty < 10)
        low_stock_count = 0  # TODO: Implement proper low stock calculation
        
        # Pending approvals
        from models.purchases import ApprovalRequest
        pending_approvals = self.session.query(func.count(ApprovalRequest.id)).filter(
            ApprovalRequest.company_id == request.company_id,
            ApprovalRequest.status == 'PENDING'
        ).scalar() or 0
        
        # Cash balance (from cash accounts)
        cash_balance = Decimal('0.00')  # TODO: Calculate from cash accounts
        
        # Inventory value
        inventory_value = Decimal('0.00')  # TODO: Calculate from inventory valuation
        
        return {
            'title_en': 'Dashboard Metrics',
            'title_ar': 'مؤشرات لوحة التحكم',
            'sales_today': sales_today,
            'sales_this_month': sales_month,
            'ar_outstanding': ar_outstanding,
            'ap_outstanding': ap_outstanding,
            'low_stock_count': low_stock_count,
            'pending_approvals': pending_approvals,
            'cash_balance': cash_balance,
            'inventory_value': inventory_value
        }

    def _calculate_account_balance(
        self, 
        account_id: UUID, 
        as_of_date: date,
        from_date: Optional[date] = None
    ) -> Decimal:
        """Calculate account balance as of a date."""
        query = self.session.query(
            func.coalesce(func.sum(JournalLine.debit), 0).label('total_debit'),
            func.coalesce(func.sum(JournalLine.credit), 0).label('total_credit')
        ).join(JournalEntry).filter(
            JournalLine.account_id == account_id,
            JournalEntry.posted == True,
            JournalEntry.entry_date <= as_of_date
        )
        
        if from_date:
            query = query.filter(JournalEntry.entry_date >= from_date)
        
        result = query.first()
        
        if not result:
            return Decimal('0.00')
        
        return (result.total_debit - result.total_credit).quantize(Decimal('0.01'))

    def _generate_csv(self, report_type: ReportType, data: Dict[str, Any]) -> tuple[bytes, str]:
        """Generate CSV output for simple reports."""
        import csv
        import io
        
        output = io.StringIO()
        
        if 'rows' in data and data['rows']:
            writer = csv.DictWriter(output, fieldnames=data['rows'][0].keys())
            writer.writeheader()
            writer.writerows(data['rows'])
        
        content = output.getvalue().encode('utf-8-sig')  # BOM for Excel compatibility
        filename = f"{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return content, filename


def generate_report(session: Session, request: ReportRequest) -> ReportResult:
    """
    Convenience function to generate a report.
    
    Args:
        session: Database session
        request: Report request parameters
        
    Returns:
        ReportResult with file content
        
    Example:
        >>> from core.reporting import generate_report, ReportRequest, ReportType, ReportFormat
        >>> request = ReportRequest(
        ...     report_type=ReportType.TRIAL_BALANCE,
        ...     format=ReportFormat.EXCEL,
        ...     company_id=company_id,
        ...     as_of_date=date.today()
        ... )
        >>> result = generate_report(session, request)
        >>> with open(result.filename, 'wb') as f:
        ...     f.write(result.content)
    """
    generator = ReportGenerator(session)
    return generator.generate(request)

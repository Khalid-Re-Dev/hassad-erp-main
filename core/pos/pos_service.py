"""
POS Business Logic
Handles sales processing, totals calculation, and integration with inventory and accounting
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.pos import Sale, SaleLine, Payment, POSSettings, SaleStatus, PaymentMethod
from models.inventory import Product, StockMovement, MovementType
from core.pos.schemas import (
    POSCreateRequest,
    POSCreateResponse,
    POSReturnRequest,
    POSReturnResponse,
    TotalsBreakdown,
)
from core.pos.payment import validate_payments, calculate_change
from core.inventory.services import get_product_stock, record_stock_movement
from core.accounting.journal import create_journal_entry
from core.accounting.posting import post_journal_entry
from core.accounting.schemas import JournalLineSchema


class POSError(Exception):
    """Base exception for POS operations"""
    pass


class InsufficientStockError(POSError):
    """Raised when product stock is insufficient"""
    pass


class InvalidPaymentError(POSError):
    """Raised when payment validation fails"""
    pass


class POSConfigurationError(POSError):
    """Raised when POS settings are missing or invalid"""
    pass


def calculate_totals(
    lines: List[Dict],
    global_discount_percent: Optional[Decimal] = None,
    global_discount_amount: Optional[Decimal] = None
) -> Dict[str, Decimal]:
    """
    Calculate totals for a POS sale
    
    Args:
        lines: List of line items with quantity, unit_price, discount, tax_rate
        global_discount_percent: Optional global discount percentage
        global_discount_amount: Optional global discount amount
    
    Returns:
        Dictionary with subtotal, discount_total, tax_total, grand_total
    
    Example:
        >>> lines = [
        ...     {"quantity": Decimal("2"), "unit_price": Decimal("100"), 
        ...      "discount_percent": Decimal("10"), "tax_rate": Decimal("15")}
        ... ]
        >>> totals = calculate_totals(lines)
        >>> totals["grand_total"]
        Decimal('207.00')
    """
    subtotal = Decimal('0.00')
    line_discount_total = Decimal('0.00')
    
    # Calculate line totals
    for line in lines:
        qty = Decimal(str(line.get('quantity', 0)))
        price = Decimal(str(line.get('unit_price', 0)))
        discount_pct = Decimal(str(line.get('discount_percent', 0)))
        
        line_subtotal = qty * price
        line_discount = Decimal('0.00')
        
        if discount_pct > 0:
            line_discount = (line_subtotal * discount_pct / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        subtotal += line_subtotal
        line_discount_total += line_discount
    
    # Base on which the global discount applies: subtotal net of line discounts.
    # Global discount must NOT be applied to amounts already removed by line
    # discounts, otherwise it double-discounts the line-discounted portion.
    net_subtotal = subtotal - line_discount_total

    # Apply global discount
    global_discount = Decimal('0.00')
    if global_discount_percent:
        global_discount = (net_subtotal * global_discount_percent / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    elif global_discount_amount:
        global_discount = Decimal(str(global_discount_amount)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    tax_total = Decimal('0.00')
    
    for line in lines:
        qty = Decimal(str(line.get('quantity', 0)))
        price = Decimal(str(line.get('unit_price', 0)))
        discount_pct = Decimal(str(line.get('discount_percent', 0)))
        tax_rate = Decimal(str(line.get('tax_rate', 0)))
        
        line_subtotal = qty * price
        line_discount = Decimal('0.00')
        
        if discount_pct > 0:
            line_discount = (line_subtotal * discount_pct / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        line_after_discount = line_subtotal - line_discount
        
        # Apply proportional global discount. Allocate the global discount
        # across lines in proportion to each line's amount AFTER its own line
        # discount, relative to the net subtotal the global discount was based
        # on. Using net_subtotal (not the post-global-discount taxable amount)
        # as the denominator keeps the allocation consistent with how the
        # global discount was computed.
        if net_subtotal > 0:
            line_global_discount = (line_after_discount / net_subtotal * global_discount).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            line_global_discount = Decimal('0.00')
        
        line_taxable = line_after_discount - line_global_discount
        line_tax = (line_taxable * tax_rate / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        tax_total += line_tax
    
    discount_total = line_discount_total + global_discount
    grand_total = subtotal - discount_total + tax_total
    
    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'discount_total': discount_total.quantize(Decimal('0.01')),
        'tax_total': tax_total.quantize(Decimal('0.01')),
        'grand_total': grand_total.quantize(Decimal('0.01')),
    }


def _generate_invoice_number(session: Session, company_id: UUID) -> str:
    """Generate next invoice number for company"""
    # Get last invoice number
    last_sale = session.query(Sale).filter(
        Sale.company_id == company_id
    ).order_by(Sale.created_at.desc()).first()
    
    if last_sale and last_sale.invoice_no:
        # Extract number from format INV-YYYY-NNNNN
        try:
            parts = last_sale.invoice_no.split('-')
            if len(parts) == 3:
                last_num = int(parts[2])
                next_num = last_num + 1
            else:
                next_num = 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    year = datetime.now().year
    return f"INV-{year}-{next_num:05d}"


def create_pos_sale(
    session: Session,
    pos_request: POSCreateRequest,
    auto_post: bool = False
) -> POSCreateResponse:
    """
    Create a new POS sale with full integration
    
    Args:
        session: Database session
        pos_request: POS sale request data
        auto_post: If True, automatically post to accounting
    
    Returns:
        POSCreateResponse with sale details
    
    Raises:
        InsufficientStockError: If product stock is insufficient
        InvalidPaymentError: If payment validation fails
        POSConfigurationError: If POS settings are missing
    
    Process:
        1. Validate product availability
        2. Calculate totals and taxes
        3. Validate payments
        4. Create Sale and SaleLine records
        5. Create Payment records
        6. Update stock (if configured)
        7. Create journal entry (debit/credit)
        8. Post journal (if auto_post=True)
    """
    try:
        with session.begin_nested():
            # Load POS settings
            pos_settings = session.query(POSSettings).filter(
                POSSettings.branch_id == pos_request.branch_id
            ).first()
            
            if not pos_settings:
                raise POSConfigurationError(f"POS settings not found for branch {pos_request.branch_id}")
            
            # Override auto_post with settings if not explicitly provided
            if not auto_post:
                auto_post = pos_settings.auto_post_journal
            
            # Validate stock availability
            for line in pos_request.lines:
                stock_info = get_product_stock(
                    session,
                    line.product_id,
                    pos_request.branch_id
                )
                
                if stock_info['available_qty'] < line.quantity:
                    if not pos_settings.allow_negative_stock:
                        raise InsufficientStockError(
                            f"Insufficient stock for product {line.sku}. "
                            f"Available: {stock_info['available_qty']}, Required: {line.quantity}"
                        )
            
            # Calculate totals
            lines_dict = [line.model_dump() for line in pos_request.lines]
            totals = calculate_totals(
                lines_dict,
                pos_request.global_discount_percent,
                pos_request.global_discount_amount
            )
            
            # Validate payments
            total_paid = sum(tender.amount for tender in pos_request.tenders)
            if total_paid < totals['grand_total']:
                if not pos_settings.allow_partial_payment:
                    raise InvalidPaymentError(
                        f"Insufficient payment. Required: {totals['grand_total']}, Paid: {total_paid}"
                    )
            
            change_due = calculate_change(total_paid, totals['grand_total'])
            
            # Generate invoice number
            invoice_no = _generate_invoice_number(session, pos_request.company_id)
            
            # Create Sale record
            sale = Sale(
                id=uuid.uuid4(),
                company_id=pos_request.company_id,
                branch_id=pos_request.branch_id,
                invoice_no=invoice_no,
                invoice_date=datetime.now(timezone.utc),
                customer_id=pos_request.customer_id,
                customer_name=pos_request.customer_name,
                cashier_user_id=pos_request.cashier_user_id,
                subtotal=totals['subtotal'],
                discount_total=totals['discount_total'],
                tax_total=totals['tax_total'],
                grand_total=totals['grand_total'],
                global_discount_percent=pos_request.global_discount_percent,
                global_discount_amount=pos_request.global_discount_amount,
                status=SaleStatus.PENDING,
                notes=pos_request.notes,
            )
            session.add(sale)
            session.flush()
            
            # Create SaleLine records and update stock
            total_cogs = Decimal('0.00')
            
            for line in pos_request.lines:
                # Get product cost
                stock_info = get_product_stock(
                    session,
                    line.product_id,
                    pos_request.branch_id
                )
                unit_cost = stock_info['avg_cost']
                total_cost = (line.quantity * unit_cost).quantize(Decimal('0.01'))
                total_cogs += total_cost
                
                # Calculate line totals
                line_subtotal = line.quantity * line.unit_price
                line_discount = Decimal('0.00')
                
                if line.discount_percent:
                    line_discount = (line_subtotal * line.discount_percent / Decimal('100')).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                elif line.discount_amount:
                    line_discount = line.discount_amount
                
                line_after_discount = line_subtotal - line_discount
                line_tax = (line_after_discount * line.tax_rate / Decimal('100')).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                
                sale_line = SaleLine(
                    id=uuid.uuid4(),
                    sale_id=sale.id,
                    product_id=line.product_id,
                    sku=line.sku,
                    product_name=line.name,
                    batch_id=line.batch_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount_percent=line.discount_percent,
                    discount_amount=line_discount,
                    tax_rate=line.tax_rate,
                    tax_amount=line_tax,
                    line_total=line_after_discount,
                    unit_cost=unit_cost,
                    total_cost=total_cost,
                )
                session.add(sale_line)
                
                # Record stock movement (if configured)
                if pos_settings.auto_stock_deduct:
                    record_stock_movement(
                        session=session,
                        product_id=line.product_id,
                        branch_id=pos_request.branch_id,
                        movement_type=MovementType.SALE,
                        quantity=-line.quantity,  # Negative for outbound
                        unit_cost=unit_cost,
                        reference_type="SALE",
                        reference_id=sale.id,
                        batch_id=line.batch_id,
                    )
            
            # Create Payment records
            for tender in pos_request.tenders:
                # Determine account based on payment method
                if tender.method == PaymentMethod.CASH:
                    account_id = pos_settings.default_cash_account_id
                elif tender.method == PaymentMethod.CARD:
                    account_id = pos_settings.default_card_account_id
                elif tender.method == PaymentMethod.CREDIT:
                    account_id = pos_settings.default_receivable_account_id
                else:
                    account_id = None
                
                payment = Payment(
                    id=uuid.uuid4(),
                    sale_id=sale.id,
                    method=tender.method,
                    amount=tender.amount,
                    card_reference=tender.card_reference,
                    card_type=tender.card_type,
                    customer_id=tender.customer_id,
                    account_id=account_id,
                )
                session.add(payment)
            
            session.flush()
            
            # Create journal entry
            journal_lines = []
            
            # Debit: Cash/Bank/Receivable (payment accounts)
            for tender in pos_request.tenders:
                if tender.method == PaymentMethod.CASH:
                    account_id = pos_settings.default_cash_account_id
                elif tender.method == PaymentMethod.CARD:
                    account_id = pos_settings.default_card_account_id
                elif tender.method == PaymentMethod.CREDIT:
                    account_id = pos_settings.default_receivable_account_id
                else:
                    continue
                
                journal_lines.append(JournalLineSchema(
                    account_id=account_id,
                    debit=tender.amount,
                    credit=Decimal('0.00'),
                    description=f"Sale {invoice_no} - {tender.method.value} payment"
                ))
            
            # Credit: Revenue (net of VAT)
            net_revenue = totals['grand_total'] - totals['tax_total']
            journal_lines.append(JournalLineSchema(
                account_id=pos_settings.default_revenue_account_id,
                debit=Decimal('0.00'),
                credit=net_revenue,
                description=f"Sale {invoice_no} - Revenue"
            ))
            
            # Credit: VAT Payable
            if totals['tax_total'] > 0:
                journal_lines.append(JournalLineSchema(
                    account_id=pos_settings.default_vat_account_id,
                    debit=Decimal('0.00'),
                    credit=totals['tax_total'],
                    description=f"Sale {invoice_no} - VAT"
                ))
            
            # Debit: COGS, Credit: Inventory
            if total_cogs > 0:
                journal_lines.append(JournalLineSchema(
                    account_id=pos_settings.default_cogs_account_id,
                    debit=total_cogs,
                    credit=Decimal('0.00'),
                    description=f"Sale {invoice_no} - COGS"
                ))
                
                journal_lines.append(JournalLineSchema(
                    account_id=pos_settings.default_inventory_account_id,
                    debit=Decimal('0.00'),
                    credit=total_cogs,
                    description=f"Sale {invoice_no} - Inventory reduction"
                ))
            
            # Create journal entry
            journal_id = create_journal_entry(
                session=session,
                company_id=pos_request.company_id,
                branch_id=pos_request.branch_id,
                reference=f"SALE-{invoice_no}",
                lines=journal_lines,
                posted=False,
            )
            
            sale.journal_entry_id = journal_id
            
            # Post journal if auto_post enabled
            if auto_post:
                post_journal_entry(
                    session=session,
                    journal_id=journal_id,
                    posted_by_user_id=pos_request.cashier_user_id,
                )
                sale.status = SaleStatus.POSTED
                sale.posted_at = datetime.now(timezone.utc)
                sale.posted_by_user_id = pos_request.cashier_user_id
            
            session.flush()
            
            # Prepare response
            response = POSCreateResponse(
                sale_id=sale.id,
                invoice_no=sale.invoice_no,
                invoice_date=sale.invoice_date,
                totals=TotalsBreakdown(
                    subtotal=totals['subtotal'],
                    discount_total=totals['discount_total'],
                    tax_total=totals['tax_total'],
                    grand_total=totals['grand_total'],
                    total_paid=total_paid,
                    change_due=change_due,
                ),
                status=sale.status.value,
                journal_entry_id=journal_id,
            )
            
            session.commit()
            return response
            
    except Exception as e:
        session.rollback()
        raise POSError(f"Failed to create POS sale: {str(e)}") from e


def process_return(
    session: Session,
    return_request: POSReturnRequest
) -> POSReturnResponse:
    """
    Process a return/refund for a previous sale
    
    Creates a reverse sale transaction with negative quantities,
    reverses stock movements, and creates reverse journal entry
    
    Args:
        session: Database session
        return_request: Return request data
    
    Returns:
        POSReturnResponse with return details
    
    Raises:
        POSError: If return validation fails
    """
    try:
        with session.begin_nested():
            # Load original sale
            original_sale = session.query(Sale).filter(
                Sale.id == return_request.original_sale_id
            ).first()
            
            if not original_sale:
                raise POSError(f"Original sale {return_request.original_sale_id} not found")
            
            # Load POS settings
            pos_settings = session.query(POSSettings).filter(
                POSSettings.branch_id == return_request.branch_id
            ).first()
            
            if not pos_settings:
                raise POSConfigurationError(f"POS settings not found for branch {return_request.branch_id}")
            
            # Check return window
            if not pos_settings.allow_returns:
                raise POSError("Returns are not allowed for this branch")
            
            days_since_sale = (datetime.now(timezone.utc) - original_sale.invoice_date).days
            if days_since_sale > pos_settings.return_window_days:
                raise POSError(
                    f"Return window expired. Sale was {days_since_sale} days ago, "
                    f"allowed window is {pos_settings.return_window_days} days"
                )
            
            # Calculate return totals
            refund_total = Decimal('0.00')
            total_cogs_return = Decimal('0.00')
            
            # Generate return invoice number
            return_invoice_no = f"RET-{original_sale.invoice_no}"
            
            # Create return sale
            return_sale = Sale(
                id=uuid.uuid4(),
                company_id=original_sale.company_id,
                branch_id=return_request.branch_id,
                invoice_no=return_invoice_no,
                invoice_date=datetime.now(timezone.utc),
                customer_id=original_sale.customer_id,
                customer_name=original_sale.customer_name,
                cashier_user_id=return_request.cashier_user_id,
                original_sale_id=original_sale.id,
                is_return=True,
                status=SaleStatus.PENDING,
                notes=return_request.reason,
            )
            session.add(return_sale)
            session.flush()
            
            # Process return lines
            for return_line in return_request.lines_to_return:
                # Load original sale line
                original_line = session.query(SaleLine).filter(
                    SaleLine.id == return_line.sale_line_id
                ).first()
                
                if not original_line:
                    raise POSError(f"Sale line {return_line.sale_line_id} not found")
                
                if return_line.quantity_to_return > original_line.quantity:
                    raise POSError(
                        f"Cannot return more than original quantity. "
                        f"Original: {original_line.quantity}, Return: {return_line.quantity_to_return}"
                    )
                
                # Calculate return amounts (proportional)
                return_ratio = return_line.quantity_to_return / original_line.quantity
                return_line_total = (original_line.line_total * return_ratio).quantize(Decimal('0.01'))
                return_tax = (original_line.tax_amount * return_ratio).quantize(Decimal('0.01'))
                return_cost = (original_line.total_cost * return_ratio).quantize(Decimal('0.01'))
                
                refund_total += return_line_total + return_tax
                total_cogs_return += return_cost
                
                # Create return sale line (negative quantities)
                return_sale_line = SaleLine(
                    id=uuid.uuid4(),
                    sale_id=return_sale.id,
                    product_id=original_line.product_id,
                    sku=original_line.sku,
                    product_name=original_line.product_name,
                    batch_id=original_line.batch_id,
                    quantity=-return_line.quantity_to_return,  # Negative
                    unit_price=original_line.unit_price,
                    discount_percent=original_line.discount_percent,
                    discount_amount=(original_line.discount_amount * return_ratio).quantize(Decimal('0.01')),
                    tax_rate=original_line.tax_rate,
                    tax_amount=-return_tax,  # Negative
                    line_total=-return_line_total,  # Negative
                    unit_cost=original_line.unit_cost,
                    total_cost=-return_cost,  # Negative
                )
                session.add(return_sale_line)
                
                # Reverse stock movement (add stock back)
                record_stock_movement(
                    session=session,
                    product_id=original_line.product_id,
                    branch_id=return_request.branch_id,
                    movement_type=MovementType.RETURN,
                    quantity=return_line.quantity_to_return,  # Positive (adding back)
                    unit_cost=original_line.unit_cost,
                    reference_type="RETURN",
                    reference_id=return_sale.id,
                    batch_id=original_line.batch_id,
                )
            
            # Update return sale totals
            return_sale.subtotal = -refund_total
            return_sale.grand_total = -refund_total
            
            # Create refund payment records
            for tender in return_request.refund_tenders:
                payment = Payment(
                    id=uuid.uuid4(),
                    sale_id=return_sale.id,
                    method=tender.method,
                    amount=-tender.amount,  # Negative for refund
                    card_reference=tender.card_reference,
                    card_type=tender.card_type,
                    customer_id=tender.customer_id,
                )
                session.add(payment)
            
            session.flush()
            
            # Create reverse journal entry
            journal_lines = []
            
            # Credit: Cash/Bank/Receivable (refund)
            for tender in return_request.refund_tenders:
                if tender.method == PaymentMethod.CASH:
                    account_id = pos_settings.default_cash_account_id
                elif tender.method == PaymentMethod.CARD:
                    account_id = pos_settings.default_card_account_id
                elif tender.method == PaymentMethod.CREDIT:
                    account_id = pos_settings.default_receivable_account_id
                else:
                    continue
                
                journal_lines.append(JournalLineSchema(
                    account_id=account_id,
                    debit=Decimal('0.00'),
                    credit=tender.amount,
                    description=f"Return {return_invoice_no} - {tender.method.value} refund"
                ))
            
            # Debit: Revenue
            journal_lines.append(JournalLineSchema(
                account_id=pos_settings.default_revenue_account_id,
                debit=refund_total,
                credit=Decimal('0.00'),
                description=f"Return {return_invoice_no} - Revenue reversal"
            ))
            
            # Credit: COGS, Debit: Inventory
            if total_cogs_return > 0:
                journal_lines.append(JournalLineSchema(
                    account_id=pos_settings.default_cogs_account_id,
                    debit=Decimal('0.00'),
                    credit=total_cogs_return,
                    description=f"Return {return_invoice_no} - COGS reversal"
                ))
                
                journal_lines.append(JournalLineSchema(
                    account_id=pos_settings.default_inventory_account_id,
                    debit=total_cogs_return,
                    credit=Decimal('0.00'),
                    description=f"Return {return_invoice_no} - Inventory restoration"
                ))
            
            # Create journal entry
            journal_id = create_journal_entry(
                session=session,
                company_id=original_sale.company_id,
                branch_id=return_request.branch_id,
                reference=f"RETURN-{return_invoice_no}",
                lines=journal_lines,
                posted=pos_settings.auto_post_journal,
            )
            
            return_sale.journal_entry_id = journal_id
            
            # Post if auto_post enabled
            if pos_settings.auto_post_journal:
                post_journal_entry(
                    session=session,
                    journal_id=journal_id,
                    posted_by_user_id=return_request.cashier_user_id,
                )
                return_sale.status = SaleStatus.POSTED
                return_sale.posted_at = datetime.now(timezone.utc)
                return_sale.posted_by_user_id = return_request.cashier_user_id
            
            session.flush()
            
            # Prepare response
            response = POSReturnResponse(
                return_sale_id=return_sale.id,
                return_invoice_no=return_sale.invoice_no,
                original_invoice_no=original_sale.invoice_no,
                refund_total=refund_total,
                status=return_sale.status.value,
                journal_entry_id=journal_id,
            )
            
            session.commit()
            return response
            
    except Exception as e:
        session.rollback()
        raise POSError(f"Failed to process return: {str(e)}") from e


def get_sale_details(session: Session, sale_id: UUID) -> Dict:
    """
    Get complete sale details including lines and payments
    
    Args:
        session: Database session
        sale_id: Sale ID
    
    Returns:
        Dictionary with sale details
    """
    sale = session.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise POSError(f"Sale {sale_id} not found")
    
    return {
        'sale': sale,
        'lines': sale.lines,
        'payments': sale.payments,
        'journal_entry': sale.journal_entry,
    }

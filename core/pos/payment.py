"""
Payment Processing
Handles payment validation, multi-payment splits, and change calculation
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from core.pos.schemas import POSTender, PaymentMethodEnum


class PaymentValidationError(Exception):
    """Raised when payment validation fails"""
    pass


def validate_payments(
    tenders: List[POSTender],
    grand_total: Decimal,
    allow_partial: bool = False,
    allow_overpayment: bool = True
) -> bool:
    """
    Validate payment tenders against grand total
    
    Args:
        tenders: List of payment tenders
        grand_total: Total amount due
        allow_partial: Allow partial payments
        allow_overpayment: Allow overpayment (change)
    
    Returns:
        True if valid
    
    Raises:
        PaymentValidationError: If validation fails
    
    Example:
        >>> tenders = [POSTender(method=PaymentMethodEnum.CASH, amount=Decimal("100"))]
        >>> validate_payments(tenders, Decimal("95.50"))
        True
    """
    if not tenders:
        raise PaymentValidationError("At least one payment tender is required")
    
    total_paid = sum(tender.amount for tender in tenders)
    
    # Check for negative amounts
    for tender in tenders:
        if tender.amount <= 0:
            raise PaymentValidationError(f"Payment amount must be positive: {tender.amount}")
    
    # Check total paid vs grand total
    if total_paid < grand_total:
        if not allow_partial:
            raise PaymentValidationError(
                f"Insufficient payment. Required: {grand_total}, Paid: {total_paid}"
            )
    
    if total_paid > grand_total:
        if not allow_overpayment:
            raise PaymentValidationError(
                f"Overpayment not allowed. Required: {grand_total}, Paid: {total_paid}"
            )
    
    # Validate credit payments have customer_id
    for tender in tenders:
        if tender.method == PaymentMethodEnum.CREDIT and not tender.customer_id:
            raise PaymentValidationError("Customer ID required for credit payments")
    
    return True


def calculate_change(total_paid: Decimal, grand_total: Decimal) -> Decimal:
    """
    Calculate change due to customer
    
    Args:
        total_paid: Total amount paid
        grand_total: Total amount due
    
    Returns:
        Change amount (0 if no change due)
    
    Example:
        >>> calculate_change(Decimal("100"), Decimal("95.50"))
        Decimal('4.50')
    """
    change = (total_paid - grand_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return max(change, Decimal('0.00'))


def split_payment_by_method(tenders: List[POSTender]) -> dict:
    """
    Group payments by method for reporting
    
    Args:
        tenders: List of payment tenders
    
    Returns:
        Dictionary with totals by payment method
    
    Example:
        >>> tenders = [
        ...     POSTender(method=PaymentMethodEnum.CASH, amount=Decimal("50")),
        ...     POSTender(method=PaymentMethodEnum.CARD, amount=Decimal("50"))
        ... ]
        >>> split_payment_by_method(tenders)
        {'CASH': Decimal('50.00'), 'CARD': Decimal('50.00')}
    """
    totals = {}
    
    for tender in tenders:
        method = tender.method.value
        if method not in totals:
            totals[method] = Decimal('0.00')
        totals[method] += tender.amount
    
    return totals

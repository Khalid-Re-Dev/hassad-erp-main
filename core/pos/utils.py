"""
POS Utility Functions
Helper functions for formatting, rounding, and calculations
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def round_currency(amount: Decimal, places: int = 2) -> Decimal:
    """
    Round currency amount to specified decimal places
    
    Args:
        amount: Amount to round
        places: Number of decimal places (default 2)
    
    Returns:
        Rounded amount
    
    Example:
        >>> round_currency(Decimal("10.556"))
        Decimal('10.56')
    """
    quantizer = Decimal('0.1') ** places
    return amount.quantize(quantizer, rounding=ROUND_HALF_UP)


def format_currency(amount: Decimal, currency_symbol: str = "SAR") -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Amount to format
        currency_symbol: Currency symbol
    
    Returns:
        Formatted string
    
    Example:
        >>> format_currency(Decimal("1234.56"))
        '1,234.56 SAR'
    """
    formatted = f"{amount:,.2f}"
    return f"{formatted} {currency_symbol}"


def calculate_tax_inclusive(
    amount_with_tax: Decimal,
    tax_rate: Decimal
) -> tuple[Decimal, Decimal]:
    """
    Calculate base amount and tax from tax-inclusive price
    
    Args:
        amount_with_tax: Total amount including tax
        tax_rate: Tax rate percentage
    
    Returns:
        Tuple of (base_amount, tax_amount)
    
    Example:
        >>> calculate_tax_inclusive(Decimal("115.00"), Decimal("15.00"))
        (Decimal('100.00'), Decimal('15.00'))
    """
    divisor = Decimal('1') + (tax_rate / Decimal('100'))
    base_amount = (amount_with_tax / divisor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    tax_amount = (amount_with_tax - base_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return base_amount, tax_amount


def calculate_tax_exclusive(
    base_amount: Decimal,
    tax_rate: Decimal
) -> tuple[Decimal, Decimal]:
    """
    Calculate tax and total from tax-exclusive price
    
    Args:
        base_amount: Base amount before tax
        tax_rate: Tax rate percentage
    
    Returns:
        Tuple of (tax_amount, total_amount)
    
    Example:
        >>> calculate_tax_exclusive(Decimal("100.00"), Decimal("15.00"))
        (Decimal('15.00'), Decimal('115.00'))
    """
    tax_amount = (base_amount * tax_rate / Decimal('100')).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    total_amount = base_amount + tax_amount
    return tax_amount, total_amount


def generate_barcode_checksum(code: str) -> str:
    """
    Generate checksum digit for barcode (EAN-13, UPC-A)
    
    Args:
        code: Barcode without checksum (12 digits)
    
    Returns:
        Complete barcode with checksum
    
    Example:
        >>> generate_barcode_checksum("123456789012")
        '1234567890128'
    """
    if len(code) != 12:
        raise ValueError("Code must be 12 digits for EAN-13")
    
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    total = odd_sum + (even_sum * 3)
    checksum = (10 - (total % 10)) % 10
    
    return code + str(checksum)

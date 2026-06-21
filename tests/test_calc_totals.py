"""
Tests for POS totals calculation
"""
import pytest
from decimal import Decimal

from core.pos.pos_service import calculate_totals


def test_simple_totals_no_discount_no_tax():
    """Test simple totals calculation without discount or tax"""
    lines = [
        {
            'quantity': Decimal('2'),
            'unit_price': Decimal('100.00'),
            'discount_percent': Decimal('0'),
            'tax_rate': Decimal('0'),
        }
    ]
    
    totals = calculate_totals(lines)
    
    assert totals['subtotal'] == Decimal('200.00')
    assert totals['discount_total'] == Decimal('0.00')
    assert totals['tax_total'] == Decimal('0.00')
    assert totals['grand_total'] == Decimal('200.00')


def test_totals_with_line_discount():
    """Test totals with line-level discount"""
    lines = [
        {
            'quantity': Decimal('2'),
            'unit_price': Decimal('100.00'),
            'discount_percent': Decimal('10'),
            'tax_rate': Decimal('0'),
        }
    ]
    
    totals = calculate_totals(lines)
    
    assert totals['subtotal'] == Decimal('200.00')
    assert totals['discount_total'] == Decimal('20.00')
    assert totals['tax_total'] == Decimal('0.00')
    assert totals['grand_total'] == Decimal('180.00')


def test_totals_with_tax():
    """Test totals with tax calculation"""
    lines = [
        {
            'quantity': Decimal('1'),
            'unit_price': Decimal('100.00'),
            'discount_percent': Decimal('0'),
            'tax_rate': Decimal('15'),
        }
    ]
    
    totals = calculate_totals(lines)
    
    assert totals['subtotal'] == Decimal('100.00')
    assert totals['discount_total'] == Decimal('0.00')
    assert totals['tax_total'] == Decimal('15.00')
    assert totals['grand_total'] == Decimal('115.00')


def test_totals_with_global_discount_percent():
    """Test totals with global discount percentage"""
    lines = [
        {
            'quantity': Decimal('2'),
            'unit_price': Decimal('100.00'),
            'discount_percent': Decimal('0'),
            'tax_rate': Decimal('15'),
        }
    ]
    
    totals = calculate_totals(lines, global_discount_percent=Decimal('10'))
    
    assert totals['subtotal'] == Decimal('200.00')
    assert totals['discount_total'] == Decimal('20.00')
    assert totals['tax_total'] == Decimal('27.00')  # 15% of 180
    assert totals['grand_total'] == Decimal('207.00')


def test_totals_complex_scenario():
    """Test complex scenario with multiple lines, discounts, and tax"""
    lines = [
        {
            'quantity': Decimal('2'),
            'unit_price': Decimal('100.00'),
            'discount_percent': Decimal('10'),
            'tax_rate': Decimal('15'),
        },
        {
            'quantity': Decimal('1'),
            'unit_price': Decimal('50.00'),
            'discount_percent': Decimal('0'),
            'tax_rate': Decimal('15'),
        },
    ]
    
    totals = calculate_totals(lines, global_discount_percent=Decimal('5'))
    
    assert totals['subtotal'] == Decimal('250.00')
    # Line discount: 20.00, Global discount: 11.50 (5% of 230)
    assert totals['discount_total'] == Decimal('31.50')
    # Tax on 218.50 at 15%
    assert totals['tax_total'] == Decimal('32.78')
    assert totals['grand_total'] == Decimal('251.28')


def test_totals_rounding():
    """Test proper rounding to 2 decimal places"""
    lines = [
        {
            'quantity': Decimal('3'),
            'unit_price': Decimal('33.33'),
            'discount_percent': Decimal('0'),
            'tax_rate': Decimal('15'),
        }
    ]
    
    totals = calculate_totals(lines)
    
    # Should round properly
    assert totals['subtotal'] == Decimal('99.99')
    assert totals['tax_total'] == Decimal('15.00')
    assert totals['grand_total'] == Decimal('114.99')

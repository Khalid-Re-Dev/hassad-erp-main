"""
Tests for receipt rendering
"""
import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from core.pos.receipt import ReceiptRenderer
from models.pos import Sale, SaleLine, Payment, PaymentMethod


def test_render_text_receipt():
    """Test plain text receipt rendering"""
    renderer = ReceiptRenderer(paper_width="80mm")
    
    # Create mock sale
    sale = Sale(
        id=uuid4(),
        invoice_no="INV-2024-00001",
        invoice_date=datetime(2024, 1, 15, 10, 30),
        subtotal=Decimal('200.00'),
        discount_total=Decimal('10.00'),
        tax_total=Decimal('28.50'),
        grand_total=Decimal('218.50'),
    )
    
    lines = [
        SaleLine(
            product_name="Product A",
            quantity=Decimal('2.0000'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('10.00'),
            tax_rate=Decimal('15.00'),
            tax_amount=Decimal('27.00'),
            line_total=Decimal('190.00'),
        )
    ]
    
    payments = [
        Payment(
            method=PaymentMethod.CASH,
            amount=Decimal('220.00'),
        )
    ]
    
    company_info = {
        'name': 'Test Company',
        'address': '123 Test St',
        'tax_id': '123456789',
        'cashier_name': 'John Doe',
    }
    
    totals = {
        'subtotal': Decimal('200.00'),
        'discount_total': Decimal('10.00'),
        'tax_total': Decimal('28.50'),
        'grand_total': Decimal('218.50'),
        'change_due': Decimal('1.50'),
    }
    
    # Render receipt
    receipt_text = renderer.render_text_receipt(sale, lines, payments, company_info, totals)
    
    # Verify content
    assert "Test Company" in receipt_text
    assert "INV-2024-00001" in receipt_text
    assert "Product A" in receipt_text
    assert "218.50" in receipt_text
    assert "CASH" in receipt_text


def test_render_arabic_receipt_image():
    """Test Arabic receipt image rendering"""
    renderer = ReceiptRenderer(paper_width="80mm")
    
    sale = Sale(
        id=uuid4(),
        invoice_no="INV-2024-00001",
        invoice_date=datetime(2024, 1, 15, 10, 30),
        subtotal=Decimal('200.00'),
        discount_total=Decimal('0.00'),
        tax_total=Decimal('30.00'),
        grand_total=Decimal('230.00'),
    )
    
    lines = [
        SaleLine(
            product_name="منتج أ",
            quantity=Decimal('2.0000'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('0.00'),
            tax_rate=Decimal('15.00'),
            tax_amount=Decimal('30.00'),
            line_total=Decimal('200.00'),
        )
    ]
    
    payments = [
        Payment(
            method=PaymentMethod.CASH,
            amount=Decimal('230.00'),
        )
    ]
    
    company_info = {
        'name': 'Test Company',
        'name_ar': 'شركة اختبار',
        'address_ar': 'عنوان الاختبار',
        'tax_id': '123456789',
        'cashier_name': 'أحمد',
    }
    
    totals = {
        'subtotal': Decimal('200.00'),
        'discount_total': Decimal('0.00'),
        'tax_total': Decimal('30.00'),
        'grand_total': Decimal('230.00'),
        'change_due': Decimal('0.00'),
    }
    
    # Render receipt image
    image = renderer.render_arabic_receipt_image(sale, lines, payments, company_info, totals)
    
    # Verify image created
    assert image is not None
    assert image.width == renderer.pixel_width
    assert image.height > 0


def test_receipt_paper_widths():
    """Test different paper widths"""
    renderer_58 = ReceiptRenderer(paper_width="58mm")
    renderer_80 = ReceiptRenderer(paper_width="80mm")
    
    assert renderer_58.char_width == 32
    assert renderer_58.pixel_width == 384
    
    assert renderer_80.char_width == 48
    assert renderer_80.pixel_width == 576

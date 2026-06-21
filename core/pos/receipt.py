"""
Receipt Rendering and Printing
Handles ESC/POS receipt generation with Arabic RTL support
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from core.pos.schemas import POSCreateResponse
from models.pos import Sale, SaleLine, Payment


class ReceiptRenderer:
    """
    Renders receipts for printing with Arabic RTL support
    """
    
    def __init__(self, paper_width: str = "80mm"):
        """
        Initialize receipt renderer
        
        Args:
            paper_width: Paper width (58mm or 80mm)
        """
        self.paper_width = paper_width
        self.char_width = 48 if paper_width == "80mm" else 32
        self.pixel_width = 576 if paper_width == "80mm" else 384
    
    def render_text_receipt(
        self,
        sale: Sale,
        lines: List[SaleLine],
        payments: List[Payment],
        company_info: Dict,
        totals: Dict
    ) -> str:
        """
        Render receipt as plain text (ASCII)
        
        Args:
            sale: Sale record
            lines: Sale line items
            payments: Payment records
            company_info: Company information
            totals: Totals breakdown
        
        Returns:
            Plain text receipt
        """
        receipt_lines = []
        
        # Header
        receipt_lines.append(self._center_text(company_info.get('name', 'Company Name')))
        receipt_lines.append(self._center_text(company_info.get('address', '')))
        receipt_lines.append(self._center_text(f"Tax ID: {company_info.get('tax_id', 'N/A')}"))
        receipt_lines.append(self._separator())
        
        # Invoice info
        receipt_lines.append(f"Invoice: {sale.invoice_no}")
        receipt_lines.append(f"Date: {sale.invoice_date.strftime('%Y-%m-%d %H:%M')}")
        receipt_lines.append(f"Cashier: {company_info.get('cashier_name', 'N/A')}")
        receipt_lines.append(self._separator())
        
        # Items header
        receipt_lines.append(f"{'Item':<20} {'Qty':>6} {'Price':>10} {'Total':>10}")
        receipt_lines.append(self._separator())
        
        # Items
        for line in lines:
            receipt_lines.append(f"{line.product_name[:20]:<20}")
            receipt_lines.append(
                f"  {line.quantity:>6.2f} x {line.unit_price:>10.2f} = {line.line_total:>10.2f}"
            )
            if line.discount_amount > 0:
                receipt_lines.append(f"  Discount: -{line.discount_amount:.2f}")
            if line.tax_amount > 0:
                receipt_lines.append(f"  Tax ({line.tax_rate}%): {line.tax_amount:.2f}")
        
        receipt_lines.append(self._separator())
        
        # Totals
        receipt_lines.append(f"{'Subtotal:':<30} {totals['subtotal']:>16.2f}")
        if totals['discount_total'] > 0:
            receipt_lines.append(f"{'Discount:':<30} -{totals['discount_total']:>15.2f}")
        receipt_lines.append(f"{'Tax:':<30} {totals['tax_total']:>16.2f}")
        receipt_lines.append(self._separator())
        receipt_lines.append(f"{'TOTAL:':<30} {totals['grand_total']:>16.2f}")
        receipt_lines.append(self._separator())
        
        # Payments
        receipt_lines.append("Payments:")
        for payment in payments:
            receipt_lines.append(f"  {payment.method.value:<20} {payment.amount:>16.2f}")
        
        if totals.get('change_due', 0) > 0:
            receipt_lines.append(f"{'Change:':<30} {totals['change_due']:>16.2f}")
        
        receipt_lines.append(self._separator())
        
        # Footer
        receipt_lines.append(self._center_text("Thank you for your business!"))
        receipt_lines.append(self._center_text("Please come again"))
        
        return "\n".join(receipt_lines)
    
    def render_arabic_receipt_image(
        self,
        sale: Sale,
        lines: List[SaleLine],
        payments: List[Payment],
        company_info: Dict,
        totals: Dict
    ) -> Image.Image:
        """
        Render receipt as image with Arabic RTL support
        
        Uses PIL to render Arabic text correctly with proper shaping
        
        Args:
            sale: Sale record
            lines: Sale line items
            payments: Payment records
            company_info: Company information
            totals: Totals breakdown
        
        Returns:
            PIL Image object
        """
        # Create image
        img_height = 800  # Will be adjusted based on content
        img = Image.new('RGB', (self.pixel_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts (fallback to default if Arabic font not available)
        try:
            font_regular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            font_arabic = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font_regular = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_arabic = ImageFont.load_default()
        
        y_position = 10
        
        # Header (Arabic)
        company_name_ar = company_info.get('name_ar', company_info.get('name', 'اسم الشركة'))
        y_position = self._draw_centered_text(draw, company_name_ar, y_position, font_bold)
        
        address_ar = company_info.get('address_ar', company_info.get('address', ''))
        if address_ar:
            y_position = self._draw_centered_text(draw, address_ar, y_position, font_arabic)
        
        tax_id_text = f"الرقم الضريبي: {company_info.get('tax_id', 'غير متوفر')}"
        y_position = self._draw_centered_text(draw, tax_id_text, y_position, font_arabic)
        
        y_position = self._draw_separator(draw, y_position)
        
        # Invoice info (Arabic RTL)
        invoice_text = f"فاتورة: {sale.invoice_no}"
        y_position = self._draw_rtl_text(draw, invoice_text, y_position, font_arabic)
        
        date_text = f"التاريخ: {sale.invoice_date.strftime('%Y-%m-%d %H:%M')}"
        y_position = self._draw_rtl_text(draw, date_text, y_position, font_arabic)
        
        cashier_text = f"الكاشير: {company_info.get('cashier_name', 'غير متوفر')}"
        y_position = self._draw_rtl_text(draw, cashier_text, y_position, font_arabic)
        
        y_position = self._draw_separator(draw, y_position)
        
        # Items (Arabic)
        for line in lines:
            product_name = line.product_name
            y_position = self._draw_rtl_text(draw, product_name, y_position, font_arabic)
            
            item_detail = f"{line.quantity:.2f} × {line.unit_price:.2f} = {line.line_total:.2f}"
            y_position = self._draw_rtl_text(draw, item_detail, y_position + 5, font_regular)
            
            y_position += 10
        
        y_position = self._draw_separator(draw, y_position)
        
        # Totals (Arabic RTL)
        subtotal_text = f"المجموع الفرعي: {totals['subtotal']:.2f}"
        y_position = self._draw_rtl_text(draw, subtotal_text, y_position, font_arabic)
        
        if totals['discount_total'] > 0:
            discount_text = f"الخصم: -{totals['discount_total']:.2f}"
            y_position = self._draw_rtl_text(draw, discount_text, y_position, font_arabic)
        
        tax_text = f"الضريبة: {totals['tax_total']:.2f}"
        y_position = self._draw_rtl_text(draw, tax_text, y_position, font_arabic)
        
        y_position = self._draw_separator(draw, y_position)
        
        total_text = f"الإجمالي: {totals['grand_total']:.2f}"
        y_position = self._draw_rtl_text(draw, total_text, y_position, font_bold)
        
        y_position = self._draw_separator(draw, y_position)
        
        # Payments
        payments_header = "طرق الدفع:"
        y_position = self._draw_rtl_text(draw, payments_header, y_position, font_arabic)
        
        for payment in payments:
            payment_text = f"{payment.method.value}: {payment.amount:.2f}"
            y_position = self._draw_rtl_text(draw, payment_text, y_position, font_arabic)
        
        if totals.get('change_due', 0) > 0:
            change_text = f"الباقي: {totals['change_due']:.2f}"
            y_position = self._draw_rtl_text(draw, change_text, y_position, font_arabic)
        
        y_position = self._draw_separator(draw, y_position)
        
        # Footer
        footer_text = "شكراً لزيارتكم"
        y_position = self._draw_centered_text(draw, footer_text, y_position + 10, font_bold)
        
        # Crop image to actual content height
        img = img.crop((0, 0, self.pixel_width, y_position + 50))
        
        return img
    
    def _center_text(self, text: str) -> str:
        """Center text within character width"""
        padding = (self.char_width - len(text)) // 2
        return " " * padding + text
    
    def _separator(self) -> str:
        """Create separator line"""
        return "-" * self.char_width
    
    def _draw_centered_text(self, draw, text: str, y: int, font) -> int:
        """Draw centered text on image"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.pixel_width - text_width) // 2
        draw.text((x, y), text, fill='black', font=font)
        return y + bbox[3] - bbox[1] + 5
    
    def _draw_rtl_text(self, draw, text: str, y: int, font) -> int:
        """Draw RTL text on image (right-aligned)"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = self.pixel_width - text_width - 10  # Right-aligned with margin
        draw.text((x, y), text, fill='black', font=font)
        return y + bbox[3] - bbox[1] + 5
    
    def _draw_separator(self, draw, y: int) -> int:
        """Draw separator line on image"""
        draw.line([(10, y), (self.pixel_width - 10, y)], fill='black', width=1)
        return y + 10


def generate_receipt_pdf(
    sale: Sale,
    lines: List[SaleLine],
    payments: List[Payment],
    company_info: Dict,
    totals: Dict,
    output_path: str
) -> str:
    """
    Generate receipt as PDF with Arabic RTL support
    
    Placeholder for Phase 6 (Reporting)
    Uses WeasyPrint or similar library for PDF generation
    
    Args:
        sale: Sale record
        lines: Sale line items
        payments: Payment records
        company_info: Company information
        totals: Totals breakdown
        output_path: Output file path
    
    Returns:
        Path to generated PDF
    """
    # TODO: Implement PDF generation with WeasyPrint
    # This is a placeholder for Phase 6
    raise NotImplementedError("PDF receipt generation will be implemented in Phase 6")

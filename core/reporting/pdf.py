"""
PDF report generation with RTL Arabic support.
Uses WeasyPrint for modern CSS/RTL rendering.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from .schemas import ReportType


class PDFReportGenerator:
    """Generate PDF reports with RTL Arabic support using WeasyPrint."""

    def __init__(self):
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_decimal'] = self._format_decimal
        self.env.filters['format_date'] = self._format_date

    def generate(self, report_type: ReportType, data: Dict[str, Any], language: str) -> tuple[bytes, str]:
        """
        Generate PDF file for report.
        
        Args:
            report_type: Type of report
            data: Report data dictionary
            language: 'ar' or 'en'
            
        Returns:
            Tuple of (file_bytes, filename)
        """
        # Get template name
        template_name = f"{report_type.value}.html"
        
        # Try to load specific template, fall back to generic
        try:
            template = self.env.get_template(template_name)
        except:
            template = self.env.get_template('generic_report.html')
        
        # Render HTML
        html_content = template.render(
            data=data,
            language=language,
            report_type=report_type.value,
            generated_at=datetime.now()
        )
        
        # Convert to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        filename = f"{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return pdf_bytes, filename

    def _format_decimal(self, value: Decimal, places: int = 2) -> str:
        """Format decimal for display."""
        if isinstance(value, Decimal):
            return f"{value:,.{places}f}"
        return str(value)

    def _format_date(self, value) -> str:
        """Format date for display."""
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

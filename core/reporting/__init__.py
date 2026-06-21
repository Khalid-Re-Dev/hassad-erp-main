"""
Hassad ERP System - Reporting Module
Phase 6: Reporting, Backup, Sync & Packaging

This module provides comprehensive reporting capabilities with:
- Financial reports (Trial Balance, Balance Sheet, Income Statement)
- Operational reports (Sales, Purchases, Inventory)
- Excel and PDF export with Arabic RTL support
"""

from .reports import generate_report, ReportGenerator
from .schemas import ReportRequest, ReportResult, ReportType

__all__ = [
    'generate_report',
    'ReportGenerator',
    'ReportRequest',
    'ReportResult',
    'ReportType',
]

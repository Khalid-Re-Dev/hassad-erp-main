"""
Company Settings Management Window.

Provides company profile management, configuration settings, and business setup.

TODO: Business Logic Implementation
- Company profile editing (name, address, contact, tax info)
- Logo and branding management  
- Business settings and preferences
- Currency and localization settings
- Integration with other modules
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFormLayout, QLineEdit, QLabel, QTextEdit, QTabWidget
)

from ui.base_ui import ModuleWidget
from models import Company
from core.db_utils import session_scope
import uuid


class CompanyWindow(ModuleWidget):
    """
    Company settings management window.
    
    Features:
    - Company profile management
    - Business configuration
    - Logo and branding settings
    - Localization preferences
    
    TODO: Add comprehensive company management functionality
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Company Settings | إعدادات الشركة")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface."""
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Company Settings | إعدادات الشركة")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save Changes | حفظ التغييرات")
        save_btn.clicked.connect(self._save_company)
        header_layout.addWidget(save_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Tab widget for different settings sections
        self.tabs = QTabWidget()
        
        # Company Profile Tab
        profile_tab = QWidget()
        profile_layout = QFormLayout()
        
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Enter company name | أدخل اسم الشركة")
        profile_layout.addRow("Company Name | اسم الشركة:", self.company_name)
        
        self.company_address = QTextEdit()
        self.company_address.setPlaceholderText("Enter company address | أدخل عنوان الشركة")
        self.company_address.setMaximumHeight(100)
        profile_layout.addRow("Address | العنوان:", self.company_address)
        
        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("Enter phone number | أدخل رقم الهاتف")
        profile_layout.addRow("Phone | الهاتف:", self.company_phone)
        
        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("Enter email address | أدخل البريد الإلكتروني")
        profile_layout.addRow("Email | البريد الإلكتروني:", self.company_email)
        
        profile_tab.setLayout(profile_layout)
        self.tabs.addTab(profile_tab, "Profile | الملف الشخصي")
        
        # Business Settings Tab
        business_tab = QWidget()
        business_layout = QFormLayout()
        
        self.tax_number = QLineEdit()
        self.tax_number.setPlaceholderText("Enter tax registration number | أدخل رقم التسجيل الضريبي")
        business_layout.addRow("Tax Number | الرقم الضريبي:", self.tax_number)
        
        self.business_type = QLineEdit()
        self.business_type.setPlaceholderText("Enter business type | أدخل نوع النشاط")
        business_layout.addRow("Business Type | نوع النشاط:", self.business_type)
        
        business_tab.setLayout(business_layout)
        self.tabs.addTab(business_tab, "Business | الأعمال")
        
        self.main_layout.addWidget(self.tabs)
        
    def load_data(self, session: Session) -> None:
        """
        Load company data from database.
        
        Args:
            session: Database session
        """
        try:
            # Load company data (placeholder - assumes single company)
            company = session.query(Company).first()
            
            if company and hasattr(self, 'company_name'):
                # Safely get company attributes with fallbacks
                name = getattr(company, 'name', '') or getattr(company, 'company_name', '')
                address = getattr(company, 'address', '') or getattr(company, 'company_address', '')
                phone = getattr(company, 'phone', '') or getattr(company, 'phone_number', '')
                email = getattr(company, 'email', '') or getattr(company, 'email_address', '')
                
                self.company_name.setText(str(name))
                self.company_address.setPlainText(str(address))
                self.company_phone.setText(str(phone))
                self.company_email.setText(str(email))
                
                # Load business fields safely
                if hasattr(self, 'tax_number'):
                    tax_num = getattr(company, 'tax_number', '') or getattr(company, 'tax_id', '')
                    self.tax_number.setText(str(tax_num))
                    
                if hasattr(self, 'business_type'):
                    biz_type = getattr(company, 'business_type', '') or getattr(company, 'industry', '')
                    self.business_type.setText(str(biz_type))
                
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            error_msg = f"Failed to load company data | فشل تحميل بيانات الشركة\nError ID: {error_id}\nDetails: {str(e)}"
            self._show_error(error_msg)
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Company load error {error_id}: {e}")
            raise
    
    def _save_company(self):
        """Save company changes."""
        # TODO: Implement company data saving
        self._show_info(
            "Save Company functionality not yet implemented.\\n"
            "This will save company profile and settings to database.\\n\\n"
            "وظيفة حفظ الشركة لم يتم تنفيذها بعد.\\n"
            "ستقوم بحفظ ملف الشركة والإعدادات في قاعدة البيانات.",
            "Coming Soon | قريباً"
        )
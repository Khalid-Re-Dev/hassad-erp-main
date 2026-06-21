# GENERATED/UPDATED BY PHASE B RESUME: 2025-11-02T07:27:06Z
"""
Product Categories Window.

Provides product category management and hierarchy.

TODO: Business Logic Implementation
- Category creation and editing
- Category hierarchy management
- Product assignment to categories
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel
)

from ui.base_ui import ModuleWidget
from models import Category
from core.services import get_category_service, ValidationError
from core.db_utils import session_scope
import logging
import uuid


class CategoriesWindow(ModuleWidget):
    """
    Product Categories management window.
    
    Features:
    - Category management
    - Hierarchy visualization
    - Product categorization
    
    TODO: Add comprehensive categories functionality
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Product Categories | فئات المنتجات")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface."""
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Categories | الفئات")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search categories... | البحث في الفئات...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)
        
        # Action button
        add_btn = QPushButton("+ Add Category | + إضافة فئة")
        add_btn.clicked.connect(self._add_category)
        header_layout.addWidget(add_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name | الاسم", "Description | الوصف", "Products | المنتجات", "Status | الحالة"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.main_layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        view_btn = QPushButton("View | عرض")
        view_btn.clicked.connect(self._view_item)
        action_layout.addWidget(view_btn)
        
        self.main_layout.addLayout(action_layout)
        
    def load_data(self, session: Session) -> None:
        """
        Load categories data from database.
        
        Args:
            session: Database session
        """
        try:
            # Query Category model
            query = session.query(Category)
            
            # Apply search filter if applicable
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
            if search_term:
                # TODO: Add search filter based on model fields
                pass
            
            results = query.limit(100).all()
            
            if hasattr(self, 'table'):
                self.table.setRowCount(len(results))
                for row, item in enumerate(results):
                    # TODO: Populate table columns with actual data
                    self.table.setItem(row, 0, QTableWidgetItem(str(getattr(item, 'id', ''))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(getattr(item, 'name', 'N/A'))))
                    
        except Exception as e:
            self._show_error(f"Failed to load categories data: {str(e)}")
            raise
    
    def _add_category(self):
        """Add new category via service layer."""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get category name (English)
        name_en, ok1 = QInputDialog.getText(
            self,
            "Add Category | إضافة فئة",
            "Enter category name (English) | أدخل اسم الفئة (إنجليزي):"
        )
        if not ok1 or not name_en.strip():
            return
        
        # Get category name (Arabic)
        name_ar, ok2 = QInputDialog.getText(
            self,
            "Add Category | إضافة فئة",
            "Enter category name (Arabic) | أدخل اسم الفئة (عربي):"
        )
        
        # Get company_id from current user
        from core.session_manager import session_manager
        current_user = session_manager.get_active_user()
        
        data = {
            'name_en': name_en.strip(),
            'name_ar': name_ar.strip() if ok2 and name_ar else None,
            'description': None,
            'company_id': current_user.company_id if current_user else None,
            'is_active': True
        }
        
        service = get_category_service()
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "Category created successfully.\n\nتم إنشاء الفئة بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Category creation error {error_id}: {e}")
            self._show_error(
                f"Failed to create category | فشل إنشاء الفئة\nError ID: {error_id}\nDetails: {str(e)}",
                title="Error | خطأ"
            )
    
    def _display_validation_errors(self, errors: list) -> None:
        """Show bilingual validation errors to the user."""
        if not errors:
            return
        en_msgs = [f"- {e.get_message('en')} (field: {e.field})" for e in errors]
        ar_msgs = [f"- {e.get_message('ar')} (الحقل: {e.field})" for e in errors]
        message = (
            "Validation errors occurred:\n" + "\n".join(en_msgs) +
            "\n\nحدثت أخطاء في التحقق:\n" + "\n".join(ar_msgs)
        )
        self._show_error(message, title="Validation | التحقق")

    def _view_item(self):
        """View selected category."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select an item to view. | يرجى اختيار عنصر للعرض.")
            return
            
        self._show_info(
            "View Product Categories functionality not yet implemented.\\n"
            "This will show detailed information.\\n\\n"
            "وظيفة عرض الفئة لم يتم تنفيذها بعد.\\n"
            "ستعرض معلومات مفصلة.",
            "Coming Soon | قريباً"
        )

# GENERATED/UPDATED BY PHASE B RESUME: 2025-11-02T07:27:06Z
"""
Branch Management Window.

Provides CRUD operations for company branches and locations.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QTextEdit
)

from ui.base_ui import ModuleWidget
from models import Branch, Company
from core.services import get_branch_service, ValidationError
import logging
import uuid


class BranchDialog(QDialog):
    """Dialog for creating/editing branches."""
    
    def __init__(self, branch: Optional[Branch] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.branch = branch
        self.is_edit = branch is not None
        self._setup_ui()
        if self.is_edit:
            self._load_branch_data()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        self.setWindowTitle("Edit Branch | تعديل الفرع" if self.is_edit else "Create Branch | إنشاء فرع")
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # Branch Code
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Branch code | رمز الفرع")
        layout.addRow("Code | الرمز:", self.code_input)
        
        # Branch Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Branch name | اسم الفرع")
        layout.addRow("Name | الاسم:", self.name_input)
        
        # Address
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Branch address | عنوان الفرع")
        self.address_input.setMaximumHeight(80)
        layout.addRow("Address | العنوان:", self.address_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+966XXXXXXXXX")
        layout.addRow("Phone | الهاتف:", self.phone_input)
        
        # Active status
        self.active_checkbox = QCheckBox("Active | نشط")
        self.active_checkbox.setChecked(True)
        layout.addRow("Status | الحالة:", self.active_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save | حفظ")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel | إلغاء")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
    
    def _load_branch_data(self) -> None:
        """Load existing branch data into form."""
        if not self.branch:
            return
        
        self.code_input.setText(self.branch.code or "")
        self.name_input.setText(self.branch.name or "")
        self.address_input.setPlainText(self.branch.address or "")
        self.phone_input.setText(self.branch.phone or "")
        self.active_checkbox.setChecked(self.branch.is_active)
    
    def get_branch_data(self) -> dict:
        """Get branch data from form."""
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "address": self.address_input.toPlainText().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "is_active": self.active_checkbox.isChecked()
        }


class BranchesWindow(ModuleWidget):
    """Branch management window."""
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Branch Management | إدارة الفروع")
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Setup user interface."""
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Branches | الفروع")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search branches... | البحث في الفروع...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)
        
        # Add button
        add_btn = QPushButton("+ Add Branch | + إضافة فرع")
        add_btn.clicked.connect(self._add_branch)
        header_layout.addWidget(add_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Code | الرمز", "Name | الاسم", "Address | العنوان", "Phone | الهاتف", "Status | الحالة"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_branch)
        self.main_layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        edit_btn = QPushButton("Edit | تعديل")
        edit_btn.clicked.connect(self._edit_branch)
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete | حذف")
        delete_btn.clicked.connect(self._delete_branch)
        action_layout.addWidget(delete_btn)
        
        self.main_layout.addLayout(action_layout)
    
    def load_data(self, session: Session) -> None:
        """Load branches from database using provided session."""
        query = session.query(Branch)
        
        # Apply search filter
        search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if search_term:
            query = query.filter(
                (Branch.name.ilike(f"%{search_term}%")) |
                (Branch.code.ilike(f"%{search_term}%"))
            )
        
        branches = query.order_by(Branch.name).all()
        
        if hasattr(self, 'table'):
            self.table.setRowCount(len(branches))
            for row, branch in enumerate(branches):
                self.table.setItem(row, 0, QTableWidgetItem(branch.code or ""))
                self.table.setItem(row, 1, QTableWidgetItem(branch.name or ""))
                self.table.setItem(row, 2, QTableWidgetItem(branch.address or ""))
                self.table.setItem(row, 3, QTableWidgetItem(branch.phone or ""))
                self.table.setItem(row, 4, QTableWidgetItem("Active | نشط" if branch.is_active else "Inactive | غير نشط"))
                
                # Store branch ID in first column
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, branch.id)
    
    def _add_branch(self) -> None:
        """Show dialog to add new branch."""
        dialog = BranchDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_branch_data()
            self._save_branch(data)
    
    def _edit_branch(self) -> None:
        """Edit selected branch."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a branch to edit. | يرجى اختيار فرع للتعديل.")
            return
        
        branch_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        from core.database import SessionLocal
        with SessionLocal() as session:
            branch = session.query(Branch).filter(Branch.id == branch_id).first()
            if branch:
                dialog = BranchDialog(branch=branch, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_branch_data()
                    self._update_branch(branch_id, data)
    
    def _delete_branch(self) -> None:
        """Delete selected branch via service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a branch to delete. | يرجى اختيار فرع للحذف.")
            return
        
        branch_name = self.table.item(current_row, 1).text()
        if self._ask_confirmation(
            f"Are you sure you want to delete branch '{branch_name}'? | هل أنت متأكد من حذف الفرع '{branch_name}'?"
        ):
            branch_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            service = get_branch_service()
            from core.db_utils import session_scope
            
            try:
                with session_scope() as session:
                    success, errors = service.delete(session, branch_id)
                    
                    if not success or errors:
                        self._display_validation_errors(errors)
                        return
                    
                    self._show_info(
                        "Branch deleted successfully.\n\nتم حذف الفرع بنجاح.",
                        title="Success | نجاح"
                    )
                    self.refresh_view()
            except Exception as e:
                error_id = str(uuid.uuid4())[:8]
                logger = logging.getLogger(__name__)
                logger.exception(f"Branch deletion error {error_id}: {e}")
                self._show_error(
                    f"Failed to delete branch | فشل حذف الفرع\nError ID: {error_id}\nDetails: {str(e)}",
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
    
    def _save_branch(self, data: dict) -> None:
        """Save new branch to database via service layer."""
        service = get_branch_service()
        from core.db_utils import session_scope
        
        # Add company_id from current user
        if self.current_user:
            data['company_id'] = self.current_user.company_id
        
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "Branch created successfully.\n\nتم إنشاء الفرع بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Branch creation error {error_id}: {e}")
            self._show_error(
                f"Failed to create branch | فشل إنشاء الفرع\nError ID: {error_id}\nDetails: {str(e)}",
                title="Error | خطأ"
            )
    
    def _update_branch(self, branch_id, data: dict) -> None:
        """Update existing branch via service layer."""
        service = get_branch_service()
        from core.db_utils import session_scope
        
        try:
            with session_scope() as session:
                instance, errors = service.update(session, branch_id, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "Branch updated successfully.\n\nتم تحديث الفرع بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Branch update error {error_id}: {e}")
            self._show_error(
                f"Failed to update branch | فشل تحديث الفرع\nError ID: {error_id}\nDetails: {str(e)}",
                title="Error | خطأ"
            )

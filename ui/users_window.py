"""User Management Window.

Provides CRUD operations for system users.

Phase F2.3 - Modernized with layout components and animations.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QComboBox, QCheckBox, QGroupBox
)
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.session_manager import session_manager
from ui.base_ui import ModuleMainWindow
from models import User, Role, Branch, Company
from core.services import get_user_service, ValidationError
from core.db_utils import session_scope
from ui.layout_components import Card, Toolbar, FilterBar, DataHeader, FormSection, Spacing
from ui.animations import fade_in, sequential_card_reveal, AnimationDuration
import logging
import uuid


class UserDialog(QDialog):
    """Dialog for creating/editing users."""
    
    def __init__(self, user: Optional[User] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user = user
        self.is_edit = user is not None
        self._setup_ui()
        if self.is_edit:
            self._load_user_data()
    
    def _setup_ui(self) -> None:
        """Setup modern sectioned dialog UI."""
        self.setWindowTitle(
            "Edit User | تعديل المستخدم" if self.is_edit 
            else "Create User | إنشاء مستخدم"
        )
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(Spacing.MEDIUM.value)
        
        # Section 1: Basic Information
        basic_card = Card("Basic Information | المعلومات الأساسية", collapsible=True)
        basic_form = FormSection(columns=2)
        
        self.username_input = QLineEdit()
        self.username_input.setEnabled(not self.is_edit)  # Cannot change username
        basic_form.add_field("Username | اسم المستخدم *", self.username_input)
        
        self.fullname_input = QLineEdit()
        basic_form.add_field("Full Name | الاسم الكامل *", self.fullname_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        basic_form.add_field("Email | البريد الإلكتروني", self.email_input)
        
        if not self.is_edit:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            basic_form.add_field("Password | كلمة المرور *", self.password_input)
        
        basic_card.add_widget(basic_form)
        main_layout.addWidget(basic_card)
        
        # Section 2: Organization
        org_card = Card("Organization | المنظمة", collapsible=True)
        org_form = FormSection(columns=2)
        
        self.company_combo = QComboBox()
        self._load_companies()
        self.company_combo.currentIndexChanged.connect(self._load_branches)
        org_form.add_field("Company | الشركة *", self.company_combo)
        
        self.branch_combo = QComboBox()
        org_form.add_field("Branch | الفرع", self.branch_combo)
        
        org_card.add_widget(org_form)
        main_layout.addWidget(org_card)
        
        # Section 3: Roles & Permissions
        roles_card = Card("Roles & Permissions | الأدوار والصلاحيات", collapsible=True)
        self.role_checkboxes = {}
        roles_container = QWidget()
        roles_layout = QVBoxLayout(roles_container)
        roles_layout.setSpacing(Spacing.SMALL.value)
        self._load_roles(roles_layout)
        roles_card.add_widget(roles_container)
        main_layout.addWidget(roles_card)
        
        # Section 4: Status
        status_card = Card("Status | الحالة")
        status_layout = QHBoxLayout()
        self.active_checkbox = QCheckBox("Active | نشط")
        self.active_checkbox.setChecked(True)
        status_layout.addWidget(self.active_checkbox)
        status_layout.addStretch()
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        status_card.add_widget(status_widget)
        main_layout.addWidget(status_card)
        
        main_layout.addStretch()
        
        # Action Buttons
        self._create_action_buttons(main_layout)
        
        # Animate card reveal
        cards = [basic_card, org_card, roles_card, status_card]
        QTimer.singleShot(50, lambda: sequential_card_reveal(cards, delay_between=50, animation_duration=150))
    
    def _create_action_buttons(self, layout):
        """Create action button row."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SMALL.value)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel | إلغاء")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save | حفظ")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_companies(self) -> None:
        """Load companies into combo box."""
        db = SessionLocal()
        try:
            companies = db.query(Company).filter(Company.is_active == True).all()
            for company in companies:
                self.company_combo.addItem(company.name, company.id)
        finally:
            db.close()
    
    def _load_branches(self) -> None:
        """Load branches for selected company."""
        self.branch_combo.clear()
        company_id = self.company_combo.currentData()
        if not company_id:
            return
        
        db = SessionLocal()
        try:
            branches = db.query(Branch).filter(
                Branch.company_id == company_id,
                Branch.is_active == True
            ).all()
            for branch in branches:
                self.branch_combo.addItem(branch.name, branch.id)
        finally:
            db.close()
    
    def _load_roles(self, layout: QVBoxLayout) -> None:
        """Load available roles as checkboxes."""
        db = SessionLocal()
        try:
            roles = db.query(Role).filter(Role.is_active == True).all()
            for role in roles:
                checkbox = QCheckBox(role.name)
                self.role_checkboxes[role.id] = checkbox
                layout.addWidget(checkbox)
        finally:
            db.close()
    
    def _load_user_data(self) -> None:
        """Load existing user data into form."""
        if not self.user:
            return
        
        self.username_input.setText(self.user.username)
        self.fullname_input.setText(self.user.full_name or "")
        self.email_input.setText(self.user.email or "")
        self.active_checkbox.setChecked(self.user.is_active)
        
        # Set company
        for i in range(self.company_combo.count()):
            if self.company_combo.itemData(i) == self.user.company_id:
                self.company_combo.setCurrentIndex(i)
                break
        
        # Set branch
        if self.user.branch_id:
            for i in range(self.branch_combo.count()):
                if self.branch_combo.itemData(i) == self.user.branch_id:
                    self.branch_combo.setCurrentIndex(i)
                    break
        
        # Set roles
        for role in self.user.roles:
            if role.id in self.role_checkboxes:
                self.role_checkboxes[role.id].setChecked(True)
    
    def get_user_data(self) -> dict:
        """Get user data from form."""
        selected_roles = [
            role_id for role_id, checkbox in self.role_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        data = {
            "username": self.username_input.text().strip(),
            "full_name": self.fullname_input.text().strip(),
            "email": self.email_input.text().strip(),
            "company_id": self.company_combo.currentData(),
            "branch_id": self.branch_combo.currentData(),
            "role_ids": selected_roles,
            "is_active": self.active_checkbox.isChecked()
        }
        
        if not self.is_edit:
            data["password"] = self.password_input.text()
        
        return data


class UsersWindow(ModuleMainWindow):
    """User management window."""
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self._setup_ui()
        # Load data using the ModuleUI refresh_view method
        self.refresh_view()
    
    def _setup_ui(self) -> None:
        """Setup modern user interface with components."""
        self.setWindowTitle("User Management | إدارة المستخدمين")
        self.setMinimumSize(1200, 700)
        
        # Page Header
        header = DataHeader(
            title="User Management | إدارة المستخدمين",
            subtitle="0 users | 0 مستخدم"
        )
        self.main_layout.addWidget(header)
        
        # Main Content Card
        main_card = Card()
        
        # Toolbar
        toolbar = Toolbar()
        toolbar.add_action("Add User | إضافة مستخدم", self._add_user, primary=True)
        toolbar.add_action("Edit | تعديل", self._edit_user)
        toolbar.add_action("Delete | حذف", self._delete_user, danger=True)
        toolbar.add_separator()
        toolbar.add_spacer()
        toolbar.add_action("Refresh | تحديث", self.refresh_view)
        main_card.add_widget(toolbar)
        
        # Filter Bar
        filter_bar = FilterBar("Search users... | بحث عن المستخدمين...")
        filter_bar.search_changed.connect(self._on_search)
        filter_bar.add_filter(
            "Status | الحالة",
            ["All | الكل", "Active | نشط", "Inactive | غير نشط"],
            self._on_status_filter
        )
        main_card.add_widget(filter_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Username | اسم المستخدم",
            "Full Name | الاسم الكامل",
            "Email | البريد",
            "Company | الشركة",
            "Branch | الفرع",
            "Roles | الأدوار",
            "Status | الحالة"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_user)
        main_card.add_widget(self.table)
        
        self.main_layout.addWidget(main_card)
        
        # Store references for updates
        self.header = header
        self.main_card = main_card
        self.filter_bar = filter_bar
        self.search_input = filter_bar.search_field  # Maintain compatibility
        self._status_filter = "All"
        
        # Apply fade-in animation
        QTimer.singleShot(50, lambda: fade_in(main_card, duration=AnimationDuration.NORMAL.value))
    
    def _on_search(self, text: str):
        """Handle search text changes."""
        self.refresh_view()
    
    def _on_status_filter(self, label: str, value: str):
        """Handle status filter changes."""
        self._status_filter = value
        self.refresh_view()
    
    def load_data(self, session: Session) -> None:
        """Load users from database using provided session."""
        query = session.query(User)
        
        # Apply search filter
        search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if search_term:
            query = query.filter(
                (User.username.ilike(f"%{search_term}%")) |
                (User.first_name.ilike(f"%{search_term}%")) |
                (User.last_name.ilike(f"%{search_term}%")) |
                (User.email.ilike(f"%{search_term}%"))
            )
        
        # Apply status filter
        if hasattr(self, '_status_filter') and self._status_filter != "All" and "All" not in self._status_filter:
            if "Active" in self._status_filter or "نشط" in self._status_filter:
                query = query.filter(User.is_active == True)
            elif "Inactive" in self._status_filter or "غير نشط" in self._status_filter:
                query = query.filter(User.is_active == False)
        
        users = query.order_by(User.username).all()
        
        if hasattr(self, 'table'):
            self.table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(user.username))
                self.table.setItem(row, 1, QTableWidgetItem(user.full_name or ""))
                self.table.setItem(row, 2, QTableWidgetItem(user.email or ""))
                # Safely access related objects
                company_name = ""
                branch_name = ""
                try:
                    company_name = user.company.name if user.company else ""
                    branch_name = user.branch.name if user.branch else ""
                except:
                    pass
                self.table.setItem(row, 3, QTableWidgetItem(company_name))
                self.table.setItem(row, 4, QTableWidgetItem(branch_name))
                self.table.setItem(row, 5, QTableWidgetItem(", ".join([r.name for r in user.roles])))
                self.table.setItem(row, 6, QTableWidgetItem("Active | نشط" if user.is_active else "Inactive | غير نشط"))
                
                # Store user ID in first column
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user.id)
            
            # Update header count
            if hasattr(self, 'header'):
                self.header.set_count(len(users), "users | مستخدمين")
    
    def _add_user(self) -> None:
        """Show dialog to add new user."""
        dialog = UserDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_user_data()
            self._save_user(data)
    
    def _edit_user(self) -> None:
        """Edit selected user."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user to edit.")
            return
        
        user_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                dialog = UserDialog(user=user, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_user_data()
                    self._update_user(user_id, data)
        finally:
            db.close()
    
    def _delete_user(self) -> None:
        """Delete selected user via service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user to delete. | يرجى اختيار مستخدم للحذف.")
            return
        
        username = self.table.item(current_row, 0).text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete | تأكيد الحذف",
            f"Are you sure you want to delete user '{username}'?\n\nهل أنت متأكد من حذف المستخدم '{username}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            user_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            service = get_user_service()
            
            try:
                with session_scope() as session:
                    success, errors = service.delete(session, user_id)
                    
                    if not success or errors:
                        self._display_validation_errors(errors)
                        return
                    
                    QMessageBox.information(
                        self, 
                        "Success | نجاح", 
                        "User deleted successfully.\n\nتم حذف المستخدم بنجاح."
                    )
                    self.refresh_view()
            except Exception as e:
                error_id = str(uuid.uuid4())[:8]
                logger = logging.getLogger(__name__)
                logger.exception(f"User deletion error {error_id}: {e}")
                QMessageBox.critical(
                    self, 
                    "Error | خطأ", 
                    f"Failed to delete user | فشل حذف المستخدم\nError ID: {error_id}\nDetails: {str(e)}"
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
        QMessageBox.critical(self, "Validation | التحقق", message)
    
    def _save_user(self, data: dict) -> None:
        """Save new user to database via service layer."""
        service = get_user_service()
        
        # Split full_name into first_name and last_name
        full_name = data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        data['first_name'] = name_parts[0] if name_parts else ''
        data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        data.pop('full_name', None)
        
        # Extract role_ids for separate handling
        role_ids = data.pop('role_ids', [])
        
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                # Assign roles if provided
                if role_ids and instance:
                    roles = session.query(Role).filter(Role.id.in_(role_ids)).all()
                    instance.roles = roles
                    session.flush()
                
                QMessageBox.information(
                    self, 
                    "Success | نجاح", 
                    "User created successfully.\n\nتم إنشاء المستخدم بنجاح."
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"User creation error {error_id}: {e}")
            QMessageBox.critical(
                self, 
                "Error | خطأ", 
                f"Failed to create user | فشل إنشاء المستخدم\nError ID: {error_id}\nDetails: {str(e)}"
            )
    
    def _update_user(self, user_id, data: dict) -> None:
        """Update existing user via service layer."""
        service = get_user_service()
        
        # Split full_name into first_name and last_name
        full_name = data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        data['first_name'] = name_parts[0] if name_parts else ''
        data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        data.pop('full_name', None)
        
        # Extract role_ids for separate handling
        role_ids = data.pop('role_ids', [])
        
        try:
            with session_scope() as session:
                instance, errors = service.update(session, user_id, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                # Update roles if provided
                if instance:
                    roles = session.query(Role).filter(Role.id.in_(role_ids)).all()
                    instance.roles = roles
                    session.flush()
                
                QMessageBox.information(
                    self, 
                    "Success | نجاح", 
                    "User updated successfully.\n\nتم تحديث المستخدم بنجاح."
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"User update error {error_id}: {e}")
            QMessageBox.critical(
                self, 
                "Error | خطأ", 
                f"Failed to update user | فشل تحديث المستخدم\nError ID: {error_id}\nDetails: {str(e)}"
            )

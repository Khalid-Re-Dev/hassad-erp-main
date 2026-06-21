"""
Roles & Permissions Management Window.

Provides CRUD operations for user roles and permission assignments.

TODO: Business Logic Implementation
- Add role creation with permission assignment
- Implement role editing and permission updates
- Add user role assignment interface
- Implement role hierarchy management
- Add audit logging for role changes
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem
)

from ui.base_ui import ModuleWidget
from models import Role, Permission
from core.db_utils import session_scope
from core.services import get_role_service, ValidationError
import logging
import uuid
from PyQt6.QtWidgets import QDialog, QFormLayout, QCheckBox


class RolesWindow(ModuleWidget):
    """
    Roles & Permissions management window.
    
    Features:
    - Role management (create, edit, delete)
    - Permission assignment to roles  
    - User role assignment
    - Permission hierarchy visualization
    
    TODO: Add comprehensive role management functionality
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Roles & Permissions | الأدوار والصلاحيات")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface."""
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Roles & Permissions Management | إدارة الأدوار والصلاحيات")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search roles... | البحث في الأدوار...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)
        
        # Add role button
        add_btn = QPushButton("+ Add Role | + إضافة دور")
        add_btn.clicked.connect(self._add_role)
        header_layout.addWidget(add_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Main content - splitter with roles and permissions
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Roles table
        roles_widget = QWidget()
        roles_layout = QVBoxLayout()
        
        roles_label = QLabel("Roles | الأدوار")
        roles_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        roles_layout.addWidget(roles_label)
        
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels([
            "Role Name | اسم الدور", 
            "Code | الرمز", 
            "Users | المستخدمين", 
            "Status | الحالة"
        ])
        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.roles_table.itemSelectionChanged.connect(self._role_selected)
        roles_layout.addWidget(self.roles_table)
        
        # Role action buttons
        role_actions = QHBoxLayout()
        role_actions.addStretch()
        
        edit_role_btn = QPushButton("Edit Role | تعديل الدور")
        edit_role_btn.clicked.connect(self._edit_role)
        role_actions.addWidget(edit_role_btn)
        
        delete_role_btn = QPushButton("Delete Role | حذف الدور")
        delete_role_btn.clicked.connect(self._delete_role)
        role_actions.addWidget(delete_role_btn)
        
        roles_layout.addLayout(role_actions)
        roles_widget.setLayout(roles_layout)
        splitter.addWidget(roles_widget)
        
        # Right panel - Permissions tree
        permissions_widget = QWidget()
        permissions_layout = QVBoxLayout()
        
        permissions_label = QLabel("Permissions | الصلاحيات")
        permissions_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        permissions_layout.addWidget(permissions_label)
        
        self.permissions_tree = QTreeWidget()
        self.permissions_tree.setHeaderLabels(["Permission | الصلاحية", "Description | الوصف"])
        permissions_layout.addWidget(self.permissions_tree)
        
        # Permission action buttons
        perm_actions = QHBoxLayout()
        perm_actions.addStretch()
        
        assign_perm_btn = QPushButton("Assign Permission | تعيين صلاحية")
        assign_perm_btn.clicked.connect(self._assign_permission)
        perm_actions.addWidget(assign_perm_btn)
        
        revoke_perm_btn = QPushButton("Revoke Permission | إلغاء صلاحية")
        revoke_perm_btn.clicked.connect(self._revoke_permission)
        perm_actions.addWidget(revoke_perm_btn)
        
        permissions_layout.addLayout(perm_actions)
        permissions_widget.setLayout(permissions_layout)
        splitter.addWidget(permissions_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        self.main_layout.addWidget(splitter)
        
    def load_data(self, session: Session) -> None:
        """
        Load roles and permissions from database.
        
        Args:
            session: Database session
        """
        try:
            # Load roles
            query = session.query(Role)
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
            if search_term:
                query = query.filter(
                    (Role.name.ilike(f"%{search_term}%")) |
                    (Role.code.ilike(f"%{search_term}%"))
                )
            
            roles = query.order_by(Role.name).all()
            
            if hasattr(self, 'roles_table'):
                self.roles_table.setRowCount(len(roles))
                for row, role in enumerate(roles):
                    # Safely get role attributes with fallbacks
                    role_name = getattr(role, 'name', f'Role #{getattr(role, "id", row+1)}')
                    role_code = getattr(role, 'code', getattr(role, 'role_code', f'R{row+1}'))
                    
                    self.roles_table.setItem(row, 0, QTableWidgetItem(str(role_name)))
                    self.roles_table.setItem(row, 1, QTableWidgetItem(str(role_code)))
                    # Count users with this role (safe)
                    user_count = len(getattr(role, 'users', [])) if hasattr(role, 'users') and getattr(role, 'users', None) else 0
                    self.roles_table.setItem(row, 2, QTableWidgetItem(str(user_count)))
                    
                    # Handle different possible active status attribute names
                    is_active = getattr(role, 'is_active', None)
                    if is_active is None:
                        is_active = getattr(role, 'active', True)  # Default to active
                    status_text = "Active | نشط" if is_active else "Inactive | غير نشط"
                    self.roles_table.setItem(row, 3, QTableWidgetItem(status_text))
                    
                    # Store role ID in first column
                    self.roles_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, role.id)
            
            # Load permissions into tree
            self._load_permissions_tree(session)
            
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            error_msg = f"Failed to load roles data | فشل تحميل بيانات الأدوار\nError ID: {error_id}\nDetails: {str(e)}"
            self._show_error(error_msg)
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Roles load error {error_id}: {e}")
            raise
    
    def _load_permissions_tree(self, session: Session):
        """Load permissions into tree structure."""
        try:
            if not hasattr(self, 'permissions_tree'):
                return
                
            self.permissions_tree.clear()
            
            # Get all permissions grouped by module
            permissions = session.query(Permission).order_by(Permission.module, Permission.name).all()
            
            modules = {}
            for permission in permissions:
                if permission.module not in modules:
                    # Create module parent item
                    module_item = QTreeWidgetItem([
                        f"{permission.module.title()} Module | وحدة {permission.module}",
                        f"All {permission.module} operations | جميع عمليات {permission.module}"
                    ])
                    modules[permission.module] = module_item
                    self.permissions_tree.addTopLevelItem(module_item)
                
                # Add permission as child
                perm_item = QTreeWidgetItem([
                    f"{permission.name} | {permission.code}",
                    permission.description or "No description | لا يوجد وصف"
                ])
                perm_item.setData(0, Qt.ItemDataRole.UserRole, permission.id)
                modules[permission.module].addChild(perm_item)
            
            # Expand all modules
            self.permissions_tree.expandAll()
            
        except Exception as e:
            self._show_error(f"Failed to load permissions: {str(e)}")
    
    def _role_selected(self):
        """Handle role selection to show its permissions."""
        try:
            selected_items = self.roles_table.selectedItems()
            if not selected_items:
                return
                
            # TODO: Highlight permissions assigned to selected role
            # This would require querying role permissions and updating tree display
            
        except Exception as e:
            self._show_error(f"Error handling role selection: {str(e)}")
    
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
    
    def _add_role(self):
        """Show dialog to add new role."""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get role name
        name, ok1 = QInputDialog.getText(
            self, 
            "Add Role | إضافة دور",
            "Enter role name | أدخل اسم الدور:"
        )
        if not ok1 or not name.strip():
            return
        
        # Get role code
        code, ok2 = QInputDialog.getText(
            self,
            "Add Role | إضافة دور",
            "Enter role code | أدخل رمز الدور:"
        )
        if not ok2 or not code.strip():
            return
        
        # Create role via service
        data = {
            'name': name.strip(),
            'code': code.strip(),
            'description': None,
            'is_active': True
        }
        
        service = get_role_service()
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "Role created successfully.\n\nتم إنشاء الدور بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Role creation error {error_id}: {e}")
            self._show_error(
                f"Failed to create role | فشل إنشاء الدور\nError ID: {error_id}\nDetails: {str(e)}",
                title="Error | خطأ"
            )
    
    def _edit_role(self):
        """Edit selected role."""
        current_row = self.roles_table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a role to edit. | يرجى اختيار دور للتعديل.")
            return
        
        role_id = self.roles_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        role_name = self.roles_table.item(current_row, 0).text()
        role_code = self.roles_table.item(current_row, 1).text()
        
        from PyQt6.QtWidgets import QInputDialog
        
        # Get new role name
        name, ok1 = QInputDialog.getText(
            self, 
            "Edit Role | تعديل الدور",
            "Enter role name | أدخل اسم الدور:",
            text=role_name
        )
        if not ok1:
            return
        
        # Get new role code
        code, ok2 = QInputDialog.getText(
            self,
            "Edit Role | تعديل الدور",
            "Enter role code | أدخل رمز الدور:",
            text=role_code
        )
        if not ok2:
            return
        
        # Update role via service
        data = {
            'name': name.strip() if name else role_name,
            'code': code.strip() if code else role_code
        }
        
        service = get_role_service()
        try:
            with session_scope() as session:
                instance, errors = service.update(session, role_id, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "Role updated successfully.\n\nتم تحديث الدور بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Role update error {error_id}: {e}")
            self._show_error(
                f"Failed to update role | فشل تحديث الدور\nError ID: {error_id}\nDetails: {str(e)}",
                title="Error | خطأ"
            )
    
    def _delete_role(self):
        """Delete selected role via service layer."""
        current_row = self.roles_table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a role to delete. | يرجى اختيار دور للحذف.")
            return
            
        role_name = self.roles_table.item(current_row, 0).text()
        
        if self._ask_confirmation(
            f"Are you sure you want to delete role '{role_name}'?\n"
            f"This action cannot be undone.\n\n"
            f"هل أنت متأكد من حذف الدور '{role_name}'؟\n"
            f"لا يمكن التراجع عن هذا الإجراء."
        ):
            role_id = self.roles_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            service = get_role_service()
            
            try:
                with session_scope() as session:
                    success, errors = service.delete(session, role_id)
                    
                    if not success or errors:
                        self._display_validation_errors(errors)
                        return
                    
                    self._show_info(
                        "Role deleted successfully.\n\nتم حذف الدور بنجاح.",
                        title="Success | نجاح"
                    )
                    self.refresh_view()
            except Exception as e:
                error_id = str(uuid.uuid4())[:8]
                logger = logging.getLogger(__name__)
                logger.exception(f"Role deletion error {error_id}: {e}")
                self._show_error(
                    f"Failed to delete role | فشل حذف الدور\nError ID: {error_id}\nDetails: {str(e)}",
                    title="Error | خطأ"
                )
    
    def _assign_permission(self):
        """Assign permission to selected role."""
        # TODO: Implement permission assignment
        self._show_info(
            "Assign Permission functionality not yet implemented.\\n"
            "This will assign the selected permission to the selected role.\\n\\n"
            "وظيفة تعيين الصلاحية لم يتم تنفيذها بعد.\\n"
            "ستقوم بتعيين الصلاحية المختارة للدور المحدد.",
            "Coming Soon | قريباً"
        )
    
    def _revoke_permission(self):
        """Revoke permission from selected role."""
        # TODO: Implement permission revocation
        self._show_info(
            "Revoke Permission functionality not yet implemented.\\n"
            "This will remove the selected permission from the selected role.\\n\\n"
            "وظيفة إلغاء الصلاحية لم يتم تنفيذها بعد.\\n"
            "ستقوم بإزالة الصلاحية المختارة من الدور المحدد.",
            "Coming Soon | قريباً"
        )
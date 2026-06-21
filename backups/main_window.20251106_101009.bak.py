"""
Main Application Window with Navigation.

Provides centralized navigation to all system modules based on user roles.
"""

from typing import Optional, Dict, Any
import importlib
import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget,
    QListWidget, QListWidgetItem, QFrame
)

from core.database import SessionLocal
from core.auth import logout_user
from core.session_manager import session_manager
from core.permissions import permission_manager
from models import User

# Configure logging
logger = logging.getLogger(__name__)

# Setup UI routing logger
routing_logger = logging.getLogger('ui_routing')
routing_handler = logging.FileHandler('logs/ui_routing.log')
routing_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
routing_handler.setFormatter(routing_formatter)
routing_logger.addHandler(routing_handler)
routing_logger.setLevel(logging.INFO)


class WelcomePage(QWidget):
    """Welcome page widget for dashboard."""
    
    def __init__(self, app_context=None, parent: Optional[QWidget] = None):
        """Initialize welcome page.
        
        Args:
            app_context: Application context (optional, for compatibility)
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup welcome page UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel("Welcome to Hassad ERP | مرحباً بك في نظام حساد")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(20)
        
        # Description
        desc_label = QLabel(
            "Enterprise Resource Planning System\n"
            "نظام تخطيط موارد المؤسسة\n\n"
            "Select a module from the sidebar to get started.\n"
            "اختر وحدة من الشريط الجانبي للبدء."
        )
        desc_label.setStyleSheet("font-size: 14px; color: #666;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        self.setLayout(layout)

# Module registry mapping module_id -> (module_path, class_name, permission_required)
MODULE_REGISTRY = {
    "dashboard": ("ui.main_window", "WelcomePage", "dashboard.view"),
    "users": ("ui.users_window", "UsersWindow", "users.view"),
    "roles": ("ui.roles_window", "RolesWindow", "roles.view"),
    "company": ("ui.company_window", "CompanyWindow", "company.view"),
    "branches": ("ui.branches_window", "BranchesWindow", "branches.view"),
    "accounts": ("ui.accounts_window", "AccountsWindow", "accounting.view"),
    "journals": ("ui.journals_window", "JournalsWindow", "accounting.view"),
    "trial_balance": ("ui.trial_balance_window", "TrialBalanceWindow", "accounting.view"),
    "products": ("ui.products_window", "ProductsWindow", "inventory.view"),
    "categories": ("ui.categories_window", "CategoriesWindow", "inventory.view"),
    "stock_movements": ("ui.stock_movements_window", "StockMovementsWindow", "inventory.view"),
    "inventory_valuation": ("ui.inventory_valuation_window", "InventoryValuationWindow", "inventory.view"),
    "pos": ("ui.pos_interface_window", "POSInterfaceWindow", "sales.view"),
    "sales_history": ("ui.sales_history_window", "SalesHistoryWindow", "sales.view"),
    "customers": ("ui.customers_window", "CustomersWindow", "sales.view"),
    "suppliers": ("ui.suppliers_window", "SuppliersWindow", "purchases.view"),
    "purchase_orders": ("ui.purchase_orders_window", "PurchaseOrdersWindow", "purchases.view"),
    "goods_receipt": ("ui.goods_receipt_window", "GoodsReceiptWindow", "purchases.view"),
    "purchase_invoices": ("ui.purchase_invoices_window", "PurchaseInvoicesWindow", "purchases.view"),
    "reports": ("ui.reports_window", "ReportsWindow", "reports.view"),
    "settings": ("ui.settings_window", "SettingsWindow", "settings.view"),
}


class MainWindow(QMainWindow):
    """
    Main application window with sidebar navigation.
    
    Provides role-based access to all system modules.
    """
    
    def __init__(self, user: User, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user = user
        self.current_module = None
        
        # Module instance tracking
        self._module_instances: Dict[str, Any] = {}
        self._app_context = {
            'session_factory': SessionLocal,
            'current_user': user,
            'current_company': None,  # TODO: Get from user context
            'current_branch': user.branch,
            'permission_manager': permission_manager
        }
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle(f"Hassad ERP - {self.user.full_name}")
        self.setMinimumSize(1400, 900)
        
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # Add welcome page
        welcome_page = self._create_welcome_page()
        self.content_stack.addWidget(welcome_page)
        
        central_widget.setLayout(main_layout)
    
    def _create_sidebar(self) -> QWidget:
        """Create navigation sidebar."""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
            QLabel {
                color: white;
                padding: 10px;
            }
            QListWidget {
                background-color: #2c3e50;
                border: none;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("HASSAD ERP")
        header.setStyleSheet("font-size: 18px; font-weight: bold; background-color: #1a252f; padding: 20px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # User info
        user_info = QLabel(f"{self.user.full_name}\n{', '.join([r.name for r in self.user.roles])}")
        user_info.setStyleSheet("font-size: 12px; padding: 15px; background-color: #34495e;")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(user_info)
        
        # Navigation menu
        self.nav_list = QListWidget()
        self.nav_list.itemClicked.connect(self._navigate_to_module)
        
        # Add menu items based on user roles
        self._add_navigation_items()
        
        layout.addWidget(self.nav_list)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self._handle_logout)
        layout.addWidget(logout_btn)
        
        sidebar.setLayout(layout)
        return sidebar
    
    def _add_navigation_items(self) -> None:
        """Add navigation items based on user permissions."""
        try:
            # Dashboard (all users)
            self._add_nav_item("Dashboard", "dashboard")
            
            # Iterate through module registry and add items based on permissions
            for module_id, (module_path, class_name, permission) in MODULE_REGISTRY.items():
                if module_id == "dashboard":
                    continue  # Already added
                
                # Check if user has permission or is admin
                if permission_manager.has_permission(self.user, permission) or permission_manager.is_admin(self.user):
                    # Map module_id to user-friendly names
                    display_names = {
                        "users": "Users",
                        "roles": "Roles & Permissions",
                        "company": "Company Settings",
                        "branches": "Branch Management",
                        "accounts": "Chart of Accounts",
                        "journals": "Journal Entries",
                        "trial_balance": "Trial Balance",
                        "products": "Products",
                        "categories": "Categories",
                        "stock_movements": "Stock Movements",
                        "inventory_valuation": "Inventory Valuation",
                        "pos": "POS",
                        "sales_history": "Sales History",
                        "customers": "Customers",
                        "suppliers": "Suppliers",
                        "purchase_orders": "Purchase Orders",
                        "goods_receipt": "Goods Receipt",
                        "purchase_invoices": "Purchase Invoices",
                        "reports": "Reports",
                        "settings": "System Settings"
                    }
                    
                    display_name = display_names.get(module_id, module_id.replace('_', ' ').title())
                    self._add_nav_item(display_name, module_id)
                    
        except Exception as e:
            logger.error(f"Error adding navigation items: {e}")
            # Fallback to basic navigation
            self._add_nav_item("Dashboard", "dashboard")
            if permission_manager.is_admin(self.user):
                self._add_nav_item("Users", "users")
                self._add_nav_item("Products", "products")
    
    def _add_nav_item(self, text: str, module_id: str) -> None:
        """Add navigation item to list."""
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, module_id)
        self.nav_list.addItem(item)
    
    def _create_welcome_page(self) -> QWidget:
        """Create welcome/dashboard page."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        welcome_label = QLabel(f"Welcome, {self.user.full_name}!")
        welcome_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(welcome_label)
        
        role_label = QLabel(f"Role: {', '.join([r.name for r in self.user.roles])}")
        role_label.setStyleSheet("font-size: 16px; color: #666; margin-top: 10px;")
        layout.addWidget(role_label)
        
        branch_label = QLabel(f"Branch: {self.user.branch.name if self.user.branch else 'N/A'}")
        branch_label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(branch_label)
        
        layout.addSpacing(40)
        
        info_label = QLabel("Select a module from the sidebar to get started.")
        info_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def _navigate_to_module(self, item: QListWidgetItem) -> None:
        """Navigate to selected module with dynamic loading and error handling."""
        module_id = item.data(Qt.ItemDataRole.UserRole)
        routing_logger.info(f"Navigation requested to module: {module_id} by user: {self.user.username}")
        
        try:
            # Handle dashboard special case
            if module_id == "dashboard":
                self._show_dashboard()
                return
            
            # Check if module is already instantiated
            if module_id in self._module_instances:
                widget = self._module_instances[module_id]
                if hasattr(widget, 'refresh_view'):
                    widget.refresh_view()
                self._set_current_widget(widget)
                return
            
            # Get module info from registry
            if module_id not in MODULE_REGISTRY:
                self._show_module_error(f"Module '{item.text()}' not found in registry.")
                return
            
            module_path, class_name, permission = MODULE_REGISTRY[module_id]
            
            # Double-check permissions
            if not (permission_manager.has_permission(self.user, permission) or permission_manager.is_admin(self.user)):
                self._show_access_denied(item.text())
                return
            
            # Dynamic import and instantiation
            widget = self._load_module_widget(module_path, class_name, module_id)
            
            if widget:
                # Cache the widget
                self._module_instances[module_id] = widget
                
                # Refresh data and show
                if hasattr(widget, 'refresh_view'):
                    QTimer.singleShot(100, widget.refresh_view)  # Slight delay for UI setup
                
                self._set_current_widget(widget)
                self.current_module = module_id
                
                logger.info(f"Successfully loaded module: {module_id}")
                routing_logger.info(f"SUCCESS: Module {module_id} loaded and displayed successfully")
            
        except Exception as e:
            logger.error(f"Failed to navigate to module {module_id}: {e}", exc_info=True)
            routing_logger.error(f"FAILURE: Module {module_id} failed to load: {str(e)}")
            self._show_module_error(f"Failed to load {item.text()}: {str(e)}")
    
    def _load_module_widget(self, module_path: str, class_name: str, module_id: str):
        """Dynamically load and instantiate a module widget."""
        routing_logger.info(f"Attempting to load module: {module_path}.{class_name} for {module_id}")
        try:
            # Import the module
            module = importlib.import_module(module_path)
            routing_logger.info(f"Successfully imported module: {module_path}")
            
            # Get the class
            widget_class = getattr(module, class_name)
            routing_logger.info(f"Found class {class_name} in module {module_path}")
            
            # Instantiate with app context
            widget = widget_class(app_context=self._app_context, parent=self)
            routing_logger.info(f"Successfully instantiated {class_name}")
            
            logger.debug(f"Successfully instantiated {class_name} from {module_path}")
            return widget
            
        except ImportError as e:
            logger.error(f"Failed to import {module_path}: {e}")
            routing_logger.error(f"IMPORT_ERROR: {module_path} - {str(e)}")
            self._show_import_error(module_id, str(e))
            return None
            
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in {module_path}: {e}")
            routing_logger.error(f"CLASS_NOT_FOUND: {class_name} in {module_path} - {str(e)}")
            self._show_class_error(module_id, class_name, str(e))
            return None
            
        except Exception as e:
            logger.error(f"Failed to instantiate {class_name}: {e}", exc_info=True)
            routing_logger.error(f"INSTANTIATION_ERROR: {class_name} - {str(e)}")
            self._show_instantiation_error(module_id, str(e))
            return None
    
    def _set_current_widget(self, widget):
        """Set widget as current in content stack."""
        try:
            # Remove old widgets (keep welcome page at index 0)
            while self.content_stack.count() > 1:
                old_widget = self.content_stack.widget(1)
                self.content_stack.removeWidget(old_widget)
                # Don't delete cached widgets
            
            # Add new widget
            self.content_stack.addWidget(widget)
            self.content_stack.setCurrentIndex(1)
            
        except Exception as e:
            logger.error(f"Failed to set current widget: {e}")
    
    def _show_module_error(self, message: str):
        """Show module loading error."""
        QMessageBox.critical(
            self,
            "Module Error | خطأ في الوحدة",
            f"{message}\n\nPlease contact administrator. | يرجى الاتصال بالمدير."
        )
    
    def _show_access_denied(self, module_name: str):
        """Show access denied message."""
        QMessageBox.warning(
            self,
            "Access Denied | تم رفض الوصول",
            f"You don't have permission to access {module_name}.\n\nContact administrator for access. | ليس لديك صلاحية للوصول إلى {module_name}.\n\nاتصل بالمدير للحصول على الصلاحية."
        )
    
    def _show_import_error(self, module_id: str, error: str):
        """Show import error with technical details."""
        QMessageBox.critical(
            self,
            "Module Import Error | خطأ في استيراد الوحدة",
            f"Failed to import module '{module_id}'. Module may not be implemented yet.\n\n"
            f"Technical details: {error}\n\n"
            f"فشل في استيراد الوحدة '{module_id}'. قد لا تكون الوحدة مُطبقة بعد.\n\n"
            f"التفاصيل التقنية: {error}"
        )
    
    def _show_class_error(self, module_id: str, class_name: str, error: str):
        """Show class not found error."""
        QMessageBox.critical(
            self,
            "Module Class Error | خطأ في فئة الوحدة",
            f"Class '{class_name}' not found in module '{module_id}'.\n\n"
            f"Technical details: {error}\n\n"
            f"الفئة '{class_name}' غير موجودة في الوحدة '{module_id}'.\n\n"
            f"التفاصيل التقنية: {error}"
        )
    
    def _show_instantiation_error(self, module_id: str, error: str):
        """Show widget instantiation error."""
        QMessageBox.critical(
            self,
            "Module Instantiation Error | خطأ في إنشاء الوحدة",
            f"Failed to create instance of module '{module_id}'.\n\n"
            f"Technical details: {error}\n\n"
            f"فشل في إنشاء مثيل للوحدة '{module_id}'.\n\n"
            f"التفاصيل التقنية: {error}"
        )
    
    def _show_dashboard(self) -> None:
        """Show dashboard."""
        self.content_stack.setCurrentIndex(0)
        self.current_module = "dashboard"
    
    def _handle_logout(self) -> None:
        """Handle logout action."""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Logout from database
            db = SessionLocal()
            try:
                logout_user(db, self.user, session_manager.get_session_token())
            finally:
                db.close()
            
            # Clear session
            session_manager.logout()
            
            # Close window and return to login
            self.close()
            
            # Show login window again
            from ui.app_launcher import show_login
            show_login()

"""
Main Application Window with Navigation.

Provides centralized navigation to all system modules based on user roles.
"""

from typing import Optional, Dict, Any
import importlib
import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget,
    QListWidget, QListWidgetItem, QFrame, QMenu, QMenuBar, QToolBar
)
from PyQt6.QtGui import QAction

from ui.components.navigation_widget import NavigationWidget
from ui.components.breadcrumb_widget import BreadcrumbWidget

from core.database import SessionLocal
from core.auth import logout_user
from core.session_manager import session_manager
from core.permissions import permission_manager
from models import User
from ui.ui_helpers import wrap_window_for_embedding
from ui.theme_manager import get_theme_manager

# Configure logging
logger = logging.getLogger(__name__)

# Ensure logs directory exists
import os
os.makedirs('logs', exist_ok=True)

# Setup UI routing logger
routing_logger = logging.getLogger('ui_routing')
routing_handler = logging.FileHandler('logs/ui_routing.log')
routing_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
routing_handler.setFormatter(routing_formatter)
routing_logger.addHandler(routing_handler)
routing_logger.setLevel(logging.INFO)


class WelcomePage(QWidget):
    """Welcome page widget for dashboard."""
    
    def __init__(self, user=None, app_context=None, parent: Optional[QWidget] = None):
        """Initialize welcome page.
        
        Args:
            user: Current user (for personalized welcome)
            app_context: Application context (optional, for compatibility)
            parent: Parent widget
        """
        super().__init__(parent)
        self.user = user
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup welcome page UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Personalized welcome if user provided
        if self.user:
            welcome_label = QLabel(f"Welcome, {self.user.full_name}! | مرحباً، {self.user.full_name}!")
            welcome_label.setStyleSheet("font-size: 28px; font-weight: bold;")
            layout.addWidget(welcome_label)
            
            role_label = QLabel(f"Role: {', '.join([r.name for r in self.user.roles])} | الدور: {', '.join([r.name for r in self.user.roles])}")
            role_label.setStyleSheet("font-size: 16px; color: #666; margin-top: 10px;")
            layout.addWidget(role_label)
            
            if self.user.branch:
                branch_label = QLabel(f"Branch: {self.user.branch.name} | الفرع: {self.user.branch.name}")
                branch_label.setStyleSheet("font-size: 16px; color: #666;")
                layout.addWidget(branch_label)
            
            layout.addSpacing(40)
        else:
            # Generic welcome
            title_label = QLabel("Welcome to Hassad ERP | مرحباً بك في نظام حساد")
            title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            layout.addSpacing(20)
        
        # Instructions
        info_label = QLabel(
            "Enterprise Resource Planning System\n"
            "نظام تخطيط موارد المؤسسة\n\n"
            "Select a module from the sidebar to get started.\n"
            "اختر وحدة من الشريط الجانبي للبدء."
        )
        info_label.setStyleSheet("font-size: 14px; color: #666;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        self.setLayout(layout)

# Module registry mapping module_id -> (module_path, class_name, permission_required)
MODULE_REGISTRY = {
    "dashboard": ("ui.dashboard_window", "DashboardWindow", "dashboard.view"),
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
        self._module_instances: Dict[str, Any] = {}  # Original widget instances
        self._wrapped_widgets: Dict[str, QWidget] = {}  # Wrapped widgets for stack
        self._app_context = {
            'session_factory': SessionLocal,
            'current_user': user,
            'current_company': None,  # TODO: Get from user context
            'current_branch': user.branch,
            'permission_manager': permission_manager
        }
        
        # Theme manager
        self.theme_manager = get_theme_manager()
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        # Apply persisted theme at startup
        app = QApplication.instance()
        if app is not None:
            self.theme_manager.apply_theme(app)
        
        # Navigation metadata for breadcrumb
        self.current_group_name = ""
        self.current_group_name_ar = ""
        self.current_module_name = ""
        self.current_module_name_ar = ""
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle(f"Hassad ERP - {self.user.full_name}")
        self.setMinimumSize(1400, 900)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar with new hierarchical navigation
        sidebar = self._create_modern_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area with breadcrumb
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, 1)
        
        central_widget.setLayout(main_layout)
        
        # Add modern dashboard as welcome page (Phase F2.5)
        # Dashboard will be loaded dynamically on first navigation to index 0
        # Keep WelcomePage as fallback for users without dashboard permission
        welcome_page = WelcomePage(user=self.user, app_context=self._app_context, parent=self)
        self.content_stack.addWidget(welcome_page)
        routing_logger.info(f"Welcome page added to stack at index 0 (dashboard loads dynamically)")
        
        # Test signal connection after UI setup
        routing_logger.info(f"UI setup complete. Navigation widget initialized")
        print(f"\n[STARTUP] Main window UI setup complete with hierarchical navigation.")
        print(f"[STARTUP] Content stack has {self.content_stack.count()} widgets")
        print(f"[STARTUP] Signal connections: module_selected -> _navigate_to_module\n")
    
    def _create_menu_bar(self) -> None:
        """Create menu bar with theme options."""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu("View | عرض")
        
        # Theme submenu
        theme_menu = QMenu("Theme | المظهر", self)
        
        # Light theme action
        light_action = QAction("Light Theme | الوضع الفاتح", self)
        light_action.triggered.connect(self._set_light_theme)
        theme_menu.addAction(light_action)
        
        # Dark theme action
        dark_action = QAction("Dark Theme | الوضع الداكن", self)
        dark_action.triggered.connect(self._set_dark_theme)
        theme_menu.addAction(dark_action)
        
        theme_menu.addSeparator()
        
        # Toggle theme action
        toggle_action = QAction("Toggle Theme | تبديل المظهر", self)
        toggle_action.setShortcut("Ctrl+T")
        toggle_action.triggered.connect(self._toggle_theme)
        theme_menu.addAction(toggle_action)
        
        view_menu.addMenu(theme_menu)
        
        # Layout submenu
        layout_menu = QMenu("Layout | التخطيط", self)
        
        # RTL action
        rtl_action = QAction("Enable RTL | تفعيل الاتجاه من اليمين لليسار", self)
        rtl_action.setCheckable(True)
        rtl_action.setChecked(self.theme_manager.is_rtl)
        rtl_action.triggered.connect(self._toggle_rtl)
        layout_menu.addAction(rtl_action)
        self.rtl_action = rtl_action  # Store reference for updates
        
        view_menu.addMenu(layout_menu)
        
        # Help menu
        help_menu = menubar.addMenu("Help | مساعدة")
        
        about_action = QAction("About Hassad ERP | عن نظام حساد", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        routing_logger.info("Menu bar created with theme options")
    
    def _create_modern_sidebar(self) -> QWidget:
        """Create modern hierarchical navigation sidebar."""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #2c3e50;
                border-right: 2px solid #34495e;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("HASSAD ERP")
        header.setStyleSheet("font-size: 18px; font-weight: bold; background-color: #1a252f; padding: 20px; color: white;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # User info
        user_info = QLabel(f"{self.user.full_name}\n{', '.join([r.name for r in self.user.roles])}")
        user_info.setStyleSheet("font-size: 12px; padding: 15px; background-color: #34495e; color: white;")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(user_info)
        
        # Hierarchical navigation widget
        self.navigation_widget = NavigationWidget(
            user=self.user,
            permission_manager=permission_manager,
            show_arabic=False,
            parent=self
        )
        self.navigation_widget.module_selected.connect(self._on_navigation_module_selected)
        layout.addWidget(self.navigation_widget)
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout | تسجيل الخروج")
        logout_btn.clicked.connect(self._handle_logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        layout.addWidget(logout_btn)
        
        sidebar.setLayout(layout)
        routing_logger.info("Modern hierarchical sidebar created")
        return sidebar
    
    def _create_content_area(self) -> QWidget:
        """Create content area with breadcrumb and stacked widget."""
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_widget.setLayout(content_layout)
        
        # Breadcrumb navigation
        self.breadcrumb = BreadcrumbWidget(show_arabic=False, parent=self)
        self.breadcrumb.breadcrumb_clicked.connect(self._on_breadcrumb_clicked)
        self.breadcrumb.setStyleSheet("""
            QWidget#breadcrumbWidget {
                background-color: #ecf0f1;
                border-bottom: 1px solid #bdc3c7;
            }
        """)
        content_layout.addWidget(self.breadcrumb)
        
        # Content stack
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        return content_widget
    
    def _create_toolbar(self) -> None:
        """Create toolbar with quick actions."""
        toolbar = QToolBar("Quick Actions")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Quick action: New Sale
        new_sale_action = QAction("🛒 New Sale", self)
        new_sale_action.setShortcut("Ctrl+N")
        new_sale_action.setStatusTip("Create a new sale transaction")
        new_sale_action.triggered.connect(lambda: self._navigate_to_module_by_id("pos"))
        toolbar.addAction(new_sale_action)
        
        toolbar.addSeparator()
        
        # Quick action: Reports
        reports_action = QAction("📊 Reports", self)
        reports_action.setShortcut("Ctrl+R")
        reports_action.setStatusTip("View reports and analytics")
        reports_action.triggered.connect(lambda: self._navigate_to_module_by_id("reports"))
        toolbar.addAction(reports_action)
        
        routing_logger.info("Toolbar created with quick actions")
    
    def _on_navigation_module_selected(self, module_id: str, group_name: str, group_name_ar: str, 
                                      module_name: str, module_name_ar: str):
        """Handle navigation widget module selection."""
        routing_logger.info(f"Navigation module selected: {module_id} from group {group_name}")
        
        # Store current navigation context
        self.current_group_name = group_name
        self.current_group_name_ar = group_name_ar
        self.current_module_name = module_name
        self.current_module_name_ar = module_name_ar
        
        # Update breadcrumb
        self.breadcrumb.set_path(
            group_name=group_name,
            group_name_ar=group_name_ar,
            module_id=module_id,
            module_name=module_name,
            module_name_ar=module_name_ar,
            module_icon=""
        )
        
        # Navigate to module
        self._navigate_to_module_by_id(module_id)
    
    def _on_breadcrumb_clicked(self, item_id: str):
        """Handle breadcrumb navigation click."""
        routing_logger.info(f"Breadcrumb clicked: {item_id}")
        
        if item_id == "dashboard":
            self._show_dashboard()
            self.breadcrumb.reset_to_home()
        else:
            # Navigate to the clicked module
            self._navigate_to_module_by_id(item_id)
    
    
    def _navigate_to_module_by_id(self, module_id: str) -> None:
        """Navigate to module by ID (for toolbar/breadcrumb navigation)."""
        routing_logger.info(f"Direct navigation to module: {module_id} by user: {self.user.username}")
        
        # DEBUG OUTPUT
        print(f"\n{'='*70}")
        print(f"NAVIGATION DEBUG: {module_id}")
        print(f"Current stack count BEFORE: {self.content_stack.count()}")
        print(f"Current index BEFORE: {self.content_stack.currentIndex()}")
        if self.content_stack.currentWidget():
            print(f"Current widget BEFORE: {self.content_stack.currentWidget().__class__.__name__}")
        print(f"{'='*70}")
        
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
                # Use the wrapped widget if it exists
                display_widget = self._wrapped_widgets.get(module_id, widget)
                self._set_current_widget_direct(display_widget)
                routing_logger.info(f"Reusing cached module: {module_id}")
                return
            
            # Get module info from registry
            if module_id not in MODULE_REGISTRY:
                self._show_module_error(f"Module '{module_id}' not found in registry.")
                return
            
            module_path, class_name, permission = MODULE_REGISTRY[module_id]
            
            # Double-check permissions
            if not (permission_manager.has_permission(self.user, permission) or permission_manager.is_admin(self.user)):
                self._show_access_denied(module_id)
                return
            
            # Dynamic import and instantiation
            widget = self._load_module_widget(module_path, class_name, module_id)
            
            if widget:
                # Cache the original widget
                self._module_instances[module_id] = widget
                
                # Wrap and display
                embeddable = wrap_window_for_embedding(widget, parent=self.content_stack)
                self._wrapped_widgets[module_id] = embeddable
                
                # Refresh data and show
                if hasattr(widget, 'refresh_view'):
                    QTimer.singleShot(100, widget.refresh_view)  # Slight delay for UI setup
                
                self._set_current_widget_direct(embeddable)
                self.current_module = module_id
                
                # DEBUG OUTPUT AFTER LOAD
                print(f"\nAFTER LOAD:")
                print(f"Stack count: {self.content_stack.count()}")
                print(f"Current index: {self.content_stack.currentIndex()}")
                if self.content_stack.currentWidget():
                    print(f"Current widget: {self.content_stack.currentWidget().__class__.__name__}")
                    print(f"Widget visible: {self.content_stack.currentWidget().isVisible()}")
                print(f"{'='*70}\n")
                
                logger.info(f"Successfully loaded module: {module_id}")
                routing_logger.info(f"SUCCESS: Module {module_id} loaded and displayed successfully")
            
        except Exception as e:
            logger.error(f"Failed to navigate to module {module_id}: {e}", exc_info=True)
            routing_logger.error(f"FAILURE: Module {module_id} failed to load: {str(e)}")
            self._show_module_error(f"Failed to load {module_id}: {str(e)}")
    
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
    
    def _set_current_widget_direct(self, embeddable_widget: QWidget):
        """Set a pre-wrapped widget as current in content stack.
        
        Args:
            embeddable_widget: Widget already prepared for embedding (QWidget, not QMainWindow)
        """
        try:
            # Check if this widget is already in the stack
            widget_index = -1
            for i in range(self.content_stack.count()):
                if self.content_stack.widget(i) is embeddable_widget:
                    widget_index = i
                    break
            
            # If not in stack, add it
            if widget_index == -1:
                widget_index = self.content_stack.addWidget(embeddable_widget)
                routing_logger.info(f"Added widget to stack at index {widget_index}: {embeddable_widget.__class__.__name__}")
            
            # Set as current widget
            self.content_stack.setCurrentIndex(widget_index)
            
            # Ensure visibility
            embeddable_widget.setVisible(True)
            embeddable_widget.show()
            self.content_stack.show()  # Ensure stack itself is visible
            
            routing_logger.info(f"Switched to widget at index {widget_index}: {embeddable_widget.__class__.__name__} (Visible={embeddable_widget.isVisible()}, Stack count={self.content_stack.count()})")
            
        except Exception as e:
            logger.error(f"Failed to set current widget: {e}", exc_info=True)
            routing_logger.error(f"ERROR setting current widget: {str(e)}")
    
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
        self.breadcrumb.reset_to_home()
        self.navigation_widget.select_module("dashboard")
    
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
    
    def _set_light_theme(self) -> None:
        """Set light theme."""
        self.theme_manager.set_light_theme()
        routing_logger.info("User switched to light theme")
    
    def _set_dark_theme(self) -> None:
        """Set dark theme."""
        self.theme_manager.set_dark_theme()
        routing_logger.info("User switched to dark theme")
    
    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        self.theme_manager.toggle_theme()
        routing_logger.info(f"Theme toggled to {self.theme_manager.current_theme.value}")
    
    def _toggle_rtl(self) -> None:
        """Toggle RTL layout."""
        self.theme_manager.toggle_direction()
        # Update checkbox state
        if hasattr(self, 'rtl_action'):
            self.rtl_action.setChecked(self.theme_manager.is_rtl)
        routing_logger.info(f"Layout direction: {self.theme_manager.current_direction.value}")
    
    def _on_theme_changed(self, theme_name: str, is_rtl: bool) -> None:
        """Handle theme change event.
        
        Args:
            theme_name: Name of the new theme
            is_rtl: Whether RTL is enabled
        """
        routing_logger.info(f"Theme changed event: {theme_name}, RTL={is_rtl}")
        
        # Update window title to reflect current theme
        theme_indicator = "🌙" if theme_name == "dark" else "☀"
        direction_indicator = "→" if is_rtl else "←"
        self.setWindowTitle(f"{theme_indicator} Hassad ERP - {self.user.full_name} {direction_indicator}")
        
        # Show status message
        if hasattr(self, 'statusBar'):
            theme_display = self.theme_manager.get_theme_name(bilingual=True)
            self.statusBar().showMessage(f"Theme: {theme_display}", 3000)
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Hassad ERP | عن نظام حساد",
            f"<h2>Hassad ERP System</h2>"
            f"<p>نظام حساد لتخطيط موارد المؤسسة</p>"
            f"<p><b>Version:</b> 1.0.0</p>"
            f"<p><b>Theme Engine:</b> Phase F2.1</p>"
            f"<p><b>Current Theme:</b> {self.theme_manager.get_theme_name(bilingual=True)}</p>"
            f"<p><b>Layout:</b> {'RTL (Right-to-Left)' if self.theme_manager.is_rtl else 'LTR (Left-to-Right)'}</p>"
            f"<hr>"
            f"<p>A modern, bilingual ERP system with full Arabic support.</p>"
            f"<p>© 2024 Hassad ERP Development Team</p>"
        )

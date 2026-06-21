"""
Base UI Module Contract for Hassad ERP.

Provides standardized interface for all module UI components
with session management, error handling, and bilingual support.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QObject
from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QProgressBar, QFrame
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models import User

# Configure logging
logger = logging.getLogger(__name__)


class ModuleUIError(Exception):
    """Base exception for module UI errors."""
    pass


class SessionError(ModuleUIError):
    """Raised when database session operations fail."""
    pass


class ModuleUI:
    """
    Base mixin class for all module UI components.
    
    Provides standardized interface with:
    - Session management
    - Error handling with bilingual messages
    - Loading states
    - Data refresh capabilities
    - Permission context
    
    This is a mixin class that should be used with ModuleWidget or ModuleMainWindow.
    Do NOT inherit from this class directly - use ModuleWidget or ModuleMainWindow.
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        """
        Initialize module UI.
        
        Args:
            app_context: Application context containing:
                - session_factory: SQLAlchemy session factory
                - current_user: User object
                - current_company: Company object (optional)
                - current_branch: Branch object (optional)
                - permission_manager: Permission manager instance
            parent: Parent widget
        """
        # Store context
        self.app_context = app_context or {}
        self.session_factory = self.app_context.get('session_factory')
        self.current_user: Optional[User] = self.app_context.get('current_user')
        self.current_company = self.app_context.get('current_company')
        self.current_branch = self.app_context.get('current_branch')
        self.permission_manager = self.app_context.get('permission_manager')
        
        # State tracking
        self._is_loading = False
        self._last_error: Optional[str] = None
        self._data_loaded = False
        
        logger.debug(f"Initialized {self.__class__.__name__} for user {self.current_user.username if self.current_user else 'unknown'}")
    
    
    @abstractmethod
    def load_data(self, session: Session) -> None:
        """
        Load data from database.
        
        This method MUST be implemented by all subclasses.
        It should load all necessary data for the module.
        
        Args:
            session: Active database session
            
        Raises:
            NotImplementedError: If not implemented by subclass
            SessionError: If database operation fails
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement load_data()")
    
    def refresh_view(self) -> None:
        """
        Refresh the view by reloading data.
        
        This method handles session management automatically
        and provides error handling and loading states.
        """
        if not self.session_factory:
            self._show_error(
                "Database session not available | جلسة قاعدة البيانات غير متاحة",
                "Session Error"
            )
            return
        
        if self._is_loading:
            logger.debug(f"{self.__class__.__name__} already loading, skipping refresh")
            return
        
        try:
            self._set_loading(True)
            
            with self.session_factory() as session:
                self.load_data(session)
                self._data_loaded = True
                if hasattr(self, 'data_loaded'):
                    self.data_loaded.emit()
                logger.debug(f"{self.__class__.__name__} data loaded successfully")
                
        except SQLAlchemyError as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(f"{self.__class__.__name__} database error: {e}")
            if hasattr(self, 'error_occurred'):
                self.error_occurred.emit(error_msg)
            self._on_error_occurred(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{self.__class__.__name__} unexpected error: {e}", exc_info=True)
            if hasattr(self, 'error_occurred'):
                self.error_occurred.emit(error_msg)
            self._on_error_occurred(error_msg)
            
        finally:
            self._set_loading(False)
    
    def get_session_context(self):
        """
        Get database session context manager.
        
        Returns:
            Context manager for database session
        """
        if not self.session_factory:
            raise SessionError("Session factory not available")
        
        return self.session_factory()
    
    def has_permission(self, permission_code: str) -> bool:
        """
        Check if current user has permission.
        
        Args:
            permission_code: Permission code to check
            
        Returns:
            bool: True if user has permission
        """
        if not self.permission_manager or not self.current_user:
            logger.warning(f"Permission check failed - missing manager or user: {permission_code}")
            return False
        
        return self.permission_manager.has_permission(self.current_user, permission_code)
    
    def is_admin(self) -> bool:
        """
        Check if current user is admin.
        
        Returns:
            bool: True if user is admin
        """
        if not self.permission_manager or not self.current_user:
            return False
        
        return self.permission_manager.is_admin(self.current_user)
    
    def _set_loading(self, loading: bool):
        """Set loading state and emit signal if available."""
        self._is_loading = loading
        if hasattr(self, 'data_loading'):
            self.data_loading.emit(loading)
        self._on_loading_state_changed(loading)
    
    def _on_loading_state_changed(self, loading: bool):
        """Handle loading state changes."""
        # Override in subclasses to update UI (e.g., show/hide progress bar)
        pass
    
    def _on_error_occurred(self, error_message: str):
        """Handle error occurrence."""
        self._last_error = error_message
        self._show_error(error_message, "Module Error | خطأ في الوحدة")
    
    def _show_error(self, message: str, title: str = "Error | خطأ"):
        """
        Show error dialog with bilingual support.
        
        Args:
            message: Error message
            title: Dialog title
        """
        QMessageBox.critical(
            self if isinstance(self, QWidget) else None,
            title,
            message
        )
    
    def _show_info(self, message: str, title: str = "Information | معلومات"):
        """
        Show information dialog.
        
        Args:
            message: Information message
            title: Dialog title
        """
        QMessageBox.information(
            self if isinstance(self, QWidget) else None,
            title,
            message
        )
    
    def _show_warning(self, message: str, title: str = "Warning | تحذير"):
        """
        Show warning dialog.
        
        Args:
            message: Warning message
            title: Dialog title
        """
        QMessageBox.warning(
            self if isinstance(self, QWidget) else None,
            title,
            message
        )
    
    def _ask_confirmation(self, message: str, title: str = "Confirm | تأكيد") -> bool:
        """
        Ask for user confirmation.
        
        Args:
            message: Confirmation message
            title: Dialog title
            
        Returns:
            bool: True if user confirmed
        """
        reply = QMessageBox.question(
            self if isinstance(self, QWidget) else None,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    @property
    def is_loading(self) -> bool:
        """Check if module is currently loading."""
        return self._is_loading
    
    @property
    def is_data_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._data_loaded
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error
    
    # ========================================================================
    # LAYOUT HELPER METHODS (Phase F2.2)
    # ========================================================================
    
    def create_modern_layout(self, pattern: str, **kwargs):
        """
        Create modern layout using layout manager.
        
        Args:
            pattern: Layout pattern name ('crud', 'list_detail', 'dashboard', 'form', 'report')
            **kwargs: Pattern-specific arguments
            
        Returns:
            Tuple of (container, components_dict)
            
        Example:
            container, components = self.create_modern_layout('crud')
            self.toolbar = components['toolbar']
            self.table = QTableWidget()
            components['data_layout'].addWidget(self.table)
        """
        try:
            from ui.layout_manager import get_layout_manager, LayoutPattern
            
            manager = get_layout_manager()
            pattern_map = {
                'crud': manager.create_crud_layout,
                'list_detail': manager.create_list_detail_layout,
                'dashboard': manager.create_dashboard_layout,
                'form': manager.create_form_layout,
                'report': manager.create_report_layout
            }
            
            if pattern not in pattern_map:
                raise ValueError(f"Unknown layout pattern: {pattern}")
            
            parent = self if isinstance(self, QWidget) else None
            return pattern_map[pattern](parent, **kwargs)
            
        except ImportError:
            logger.warning("Layout manager not available, using basic layout")
            # Return basic container
            container = QWidget(parent if isinstance(self, QWidget) else None)
            layout = QVBoxLayout(container)
            return container, {'layout': layout}
    
    def create_card(self, title: str = "", **kwargs):
        """
        Create a card component.
        
        Args:
            title: Card title
            **kwargs: Card options (collapsible, style)
            
        Returns:
            Card widget
        """
        try:
            from ui.layout_components import Card
            return Card(title, **kwargs)
        except ImportError:
            logger.warning("Card component not available, using basic frame")
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            return frame
    
    def create_toolbar(self, title: str = ""):
        """
        Create a toolbar component.
        
        Args:
            title: Optional toolbar title
            
        Returns:
            Toolbar widget
        """
        try:
            from ui.layout_components import Toolbar
            return Toolbar(title)
        except ImportError:
            logger.warning("Toolbar component not available, using basic widget")
            return QWidget()
    
    def create_filter_bar(self, placeholder: str = "Search... | بحث..."):
        """
        Create a filter bar component.
        
        Args:
            placeholder: Search field placeholder
            
        Returns:
            FilterBar widget
        """
        try:
            from ui.layout_components import FilterBar
            return FilterBar(placeholder)
        except ImportError:
            logger.warning("FilterBar component not available, using basic widget")
            return QWidget()


class ModuleWidget(QWidget, ModuleUI):
    """
    Base class for module widgets.
    
    Combines QWidget functionality with ModuleUI contract.
    Use this for modules that should be embedded in other windows.
    """
    
    # Signals for communication
    data_loaded = pyqtSignal()
    data_loading = pyqtSignal(bool)  # True when loading starts, False when ends
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        ModuleUI.__init__(self, app_context, parent)
        
        # Connect signals
        self.data_loading.connect(self._on_loading_state_changed)
        self.error_occurred.connect(self._on_error_occurred)
        
        # Setup basic layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Add loading indicator
        self._setup_loading_ui()
    
    def _setup_loading_ui(self):
        """Setup loading indicator UI."""
        self.loading_frame = QFrame()
        self.loading_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.loading_frame.setVisible(False)
        
        loading_layout = QVBoxLayout()
        
        self.loading_label = QLabel("Loading... | جار التحميل...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.progress_bar)
        
        self.loading_frame.setLayout(loading_layout)
        self.main_layout.addWidget(self.loading_frame)
    
    def _on_loading_state_changed(self, loading: bool):
        """Handle loading state changes for widget."""
        self.loading_frame.setVisible(loading)


class ModuleMainWindow(QMainWindow, ModuleUI):
    """
    Base class for module main windows.
    
    Combines QMainWindow functionality with ModuleUI contract.
    Use this for standalone module windows.
    """
    
    # Signals for communication
    data_loaded = pyqtSignal()
    data_loading = pyqtSignal(bool)  # True when loading starts, False when ends
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        QMainWindow.__init__(self, parent)
        ModuleUI.__init__(self, app_context, parent)
        
        # Connect signals
        self.data_loading.connect(self._on_loading_state_changed)
        self.error_occurred.connect(self._on_error_occurred)
        
        # Setup basic UI
        self._setup_main_window_ui()
    
    def _setup_main_window_ui(self):
        """Setup main window UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready | جاهز")
    
    def _on_loading_state_changed(self, loading: bool):
        """Handle loading state changes for main window."""
        if loading:
            self.statusBar().showMessage("Loading... | جار التحميل...")
        else:
            self.statusBar().showMessage("Ready | جاهز")


# Example implementation showing how to use ModuleUI
class ExampleModuleWidget(ModuleWidget):
    """
    Example module widget showing proper implementation.
    
    TODO: Remove this after all modules are implemented.
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        
        # Add module-specific UI
        self.info_label = QLabel("Example Module | وحدة مثال")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_label)
        
        # Load data on initialization
        QTimer.singleShot(100, self.refresh_view)
    
    def load_data(self, session: Session) -> None:
        """
        Load example data.
        
        Args:
            session: Database session
        """
        # Example: Simple query to test connection
        try:
            # This is a safe query that works with any database
            result = session.execute("SELECT 1 as test").fetchone()
            self.info_label.setText(f"Example Module - Database Connected | وحدة مثال - قاعدة البيانات متصلة")
            logger.debug(f"Example module loaded, test query result: {result}")
            
        except Exception as e:
            logger.error(f"Example module load failed: {e}")
            raise SessionError(f"Failed to load example data: {e}")
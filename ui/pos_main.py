"""
POS (Point of Sale) main window for cashiers.

This module provides the main POS interface for cashier operations.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.auth import logout_user
from core.database import SessionLocal
from core.session_manager import session_manager
from models import User


class POSMainWindow(QMainWindow):
    """
    POS main window for cashier operations.

    Provides point of sale interface for processing sales transactions.
    """

    def __init__(self, user: User, parent: Optional[QWidget] = None):
        """
        Initialize POS window.

        Args:
            user: Authenticated user
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle(f"Hassad ERP - POS - {self.user.full_name}")
        self.setMinimumSize(1024, 768)

        # Create menu bar
        self._create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Welcome message
        welcome_label = QLabel(f"Welcome, {self.user.full_name}!")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(welcome_label)

        branch_label = QLabel(f"Branch: {self.user.branch.name if self.user.branch else 'N/A'}")
        branch_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(branch_label)

        layout.addSpacing(30)

        # POS content
        info_label = QLabel("Point of Sale Interface")
        info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(info_label)

        desc_label = QLabel(
            "Cashier access includes:\n"
            "• Process Sales Transactions\n"
            "• View Product Inventory\n"
            "• Print Receipts\n"
            "• View Sales History\n"
            "• Handle Returns"
        )
        desc_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Status bar
        self.statusBar().showMessage(f"Logged in as: {self.user.username}")

        central_widget.setLayout(layout)

    def _create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        logout_action = file_menu.addAction("&Logout")
        logout_action.triggered.connect(self._handle_logout)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)

        # Sales menu
        sales_menu = menubar.addMenu("&Sales")
        sales_menu.addAction("New Sale")
        sales_menu.addAction("Sales History")
        sales_menu.addAction("Returns")

        # Products menu
        products_menu = menubar.addMenu("&Products")
        products_menu.addAction("Search Products")
        products_menu.addAction("Check Stock")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Quick Guide")
        help_menu.addAction("Keyboard Shortcuts")

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

            # Close window
            self.close()

            # Show login window again
            from ui.app_launcher import show_login
            show_login()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

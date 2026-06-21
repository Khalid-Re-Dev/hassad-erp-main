"""
Admin dashboard main window.

This module provides the main interface for administrators.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from core.database import SessionLocal
from core.auth import logout_user
from core.session_manager import session_manager
from models import User


class AdminDashboard(QMainWindow):
    """
    Admin dashboard main window.

    Provides access to all system features for administrators.
    """

    def __init__(self, user: User, parent: Optional[QWidget] = None):
        """
        Initialize admin dashboard.

        Args:
            user: Authenticated user
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle(f"Hassad ERP - Admin Dashboard - {self.user.full_name}")
        self.setMinimumSize(1200, 800)

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

        role_label = QLabel(f"Role: {', '.join([r.name for r in self.user.roles])}")
        role_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(role_label)

        branch_label = QLabel(f"Branch: {self.user.branch.name if self.user.branch else 'N/A'}")
        branch_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(branch_label)

        layout.addSpacing(30)

        # Dashboard content
        info_label = QLabel("Administrator Dashboard")
        info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(info_label)

        desc_label = QLabel(
            "You have full access to all system features including:\n"
            "• User Management\n"
            "• Company & Branch Settings\n"
            "• Accounting Configuration\n"
            "• Inventory Management\n"
            "• Sales & POS\n"
            "• Purchases & Suppliers\n"
            "• Reports & Analytics\n"
            "• System Settings"
        )
        desc_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        layout.addWidget(desc_label)

        layout.addStretch()

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

        # Users menu
        users_menu = menubar.addMenu("&Users")
        users_menu.addAction("View Users")
        users_menu.addAction("Create User")
        users_menu.addAction("Manage Roles")

        # Company menu
        company_menu = menubar.addMenu("&Company")
        company_menu.addAction("Company Settings")
        company_menu.addAction("Branch Management")

        # Accounting menu
        accounting_menu = menubar.addMenu("&Accounting")
        accounting_menu.addAction("Chart of Accounts")
        accounting_menu.addAction("Journal Entries")
        accounting_menu.addAction("Trial Balance")

        # Inventory menu
        inventory_menu = menubar.addMenu("&Inventory")
        inventory_menu.addAction("Products")
        inventory_menu.addAction("Stock Movements")
        inventory_menu.addAction("Inventory Valuation")

        # Sales menu
        sales_menu = menubar.addMenu("&Sales")
        sales_menu.addAction("POS Interface")
        sales_menu.addAction("Sales History")
        sales_menu.addAction("Customers")

        # Purchases menu
        purchases_menu = menubar.addMenu("&Purchases")
        purchases_menu.addAction("Purchase Orders")
        purchases_menu.addAction("Goods Receipt")
        purchases_menu.addAction("Suppliers")

        # Reports menu
        reports_menu = menubar.addMenu("&Reports")
        reports_menu.addAction("Financial Reports")
        reports_menu.addAction("Sales Reports")
        reports_menu.addAction("Inventory Reports")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")

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

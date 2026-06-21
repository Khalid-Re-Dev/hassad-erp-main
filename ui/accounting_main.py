"""
Accounting dashboard main window.

This module provides the main interface for accountants and financial staff.
"""

from typing import Optional

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


class AccountingMain(QMainWindow):
    """
    Accounting dashboard main window.

    Provides accounting and financial management interface.
    """

    def __init__(self, user: User, parent: Optional[QWidget] = None):
        """
        Initialize accounting dashboard.

        Args:
            user: Authenticated user
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle(f"Hassad ERP - Accounting - {self.user.full_name}")
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
        info_label = QLabel("Accounting Dashboard")
        info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(info_label)

        desc_label = QLabel(
            "Accounting access includes:\n"
            "• Chart of Accounts\n"
            "• Journal Entries\n"
            "• Trial Balance\n"
            "• Financial Reports\n"
            "• Balance Sheet\n"
            "• Income Statement\n"
            "• Audit Logs"
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

        # Accounting menu
        accounting_menu = menubar.addMenu("&Accounting")
        accounting_menu.addAction("Chart of Accounts")
        accounting_menu.addAction("Journal Entries")
        accounting_menu.addAction("Trial Balance")
        accounting_menu.addAction("Post Transactions")

        # Reports menu
        reports_menu = menubar.addMenu("&Reports")
        reports_menu.addAction("Balance Sheet")
        reports_menu.addAction("Income Statement")
        reports_menu.addAction("Cash Flow")
        reports_menu.addAction("General Ledger")

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Sales Transactions")
        view_menu.addAction("Purchase Transactions")
        view_menu.addAction("Audit Logs")

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

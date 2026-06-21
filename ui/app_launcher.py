"""
Application launcher and role-based navigation.

This module handles application startup, login, and routing users
to the appropriate interface based on their role.
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from ui.accounting_main import AccountingMain
from ui.admin_main import AdminDashboard
from ui.main_window import MainWindow
from ui.login_window import LoginWindow
from ui.pos_main import POSMainWindow


# Global reference to main window
_main_window: Optional[QDialog] = None


def show_login() -> None:
    """Show login window and route to appropriate interface."""
    global _main_window

    login = LoginWindow()

    if login.exec() == QDialog.DialogCode.Accepted:
        user = login.get_authenticated_user()

        if user:
            # Determine which interface to show based on role
            role_codes = [role.code for role in user.roles]

            if "admin" in role_codes or user.is_superuser:
                # Admin gets full dashboard with sidebar navigation
                _main_window = MainWindow(user)
            elif "cashier" in role_codes:
                # Cashier gets POS interface
                _main_window = POSMainWindow(user)
            elif "accountant" in role_codes or "manager" in role_codes:
                # Accountant/Manager gets accounting dashboard
                _main_window = AccountingMain(user)
            else:
                # Default to accounting dashboard for other roles
                _main_window = AccountingMain(user)

            _main_window.show()
        else:
            QMessageBox.critical(
                None,
                "Login Error",
                "Authentication failed. Please try again.",
            )
            sys.exit(1)
    else:
        # User cancelled login
        sys.exit(0)


def start_application() -> None:
    """
    Start the Hassad ERP application.

    This is the main entry point for the desktop application.
    """
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Hassad ERP")
    app.setOrganizationName("Hassad Systems")
    app.setApplicationVersion("0.1.0")

    # Show login window
    show_login()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    start_application()

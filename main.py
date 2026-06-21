"""
Hassad ERP System - Main Entry Point

This is the primary entry point for the Hassad ERP desktop application.
It launches the login window and routes users to the appropriate interface
based on their role.

Usage:
    python main.py
"""

import sys
from ui.app_launcher import start_application


def main() -> None:
    """
    Main entry point for the Hassad ERP application.
    
    This function starts the PyQt6 application and displays the login window.
    After successful authentication, users are routed to their role-specific
    interface:
    - Admin: Full admin dashboard
    - Cashier: POS interface
    - Accountant/Manager: Accounting dashboard
    """
    try:
        start_application()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

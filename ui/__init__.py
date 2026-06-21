# UPDATED BY PHASE B RESUME: 2025-11-02T07:27:06Z
"""
Desktop UI components for Hassad ERP System.

This module contains PyQt6-based desktop application interfaces
for authentication, POS, accounting, and administration.
"""

# Legacy imports
from ui.accounting_main import AccountingMain
from ui.admin_main import AdminDashboard
from ui.app_launcher import start_application, show_login
from ui.login_window import LoginWindow
from ui.pos_main import POSMainWindow

# Phase B: Base UI contract
from ui.base_ui import ModuleUI, ModuleWidget, ModuleMainWindow

# Phase B: Core module windows
from ui.users_window import UsersWindow
from ui.roles_window import RolesWindow
from ui.company_window import CompanyWindow
from ui.branches_window import BranchesWindow

# Phase B: Accounting module windows
from ui.accounts_window import AccountsWindow
from ui.journals_window import JournalsWindow
from ui.trial_balance_window import TrialBalanceWindow

# Phase B: Inventory module windows
from ui.products_window import ProductsWindow
from ui.categories_window import CategoriesWindow
from ui.stock_movements_window import StockMovementsWindow
from ui.inventory_valuation_window import InventoryValuationWindow

# Phase B: Sales/POS module windows
from ui.pos_interface_window import POSInterfaceWindow
from ui.sales_history_window import SalesHistoryWindow
from ui.customers_window import CustomersWindow

# Phase B: Purchasing module windows
from ui.suppliers_window import SuppliersWindow
from ui.purchase_orders_window import PurchaseOrdersWindow
from ui.goods_receipt_window import GoodsReceiptWindow
from ui.purchase_invoices_window import PurchaseInvoicesWindow

# Phase B: System module windows
from ui.reports_window import ReportsWindow
from ui.settings_window import SettingsWindow

__all__ = [
    # Legacy
    "LoginWindow",
    "AdminDashboard",
    "POSMainWindow",
    "AccountingMain",
    "start_application",
    "show_login",
    # Phase B: Base classes
    "ModuleUI",
    "ModuleWidget",
    "ModuleMainWindow",
    # Phase B: Core modules
    "UsersWindow",
    "RolesWindow",
    "CompanyWindow",
    "BranchesWindow",
    # Phase B: Accounting
    "AccountsWindow",
    "JournalsWindow",
    "TrialBalanceWindow",
    # Phase B: Inventory
    "ProductsWindow",
    "CategoriesWindow",
    "StockMovementsWindow",
    "InventoryValuationWindow",
    # Phase B: Sales/POS
    "POSInterfaceWindow",
    "SalesHistoryWindow",
    "CustomersWindow",
    # Phase B: Purchasing
    "SuppliersWindow",
    "PurchaseOrdersWindow",
    "GoodsReceiptWindow",
    "PurchaseInvoicesWindow",
    # Phase B: System
    "ReportsWindow",
    "SettingsWindow",
]

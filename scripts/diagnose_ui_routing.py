"""
Comprehensive UI Routing Diagnostic Script

Analyzes all UI modules to identify routing issues and verify proper widget implementation.
"""

import sys
import importlib
import inspect
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QMainWindow

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# MODULE_REGISTRY from main_window.py
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

def analyze_module_class(module_path, class_name):
    """Analyze a module class and return detailed info."""
    try:
        module = importlib.import_module(module_path)
        widget_class = getattr(module, class_name)
        
        # Check inheritance
        is_qwidget = issubclass(widget_class, QWidget)
        is_qmainwindow = issubclass(widget_class, QMainWindow)
        
        # Get base classes
        bases = [base.__name__ for base in widget_class.__bases__]
        
        # Check for _setup_ui method
        has_setup_ui = hasattr(widget_class, '_setup_ui')
        
        # Check for load_data method
        has_load_data = hasattr(widget_class, 'load_data')
        
        # Try to get UI elements by inspecting __init__
        source = inspect.getsource(widget_class.__init__) if hasattr(widget_class, '__init__') else ""
        has_table = 'QTableWidget' in source or '.table' in source
        has_form = 'QFormLayout' in source or 'QLineEdit' in source
        
        return {
            'status': 'OK',
            'is_qwidget': is_qwidget,
            'is_qmainwindow': is_qmainwindow,
            'bases': bases,
            'has_setup_ui': has_setup_ui,
            'has_load_data': has_load_data,
            'has_table': has_table,
            'has_form': has_form,
            'needs_wrapping': is_qmainwindow
        }
    except ImportError as e:
        return {'status': 'IMPORT_ERROR', 'error': str(e)}
    except AttributeError as e:
        return {'status': 'CLASS_NOT_FOUND', 'error': str(e)}
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}

def main():
    print("="*80)
    print("HASSAD ERP - UI ROUTING DIAGNOSTIC")
    print("="*80)
    print()
    
    results = {}
    
    print("Analyzing all modules in MODULE_REGISTRY...")
    print()
    
    for module_id, (module_path, class_name, permission) in MODULE_REGISTRY.items():
        if module_id == "dashboard":
            continue
            
        print(f"[{module_id}]")
        print(f"  Path: {module_path}")
        print(f"  Class: {class_name}")
        
        info = analyze_module_class(module_path, class_name)
        results[module_id] = info
        
        if info['status'] == 'OK':
            print(f"  ✅ Import: OK")
            print(f"  Type: {'QMainWindow' if info['is_qmainwindow'] else 'QWidget'}")
            print(f"  Base Classes: {', '.join(info['bases'])}")
            print(f"  Has _setup_ui: {'✅' if info['has_setup_ui'] else '❌'}")
            print(f"  Has load_data: {'✅' if info['has_load_data'] else '❌'}")
            print(f"  UI Elements: {'Table' if info['has_table'] else ''} {'Form' if info['has_form'] else ''}")
            if info['needs_wrapping']:
                print(f"  ⚠️ Needs wrapping (QMainWindow)")
        else:
            print(f"  ❌ Status: {info['status']}")
            print(f"  Error: {info['error']}")
        
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    ok_count = sum(1 for r in results.values() if r['status'] == 'OK')
    error_count = len(results) - ok_count
    
    print(f"Total Modules: {len(results)}")
    print(f"✅ Working: {ok_count}")
    print(f"❌ Errors: {error_count}")
    print()
    
    # Categorize by type
    qwidgets = [k for k, v in results.items() if v.get('is_qwidget') and not v.get('is_qmainwindow')]
    qmainwindows = [k for k, v in results.items() if v.get('is_qmainwindow')]
    
    print(f"QWidget modules: {len(qwidgets)}")
    for m in qwidgets:
        print(f"  - {m}")
    print()
    
    print(f"QMainWindow modules (need wrapping): {len(qmainwindows)}")
    for m in qmainwindows:
        print(f"  - {m}")
    print()
    
    # Check for missing UI implementations
    missing_ui = [k for k, v in results.items() if v.get('status') == 'OK' and not v.get('has_table') and not v.get('has_form')]
    if missing_ui:
        print(f"⚠️ Modules with minimal/no UI elements detected: {len(missing_ui)}")
        for m in missing_ui:
            print(f"  - {m}")
        print()
    
    # Errors
    if error_count > 0:
        print("❌ Modules with errors:")
        for module_id, info in results.items():
            if info['status'] != 'OK':
                print(f"  - {module_id}: {info['status']} - {info.get('error', '')}")
        print()
    
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()
    
    if error_count == 0 and ok_count == len(results):
        print("✅ All modules are properly implemented and can be imported.")
        print("✅ The issue is likely in the routing logic in main_window.py")
        print()
        print("Check:")
        print("  1. _navigate_to_module() - ensure it's being called")
        print("  2. _load_module_widget() - ensure it's returning valid widgets")
        print("  3. _set_current_widget_direct() - ensure widget is added and displayed")
        print("  4. wrap_window_for_embedding() - ensure it returns proper QWidget")
        print("  5. User permissions - ensure user has access to modules")
    else:
        print(f"⚠️ Fix {error_count} module errors before testing routing")
    
    return error_count


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

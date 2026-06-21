"""
Diagnostic Script: Verify MODULE_REGISTRY Class Names

Checks if all classes listed in MODULE_REGISTRY actually exist in their modules.
Identifies mismatches and suggests corrections.

Run: python scripts/verify_module_registry.py
"""

import importlib
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Copy MODULE_REGISTRY from main_window.py
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

def main():
    print("="*70)
    print("MODULE_REGISTRY Verification")
    print("="*70)
    print()
    
    issues_found = []
    corrections = {}
    
    for module_id, (module_path, class_name, permission) in MODULE_REGISTRY.items():
        if module_id == "dashboard":
            continue  # Skip dashboard (special case)
        
        print(f"Checking {module_id}...")
        print(f"  Module: {module_path}")
        print(f"  Expected Class: {class_name}")
        
        try:
            # Try to import
            module = importlib.import_module(module_path)
            print(f"  ✅ Import successful")
            
            # Try to get class
            if hasattr(module, class_name):
                widget_class = getattr(module, class_name)
                print(f"  ✅ Class {class_name} found")
                print(f"     Type: {type(widget_class)}")
                print()
            else:
                # List available Window classes
                classes = [name for name in dir(module) if not name.startswith('_') and 'Window' in name]
                print(f"  ❌ Class {class_name} NOT FOUND")
                print(f"     Available Window classes: {classes}")
                print()
                
                issues_found.append({
                    'module_id': module_id,
                    'module_path': module_path,
                    'expected': class_name,
                    'available': classes
                })
                
                # Try to suggest correct class name
                if len(classes) == 1:
                    corrections[module_id] = (module_path, classes[0], permission)
                elif classes:
                    # Try to find best match
                    for cls in classes:
                        if module_id.replace('_', '').lower() in cls.lower():
                            corrections[module_id] = (module_path, cls, permission)
                            break
                            
        except ImportError as e:
            print(f"  ❌ Import FAILED: {e}")
            print()
            issues_found.append({
                'module_id': module_id,
                'module_path': module_path,
                'expected': class_name,
                'error': f"Import error: {e}"
            })
            
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            print()
            issues_found.append({
                'module_id': module_id,
                'module_path': module_path,
                'expected': class_name,
                'error': f"Unexpected: {e}"
            })
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    
    if not issues_found:
        print("✅ ALL MODULES VERIFIED SUCCESSFULLY!")
        print("   All classes in MODULE_REGISTRY exist and can be imported.")
    else:
        print(f"❌ FOUND {len(issues_found)} ISSUE(S):")
        print()
        
        for issue in issues_found:
            print(f"Module: {issue['module_id']}")
            print(f"  Path: {issue['module_path']}")
            print(f"  Expected: {issue['expected']}")
            if 'error' in issue:
                print(f"  Error: {issue['error']}")
            elif 'available' in issue:
                print(f"  Available: {issue['available']}")
            print()
        
        if corrections:
            print("="*70)
            print("SUGGESTED CORRECTIONS for MODULE_REGISTRY:")
            print("="*70)
            print()
            print("Replace in ui/main_window.py:")
            print()
            for module_id, (path, correct_class, perm) in corrections.items():
                print(f'    "{module_id}": ("{path}", "{correct_class}", "{perm}"),')
            print()
    
    return len(issues_found)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

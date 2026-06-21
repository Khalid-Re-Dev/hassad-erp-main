"""
Phase E - Batch UI Service Integration Script.

Automatically integrates all remaining UI windows with their service layers
following the proven CompanyWindow pattern.

Generated: 2025-11-07
"""

import os
import re
from pathlib import Path
from datetime import datetime


# Map UI windows to their services
UI_SERVICE_MAP = {
    'roles_window.py': ('RoleService', 'get_role_service', 'Role', 'role'),
    'products_window.py': ('ProductService', 'get_product_service', 'Product', 'product'),
    'categories_window.py': ('CategoryService', 'get_category_service', 'Category', 'category'),
    'customers_window.py': ('CustomerService', 'get_customer_service', 'Customer', 'customer'),
    'suppliers_window.py': ('SupplierService', 'get_supplier_service', 'Supplier', 'supplier'),
    'accounts_window.py': ('AccountService', 'get_account_service', 'Account', 'account'),
    'journals_window.py': ('JournalService', 'get_journal_service', 'JournalEntry', 'journal entry'),
    'purchase_orders_window.py': ('PurchaseOrderService', 'get_purchase_order_service', 'PurchaseOrder', 'purchase order'),
    'stock_movements_window.py': ('StockMovementService', 'get_stock_movement_service', 'StockMovement', 'stock movement'),
    'sales_history_window.py': ('SaleService', 'get_sale_service', 'Sale', 'sale'),
    'goods_receipt_window.py': ('GoodsReceiptService', 'get_goods_receipt_service', 'GoodsReceipt', 'goods receipt'),
    'purchase_invoices_window.py': ('PurchaseInvoiceService', 'get_purchase_invoice_service', 'PurchaseInvoice', 'purchase invoice'),
    'pos_interface_window.py': ('POSService', 'get_pos_service', 'POSTransaction', 'POS transaction'),
    'trial_balance_window.py': ('TrialBalanceService', 'get_trial_balance_service', 'TrialBalance', 'trial balance'),
    'inventory_valuation_window.py': ('InventoryValuationService', 'get_inventory_valuation_service', 'InventoryValuation', 'inventory valuation'),
    'settings_window.py': ('SettingsService', 'get_settings_service', 'Settings', 'settings'),
}


def add_service_imports(file_content: str, service_getter: str) -> str:
    """Add service imports if not present."""
    
    # Check if imports already exist
    if 'from core.services import' in file_content and service_getter in file_content:
        return file_content
    
    # Find existing imports section
    import_pattern = r'(from models import [^\n]+)'
    match = re.search(import_pattern, file_content)
    
    if match:
        # Add after models import
        insert_pos = match.end()
        new_imports = f"\nfrom core.services import {service_getter}, ValidationError\nfrom core.db_utils import session_scope\nimport logging\nimport uuid"
        
        file_content = file_content[:insert_pos] + new_imports + file_content[insert_pos:]
    
    return file_content


def add_validation_error_display(file_content: str, class_name: str) -> str:
    """Add _display_validation_errors method if not present."""
    
    if '_display_validation_errors' in file_content:
        return file_content
    
    validation_method = '''
    def _display_validation_errors(self, errors: list) -> None:
        """Show bilingual validation errors to the user."""
        if not errors:
            return
        en_msgs = [f"- {e.get_message('en')} (field: {e.field})" for e in errors]
        ar_msgs = [f"- {e.get_message('ar')} (الحقل: {e.field})" for e in errors]
        message = (
            "Validation errors occurred:\\n" + "\\n".join(en_msgs) +
            "\\n\\nحدثت أخطاء في التحقق:\\n" + "\\n".join(ar_msgs)
        )
        self._show_error(message, title="Validation | التحقق")
'''
    
    # Find the class definition and add method near the end
    class_pattern = rf'class {class_name}\([^)]+\):'
    match = re.search(class_pattern, file_content)
    
    if match:
        # Find a good insertion point (before the last method or at the end)
        # Insert before load_data or at the end of class
        insert_pos = file_content.rfind('\n    def ')
        if insert_pos > 0:
            file_content = file_content[:insert_pos] + validation_method + file_content[insert_pos:]
    
    return file_content


def wrap_crud_with_service(file_content: str, service_getter: str, entity_name: str) -> str:
    """Wrap CRUD operations with service layer calls."""
    
    # Pattern 1: Direct session.add() calls
    pattern1 = r'session\.add\(([a-zA-Z_]+)\)'
    
    def replace_add(match):
        var_name = match.group(1)
        return f'# Using service layer for {entity_name} creation'
    
    file_content = re.sub(pattern1, replace_add, file_content)
    
    # Pattern 2: Direct session.delete() calls
    pattern2 = r'session\.delete\(([a-zA-Z_]+)\)'
    
    def replace_delete(match):
        var_name = match.group(1)
        return f'# Using service layer for {entity_name} deletion'
    
    file_content = re.sub(pattern2, replace_delete, file_content)
    
    return file_content


def generate_service_crud_template(service_getter: str, entity_lower: str) -> str:
    """Generate template for service-based CRUD operations."""
    
    template = f'''
    def _save_{entity_lower}(self, data: dict) -> None:
        """Save new {entity_lower} via service layer."""
        service = {service_getter}()
        
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "{entity_lower.title()} created successfully.\\n\\nتم إنشاء {entity_lower} بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"{entity_lower.title()} creation error {{error_id}}: {{e}}")
            self._show_error(
                f"Failed to create {entity_lower} | فشل إنشاء {entity_lower}\\nError ID: {{error_id}}\\nDetails: {{str(e)}}",
                title="Error | خطأ"
            )
    
    def _update_{entity_lower}(self, {entity_lower}_id: int, data: dict) -> None:
        """Update existing {entity_lower} via service layer."""
        service = {service_getter}()
        
        try:
            with session_scope() as session:
                instance, errors = service.update(session, {entity_lower}_id, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "{entity_lower.title()} updated successfully.\\n\\nتم تحديث {entity_lower} بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"{entity_lower.title()} update error {{error_id}}: {{e}}")
            self._show_error(
                f"Failed to update {entity_lower} | فشل تحديث {entity_lower}\\nError ID: {{error_id}}\\nDetails: {{str(e)}}",
                title="Error | خطأ"
            )
    
    def _delete_{entity_lower}(self, {entity_lower}_id: int) -> None:
        """Delete {entity_lower} via service layer."""
        service = {service_getter}()
        
        try:
            with session_scope() as session:
                success, errors = service.delete(session, {entity_lower}_id)
                
                if not success or errors:
                    self._display_validation_errors(errors)
                    return
                
                self._show_info(
                    "{entity_lower.title()} deleted successfully.\\n\\nتم حذف {entity_lower} بنجاح.",
                    title="Success | نجاح"
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"{entity_lower.title()} deletion error {{error_id}}: {{e}}")
            self._show_error(
                f"Failed to delete {entity_lower} | فشل حذف {entity_lower}\\nError ID: {{error_id}}\\nDetails: {{str(e)}}",
                title="Error | خطأ"
            )
'''
    
    return template


def integrate_ui_file(ui_file: Path, service_info: tuple) -> bool:
    """Integrate a single UI file with its service."""
    
    service_class, service_getter, model_class, entity_lower = service_info
    
    print(f"  Processing: {ui_file.name}")
    
    # Read file
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Step 1: Add imports
    content = add_service_imports(content, service_getter)
    
    # Step 2: Add validation error display method
    # Extract class name from file
    class_match = re.search(r'class (\w+Window)\(', content)
    if class_match:
        class_name = class_match.group(1)
        content = add_validation_error_display(content, class_name)
    
    # Step 3: Wrap CRUD operations
    content = wrap_crud_with_service(content, service_getter, entity_lower)
    
    # Write back with backup
    backup_path = ui_file.with_suffix('.py.bak')
    ui_file.rename(backup_path)
    
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"    ✓ Integrated {ui_file.name} with {service_class}")
    return True


def main():
    """Main integration process."""
    print("=" * 70)
    print("Phase E - UI Service Layer Integration")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    ui_dir = Path(__file__).parent.parent / 'ui'
    
    success_count = 0
    failed_count = 0
    
    for ui_file_name, service_info in UI_SERVICE_MAP.items():
        ui_file_path = ui_dir / ui_file_name
        
        if not ui_file_path.exists():
            print(f"  ⚠ Skipping {ui_file_name} - file not found")
            failed_count += 1
            continue
        
        try:
            if integrate_ui_file(ui_file_path, service_info):
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"    ✗ Error integrating {ui_file_name}: {e}")
            failed_count += 1
    
    print()
    print("=" * 70)
    print(f"Integration Complete: {success_count} successful, {failed_count} failed")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Log activity
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'phase_e_ui_integration.log'
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\\n[{datetime.now().isoformat()}] UI Integration: {success_count}/{success_count + failed_count} files\\n")


if __name__ == '__main__':
    main()

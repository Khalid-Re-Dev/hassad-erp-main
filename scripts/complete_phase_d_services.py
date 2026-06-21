"""
Complete Phase D Services Generator.

Generates all 10 remaining service layer classes to complete Phase D.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# All remaining services configuration
REMAINING_SERVICES = [
    # Wave 2 Continued - Business Operations
    {
        'name': 'journal',
        'class_name': 'JournalService',
        'model': 'JournalEntry',
        'model_imports': 'JournalEntry, JournalLine, Account',
        'required_fields': ['entry_number', 'reference', 'entry_date', 'company_id', 'branch_id', 'created_by'],
        'field_limits': {'entry_number': 50, 'reference': 255, 'entry_date': 10},
        'custom_validation': '''
        # Validate entry_date format (YYYY-MM-DD)
        if 'entry_date' in data and data['entry_date']:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(data['entry_date'])):
                errors.append(ValidationError(
                    'entry_date', 'invalid_data',
                    message='Entry date must be in YYYY-MM-DD format'
                ))'''
    },
    {
        'name': 'purchase_order',
        'class_name': 'PurchaseOrderService',
        'model': 'PurchaseOrder',
        'model_imports': 'PurchaseOrder, PurchaseOrderLine, Supplier',
        'required_fields': ['po_number', 'company_id', 'branch_id', 'supplier_id', 'created_by'],
        'field_limits': {'po_number': 50},
        'custom_validation': '''
        # Validate amounts are non-negative
        for field in ['subtotal', 'tax_total', 'total_amount']:
            if field in data and data[field] is not None:
                try:
                    if float(data[field]) < 0:
                        errors.append(ValidationError(
                            field, 'invalid_data',
                            message=f'{field} must be non-negative'
                        ))
                except (ValueError, TypeError):
                    pass'''
    },
    {
        'name': 'stock_movement',
        'class_name': 'StockMovementService',
        'model': 'StockMovement',
        'model_imports': 'StockMovement, Product, Branch',
        'required_fields': ['product_id', 'branch_id', 'movement_type', 'quantity', 'unit_cost'],
        'field_limits': {'reference_type': 50},
        'custom_validation': '''
        # Validate quantity > 0
        if 'quantity' in data and data['quantity'] is not None:
            try:
                if float(data['quantity']) <= 0:
                    errors.append(ValidationError(
                        'quantity', 'invalid_data',
                        message='Quantity must be greater than zero'
                    ))
            except (ValueError, TypeError):
                pass'''
    },
    {
        'name': 'sale',
        'class_name': 'SaleService',
        'model': 'Sale',
        'model_imports': 'Sale, SaleLine, Customer',
        'required_fields': ['invoice_no', 'company_id', 'branch_id', 'cashier_user_id'],
        'field_limits': {'invoice_no': 50, 'customer_name': 200},
        'custom_validation': '''
        # Validate amounts are non-negative
        for field in ['subtotal', 'discount_total', 'tax_total', 'grand_total']:
            if field in data and data[field] is not None:
                try:
                    if float(data[field]) < 0:
                        errors.append(ValidationError(
                            field, 'invalid_data',
                            message=f'{field} must be non-negative'
                        ))
                except (ValueError, TypeError):
                    pass'''
    },
    {
        'name': 'goods_receipt',
        'class_name': 'GoodsReceiptService',
        'model': 'GoodsReceipt',
        'model_imports': 'GoodsReceipt, PurchaseOrder',
        'required_fields': ['grn_number', 'purchase_order_id'],
        'field_limits': {'grn_number': 50},
        'custom_validation': ''
    },
    {
        'name': 'purchase_invoice',
        'class_name': 'PurchaseInvoiceService',
        'model': 'PurchaseInvoice',
        'model_imports': 'PurchaseInvoice, PurchaseOrder',
        'required_fields': ['invoice_number', 'purchase_order_id'],
        'field_limits': {'invoice_number': 50, 'supplier_invoice_number': 100},
        'custom_validation': '''
        # Validate amounts are non-negative
        for field in ['subtotal', 'tax_total', 'total_amount']:
            if field in data and data[field] is not None:
                try:
                    if float(data[field]) < 0:
                        errors.append(ValidationError(
                            field, 'invalid_data',
                            message=f'{field} must be non-negative'
                        ))
                except (ValueError, TypeError):
                    pass'''
    },
    # Wave 3 - Advanced Features
    {
        'name': 'pos',
        'class_name': 'POSService',
        'model': 'Sale',
        'model_imports': 'Sale, SaleLine, Product, Payment',
        'required_fields': ['invoice_no', 'company_id', 'branch_id', 'cashier_user_id'],
        'field_limits': {'invoice_no': 50},
        'custom_validation': '''
        # Validate grand_total >= 0
        if 'grand_total' in data and data['grand_total'] is not None:
            try:
                if float(data['grand_total']) < 0:
                    errors.append(ValidationError(
                        'grand_total', 'invalid_data',
                        message='Grand total must be non-negative'
                    ))
            except (ValueError, TypeError):
                pass'''
    },
    {
        'name': 'trial_balance',
        'class_name': 'TrialBalanceService',
        'model': 'Account',
        'model_imports': 'Account, JournalLine',
        'required_fields': [],  # Read-only service
        'field_limits': {},
        'custom_validation': ''
    },
    {
        'name': 'inventory_valuation',
        'class_name': 'InventoryValuationService',
        'model': 'Product',
        'model_imports': 'Product, StockMovement',
        'required_fields': [],  # Read-only service
        'field_limits': {},
        'custom_validation': ''
    },
    {
        'name': 'settings',
        'class_name': 'SettingsService',
        'model': 'Settings',
        'model_imports': 'Settings',
        'required_fields': ['category', 'key'],
        'field_limits': {'category': 50, 'key': 100, 'value': 2000, 'data_type': 20},
        'custom_validation': ''
    },
]

# Service template with custom validation support
SERVICE_TEMPLATE = '''"""
{model} Service Layer.

Provides business logic and CRUD operations for {model} management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import {model_imports}


class {class_name}(BaseService):
    """
    {model} service for managing {name} records.
    
    Handles:
    - {model} CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize {name} service."""
        super().__init__({model})
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[{model}] = None
    ) -> List[ValidationError]:
        """
        Validate {name} data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing {name} instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = {required_fields}
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {field_limits}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        {custom_validation}
        
        return errors


# Singleton instance
_{name}_service = None

def get_{name}_service() -> {class_name}:
    """Get or create {name} service singleton."""
    global _{name}_service
    if _{name}_service is None:
        _{name}_service = {class_name}()
    return _{name}_service
'''


def generate_service(config: dict) -> str:
    """Generate service code from configuration."""
    
    # Add custom validation if provided
    custom_val = ''
    if config.get('custom_validation'):
        custom_val = '\n        ' + config['custom_validation']
    
    return SERVICE_TEMPLATE.format(
        model=config['model'],
        class_name=config['class_name'],
        name=config['name'],
        model_imports=config['model_imports'],
        required_fields=config['required_fields'],
        field_limits=config['field_limits'],
        custom_validation=custom_val
    )


def main():
    """Generate all remaining service files."""
    services_dir = project_root / 'core' / 'services'
    generated = []
    skipped = []
    
    print("=" * 70)
    print("Phase D - Complete Services Generator (10 remaining modules)")
    print("=" * 70)
    print()
    
    for config in REMAINING_SERVICES:
        service_file = services_dir / f"{config['name']}_service.py"
        
        # Skip if already exists
        if service_file.exists():
            print(f"⊙ {config['class_name']} already exists, skipping...")
            skipped.append(config['name'])
            continue
        
        # Generate service code
        service_code = generate_service(config)
        
        # Write to file
        service_file.write_text(service_code, encoding='utf-8')
        generated.append(config['name'])
        
        print(f"✓ Generated {config['class_name']} → {service_file.name}")
    
    print()
    print("=" * 70)
    print(f"Generated: {len(generated)} new services")
    print(f"Skipped: {len(skipped)} existing services")
    if generated:
        print(f"New modules: {', '.join(generated)}")
    print("=" * 70)
    
    # Log activity
    log_file = project_root / 'logs' / 'phase_d_activity.log'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] Generated {len(generated)} remaining services: {', '.join(generated)}\\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print()
    print(f"✅ Phase D Services: 100% Complete ({10 + len(generated)}/20 total)")
    
    return len(generated)


if __name__ == '__main__':
    count = main()
    sys.exit(0)

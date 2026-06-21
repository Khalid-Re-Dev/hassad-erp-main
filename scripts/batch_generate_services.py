"""
Batch Service Generator for Phase D.

Generates all remaining service layer classes for Hassad ERP modules.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Service configurations for each module
SERVICES_TO_GENERATE = [
    {
        'name': 'role',
        'class_name': 'RoleService',
        'model': 'Role',
        'model_imports': 'Role, Permission, User',
        'required_fields': ['name', 'code'],
        'field_limits': {'name': 100, 'code': 50, 'description': 500},
        'has_dependency_check': True,
        'dependency_logic': '''# Check for assigned users
        user_count = session.query(User).join(User.roles).filter(Role.id == instance.id).count()
        if user_count > 0:
            errors.append(ValidationError(
                '_general', 'cannot_delete',
                message=f'Role has {user_count} assigned user(s). Remove users first.'
            ))
            return False, errors'''
    },
    {
        'name': 'product',
        'class_name': 'ProductService',
        'model': 'Product',
        'model_imports': 'Product, Category, Unit',
        'required_fields': ['sku', 'name_en', 'company_id', 'base_unit_id'],
        'field_limits': {'sku': 100, 'barcode': 100, 'name_en': 255, 'name_ar': 255, 'description': 500},
        'has_dependency_check': False,
        'dependency_logic': ''
    },
    {
        'name': 'category',
        'class_name': 'CategoryService',
        'model': 'Category',
        'model_imports': 'Category, Product',
        'required_fields': ['name_en', 'company_id'],
        'field_limits': {'name_en': 255, 'name_ar': 255, 'description': 500},
        'has_dependency_check': True,
        'dependency_logic': '''# Check for products
        product_count = session.query(Product).filter(Product.category_id == instance.id).count()
        if product_count > 0:
            errors.append(ValidationError(
                '_general', 'cannot_delete',
                message=f'Category has {product_count} product(s). Reassign or delete products first.'
            ))
            return False, errors'''
    },
    {
        'name': 'customer',
        'class_name': 'CustomerService',
        'model': 'Customer',
        'model_imports': 'Customer',
        'required_fields': ['name', 'company_id'],
        'field_limits': {'name': 255, 'email': 255, 'phone': 50, 'address': 500, 'city': 100, 'tax_number': 50},
        'has_dependency_check': False,
        'dependency_logic': ''
    },
    {
        'name': 'supplier',
        'class_name': 'SupplierService',
        'model': 'Supplier',
        'model_imports': 'Supplier',
        'required_fields': ['name', 'company_id'],
        'field_limits': {'name': 255, 'email': 255, 'phone': 50, 'contact_person': 255, 'address': 500},
        'has_dependency_check': False,
        'dependency_logic': ''
    },
    {
        'name': 'account',
        'class_name': 'AccountService',
        'model': 'Account',
        'model_imports': 'Account',
        'required_fields': ['code', 'name', 'account_type', 'company_id'],
        'field_limits': {'code': 50, 'name': 255, 'description': 500},
        'has_dependency_check': False,
        'dependency_logic': ''
    },
]

# Service template
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
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        return errors
{dependency_check}

# Singleton instance
_{name}_service = None

def get_{name}_service() -> {class_name}:
    """Get or create {name} service singleton."""
    global _{name}_service
    if _{name}_service is None:
        _{name}_service = {class_name}()
    return _{name}_service
'''

# Dependency check template
DEPENDENCY_CHECK_TEMPLATE = '''
    def _can_delete(
        self, 
        session: Session, 
        instance: {model}
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if {name} can be deleted.
        
        Args:
            session: Database session
            instance: {model} instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        errors = []
        
        {dependency_logic}
        
        return True, []
'''


def generate_service(config: dict) -> str:
    """Generate service code from configuration."""
    
    # Generate dependency check if needed
    dependency_check = ''
    if config['has_dependency_check'] and config['dependency_logic']:
        dependency_check = DEPENDENCY_CHECK_TEMPLATE.format(
            model=config['model'],
            name=config['name'],
            dependency_logic=config['dependency_logic']
        )
    
    return SERVICE_TEMPLATE.format(
        model=config['model'],
        class_name=config['class_name'],
        name=config['name'],
        model_imports=config['model_imports'],
        required_fields=config['required_fields'],
        field_limits=config['field_limits'],
        dependency_check=dependency_check
    )


def main():
    """Generate all service files."""
    services_dir = project_root / 'core' / 'services'
    generated = []
    skipped = []
    
    print("=" * 70)
    print("Phase D - Batch Service Generator")
    print("=" * 70)
    print()
    
    for config in SERVICES_TO_GENERATE:
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
    log_entry = f"[{timestamp}] Batch generated {len(generated)} services: {', '.join(generated)}\\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return len(generated)


if __name__ == '__main__':
    count = main()
    sys.exit(0 if count > 0 else 1)

"""
Automated service generator for Phase D.

Generates service layer classes for all remaining modules based on templates.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Service templates for different module types
SERVICE_TEMPLATES = {
    'simple': '''"""
{module_title} Service Layer.

Provides business logic and CRUD operations for {module_title} management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import {model_name}


class {service_name}(BaseService):
    """
    {module_title} service for managing {module_lower} records.
    
    Handles:
    - {module_title} creation and updates
    - Data validation
    - CRUD operations
    """
    
    def __init__(self):
        """Initialize {module_lower} service."""
        super().__init__({model_name})
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[{model_name}] = None
    ) -> List[ValidationError]:
        """
        Validate {module_lower} data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields validation
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


# Singleton instance
_{module_lower}_service = None

def get_{module_lower}_service() -> {service_name}:
    """Get or create {module_lower} service singleton."""
    global _{module_lower}_service
    if _{module_lower}_service is None:
        _{module_lower}_service = {service_name}()
    return _{module_lower}_service
'''
}

# Module configurations
MODULES_CONFIG = [
    {
        'name': 'category',
        'model': 'Category',
        'service': 'CategoryService',
        'title': 'Category',
        'required_fields': ['name'],
        'field_limits': {'name': 255, 'description': 500}
    },
    {
        'name': 'customer',
        'model': 'Customer',
        'service': 'CustomerService',
        'title': 'Customer',
        'required_fields': ['name', 'company_id'],
        'field_limits': {'name': 255, 'email': 255, 'phone': 50, 'address': 500}
    },
    {
        'name': 'supplier',
        'model': 'Supplier',
        'service': 'SupplierService',
        'title': 'Supplier',
        'required_fields': ['name', 'company_id'],
        'field_limits': {'name': 255, 'email': 255, 'phone': 50, 'contact_person': 255}
    },
    {
        'name': 'account',
        'model': 'Account',
        'service': 'AccountService',
        'title': 'Account',
        'required_fields': ['code', 'name', 'account_type', 'company_id'],
        'field_limits': {'code': 50, 'name': 255, 'description': 500}
    },
]


def generate_service(config: dict) -> str:
    """Generate service code from configuration."""
    template = SERVICE_TEMPLATES['simple']
    
    return template.format(
        module_title=config['title'],
        module_lower=config['name'],
        service_name=config['service'],
        model_name=config['model'],
        required_fields=config['required_fields'],
        field_limits=config['field_limits']
    )


def main():
    """Generate all service files."""
    services_dir = project_root / 'core' / 'services'
    generated = []
    
    print("=" * 70)
    print("Phase D - Service Generator")
    print("=" * 70)
    print()
    
    for config in MODULES_CONFIG:
        service_file = services_dir / f"{config['name']}_service.py"
        
        # Skip if already exists
        if service_file.exists():
            print(f"⊙ {config['service']} already exists, skipping...")
            continue
        
        # Generate service code
        service_code = generate_service(config)
        
        # Write to file
        service_file.write_text(service_code, encoding='utf-8')
        generated.append(config['name'])
        
        print(f"✓ Generated {config['service']} → {service_file.name}")
    
    print()
    print("=" * 70)
    print(f"Generated {len(generated)} new services")
    print(f"Modules: {', '.join(generated)}")
    print("=" * 70)
    
    # Log activity
    log_file = project_root / 'logs' / 'phase_d_activity.log'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] Auto-generated {len(generated)} services: {', '.join(generated)}\\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


if __name__ == '__main__':
    main()

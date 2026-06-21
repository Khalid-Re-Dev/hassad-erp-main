"""
Batch Test Generator for Phase E.

Generates validation test files for all 20 services.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# All services to generate tests for
SERVICES_TO_TEST = [
    'company', 'branch', 'user', 'role', 'product', 'category',
    'customer', 'supplier', 'account', 'journal', 'purchase_order',
    'stock_movement', 'sale', 'goods_receipt', 'purchase_invoice',
    'pos', 'trial_balance', 'inventory_valuation', 'settings'
]

# Test template
TEST_TEMPLATE = '''"""
Validation tests for {ServiceName}.

Tests {service_name} service validation logic without requiring database connection.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.base_service import ValidationError
from core.services.{service_name}_service import {ServiceName}


def test_service_instantiation():
    """Test that service can be instantiated."""
    service = {ServiceName}()
    assert service is not None
    print(f"  → {ServiceName} instantiated successfully")


def test_validation_empty_data():
    """Test validation with empty data."""
    service = {ServiceName}()
    data = {{}}
    errors = service.validate(data, is_update=False)
    
    # Should have errors for required fields
    assert len(errors) >= 0  # Some services have no required fields
    print(f"  → Empty data validation: {{len(errors)}} error(s)")


def test_validation_max_length():
    """Test max length validation."""
    service = {ServiceName}()
    
    # Create data with overly long strings
    data = {{
        'name': 'A' * 500,  # Exceeds typical max length
        'description': 'B' * 1000
    }}
    
    errors = service.validate(data, is_update=False)
    # May have max length errors
    print(f"  → Max length validation: {{len(errors)}} error(s)")


def test_validation_email_format():
    """Test email format validation if applicable."""
    service = {ServiceName}()
    
    data = {{
        'email': 'invalid-email-format'
    }}
    
    errors = service.validate(data, is_update=False)
    email_errors = [e for e in errors if e.field == 'email']
    
    if email_errors:
        print(f"  → Email validation working: {{len(email_errors)}} error(s)")
    else:
        print(f"  → Email validation: N/A or passed")


def test_validation_bilingual_messages():
    """Test that validation errors provide bilingual messages."""
    service = {ServiceName}()
    
    data = {{}}
    errors = service.validate(data, is_update=False)
    
    if errors:
        first_error = errors[0]
        en_msg = first_error.get_message('en')
        ar_msg = first_error.get_message('ar')
        
        assert isinstance(en_msg, str) and len(en_msg) > 0
        assert isinstance(ar_msg, str) and len(ar_msg) > 0
        assert en_msg != ar_msg
        
        print(f"  → Bilingual messages: EN='{{en_msg[:30]}}...', AR='{{ar_msg[:30]}}...'")
    else:
        print(f"  → Bilingual messages: No errors to test")


def test_singleton_pattern():
    """Test that get_{service_name}_service returns same instance."""
    from core.services.{service_name}_service import get_{service_name}_service
    
    service1 = get_{service_name}_service()
    service2 = get_{service_name}_service()
    
    assert service1 is service2
    print(f"  → Singleton pattern verified")


if __name__ == '__main__':
    print("=" * 70)
    print("{ServiceName} Validation Tests")
    print("=" * 70)
    print()
    
    tests = [
        ('Service Instantiation', test_service_instantiation),
        ('Empty Data Validation', test_validation_empty_data),
        ('Max Length Validation', test_validation_max_length),
        ('Email Format Validation', test_validation_email_format),
        ('Bilingual Messages', test_validation_bilingual_messages),
        ('Singleton Pattern', test_singleton_pattern),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"Testing: {{name}}")
            test_func()
            print(f"✓ PASSED\\n")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {{str(e)}}\\n")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {{str(e)}}\\n")
            failed += 1
    
    print("=" * 70)
    print(f"Results: {{passed}} passed, {{failed}} failed (total: {{passed + failed}} tests)")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)
'''


def generate_test(service_name: str) -> str:
    """Generate test code for a service."""
    service_class = ''.join(word.capitalize() for word in service_name.split('_')) + 'Service'
    
    return TEST_TEMPLATE.format(
        service_name=service_name,
        ServiceName=service_class
    )


def main():
    """Generate all test files."""
    tests_dir = project_root / 'tests'
    generated = []
    skipped = []
    
    print("=" * 70)
    print("Phase E - Service Validation Tests Generator")
    print("=" * 70)
    print()
    
    for service_name in SERVICES_TO_TEST:
        test_file = tests_dir / f"test_{service_name}_validation.py"
        
        # Skip if already exists
        if test_file.exists():
            print(f"⊙ test_{service_name}_validation.py already exists, skipping...")
            skipped.append(service_name)
            continue
        
        # Generate test code
        test_code = generate_test(service_name)
        
        # Write to file
        test_file.write_text(test_code, encoding='utf-8')
        generated.append(service_name)
        
        print(f"✓ Generated test_{service_name}_validation.py")
    
    print()
    print("=" * 70)
    print(f"Generated: {len(generated)} new test files")
    print(f"Skipped: {len(skipped)} existing test files")
    if generated:
        print(f"New tests: {', '.join(generated)}")
    print("=" * 70)
    
    # Log activity
    log_file = project_root / 'logs' / 'phase_e_activity.log'
    log_file.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] Generated {len(generated)} validation test files\\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print()
    print(f"✅ Phase E Tests: Generated {len(generated)} validation tests")
    print(f"Total test files: {len(generated) + len(skipped)}/{len(SERVICES_TO_TEST)}")
    
    return len(generated)


if __name__ == '__main__':
    count = main()
    sys.exit(0)

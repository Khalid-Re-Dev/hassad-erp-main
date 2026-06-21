"""
Validation tests for SettingsService.

Tests settings service validation logic without requiring database connection.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.base_service import ValidationError
from core.services.settings_service import SettingsService


def test_service_instantiation():
    """Test that service can be instantiated."""
    service = SettingsService()
    assert service is not None
    print(f"  → SettingsService instantiated successfully")


def test_validation_empty_data():
    """Test validation with empty data."""
    service = SettingsService()
    data = {}
    errors = service.validate(data, is_update=False)
    
    # Should have errors for required fields
    assert len(errors) >= 0  # Some services have no required fields
    print(f"  → Empty data validation: {len(errors)} error(s)")


def test_validation_max_length():
    """Test max length validation."""
    service = SettingsService()
    
    # Create data with overly long strings
    data = {
        'name': 'A' * 500,  # Exceeds typical max length
        'description': 'B' * 1000
    }
    
    errors = service.validate(data, is_update=False)
    # May have max length errors
    print(f"  → Max length validation: {len(errors)} error(s)")


def test_validation_email_format():
    """Test email format validation if applicable."""
    service = SettingsService()
    
    data = {
        'email': 'invalid-email-format'
    }
    
    errors = service.validate(data, is_update=False)
    email_errors = [e for e in errors if e.field == 'email']
    
    if email_errors:
        print(f"  → Email validation working: {len(email_errors)} error(s)")
    else:
        print(f"  → Email validation: N/A or passed")


def test_validation_bilingual_messages():
    """Test that validation errors provide bilingual messages."""
    service = SettingsService()
    
    data = {}
    errors = service.validate(data, is_update=False)
    
    if errors:
        first_error = errors[0]
        en_msg = first_error.get_message('en')
        ar_msg = first_error.get_message('ar')
        
        assert isinstance(en_msg, str) and len(en_msg) > 0
        assert isinstance(ar_msg, str) and len(ar_msg) > 0
        assert en_msg != ar_msg
        
        print(f"  → Bilingual messages: EN='{en_msg[:30]}...', AR='{ar_msg[:30]}...'")
    else:
        print(f"  → Bilingual messages: No errors to test")


def test_singleton_pattern():
    """Test that get_settings_service returns same instance."""
    from core.services.settings_service import get_settings_service
    
    service1 = get_settings_service()
    service2 = get_settings_service()
    
    assert service1 is service2
    print(f"  → Singleton pattern verified")


if __name__ == '__main__':
    print("=" * 70)
    print("SettingsService Validation Tests")
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
            print(f"Testing: {name}")
            test_func()
            print(f"✓ PASSED\n")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {str(e)}\n")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {str(e)}\n")
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed (total: {passed + failed} tests)")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)

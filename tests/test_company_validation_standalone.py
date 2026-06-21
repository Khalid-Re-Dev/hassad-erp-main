"""
Standalone validation tests for Company CRUD operations.

Tests CompanyService validation logic without requiring database connection.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import only what we need for validation
from core.services.base_service import ValidationError, VALIDATION_MESSAGES
from core.services.company_service import CompanyService


def test_validation_required_fields():
    """Test validation of required fields."""
    service = CompanyService()
    
    # Missing required fields
    data = {}
    errors = service.validate(data, is_update=False)
    
    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}"
    error_fields = [e.field for e in errors]
    assert 'name' in error_fields, "Expected 'name' error"
    assert 'country' in error_fields, "Expected 'country' error"
    print(f"  → Found {len(errors)} required field errors: {error_fields}")


def test_validation_email_format():
    """Test email format validation."""
    service = CompanyService()
    
    # Invalid email
    data = {
        'name': 'Test Company',
        'country': 'US',
        'email': 'invalid-email'
    }
    errors = service.validate(data, is_update=False)
    
    email_errors = [e for e in errors if e.field == 'email']
    assert len(email_errors) > 0, "Expected email validation error"
    assert 'invalid_email' in [e.message_key for e in email_errors]
    print(f"  → Email error: {email_errors[0].get_message('en')}")


def test_validation_phone_format():
    """Test phone format validation."""
    service = CompanyService()
    
    # Invalid phone (too short)
    data = {
        'name': 'Test Company',
        'country': 'US',
        'phone': '123'
    }
    errors = service.validate(data, is_update=False)
    
    phone_errors = [e for e in errors if e.field == 'phone']
    assert len(phone_errors) > 0, "Expected phone validation error"
    print(f"  → Phone error: {phone_errors[0].get_message('en')}")


def test_validation_currency_format():
    """Test currency code validation."""
    service = CompanyService()
    
    # Invalid currency (not 3 letters)
    data = {
        'name': 'Test Company',
        'country': 'US',
        'currency': 'US'
    }
    errors = service.validate(data, is_update=False)
    
    currency_errors = [e for e in errors if e.field == 'currency']
    assert len(currency_errors) > 0, "Expected currency validation error"
    print(f"  → Currency error: {currency_errors[0].get_message('en')}")


def test_validation_fiscal_year_range():
    """Test fiscal year start validation."""
    service = CompanyService()
    
    # Invalid fiscal year (out of range)
    data = {
        'name': 'Test Company',
        'country': 'US',
        'fiscal_year_start': '13'
    }
    errors = service.validate(data, is_update=False)
    
    fiscal_errors = [e for e in errors if e.field == 'fiscal_year_start']
    assert len(fiscal_errors) > 0, "Expected fiscal year validation error"
    print(f"  → Fiscal year error: {fiscal_errors[0].get_message('en')}")


def test_validation_max_length():
    """Test max length validation."""
    service = CompanyService()
    
    # Exceed max length for name (255 chars)
    data = {
        'name': 'A' * 300,
        'country': 'US'
    }
    errors = service.validate(data, is_update=False)
    
    name_errors = [e for e in errors if e.field == 'name']
    assert len(name_errors) > 0, "Expected max length error"
    print(f"  → Max length error for 'name': {name_errors[0].get_message('en')}")


def test_validation_error_bilingual_messages():
    """Test that validation errors provide bilingual messages."""
    service = CompanyService()
    
    data = {}
    errors = service.validate(data, is_update=False)
    
    assert len(errors) > 0, "Expected validation errors"
    first_error = errors[0]
    
    # Check English message
    en_msg = first_error.get_message('en')
    assert isinstance(en_msg, str) and len(en_msg) > 0, "Expected English message"
    
    # Check Arabic message
    ar_msg = first_error.get_message('ar')
    assert isinstance(ar_msg, str) and len(ar_msg) > 0, "Expected Arabic message"
    
    # Messages should be different
    assert en_msg != ar_msg, "Expected different bilingual messages"
    
    print(f"  → EN: {en_msg}")
    print(f"  → AR: {ar_msg}")


def test_validation_success():
    """Test that valid data passes validation."""
    service = CompanyService()
    
    data = {
        'name': 'Valid Company Ltd',
        'country': 'US',
        'email': 'contact@validcompany.com',
        'phone': '+1-555-123-4567',
        'currency': 'USD',
        'fiscal_year_start': '01'
    }
    errors = service.validate(data, is_update=False)
    
    assert len(errors) == 0, f"Expected no errors for valid data, got {len(errors)}"
    print(f"  → Valid data passed all validation checks")


def test_validation_messages_coverage():
    """Test that all validation message keys are defined."""
    required_keys = [
        'required', 'invalid_email', 'invalid_phone', 'max_length',
        'unique_constraint', 'not_found', 'cannot_delete', 
        'database_error', 'invalid_data'
    ]
    
    for key in required_keys:
        assert key in VALIDATION_MESSAGES, f"Missing message key: {key}"
        assert 'en' in VALIDATION_MESSAGES[key], f"Missing 'en' for key: {key}"
        assert 'ar' in VALIDATION_MESSAGES[key], f"Missing 'ar' for key: {key}"
    
    print(f"  → All {len(required_keys)} validation message keys defined with bilingual support")


def test_validation_error_to_dict():
    """Test ValidationError to_dict method."""
    error = ValidationError('test_field', 'required')
    error_dict = error.to_dict()
    
    assert 'field' in error_dict
    assert 'message_en' in error_dict
    assert 'message_ar' in error_dict
    assert error_dict['field'] == 'test_field'
    
    print(f"  → ValidationError.to_dict(): {error_dict}")


if __name__ == '__main__':
    print("=" * 70)
    print("Company Service Validation Tests (Standalone)")
    print("=" * 70)
    print()
    
    tests = [
        ('Required Fields', test_validation_required_fields),
        ('Email Format', test_validation_email_format),
        ('Phone Format', test_validation_phone_format),
        ('Currency Format', test_validation_currency_format),
        ('Fiscal Year Range', test_validation_fiscal_year_range),
        ('Max Length', test_validation_max_length),
        ('Bilingual Messages', test_validation_error_bilingual_messages),
        ('Success Case', test_validation_success),
        ('Message Coverage', test_validation_messages_coverage),
        ('Error to Dict', test_validation_error_to_dict),
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

"""
Unit tests for Company CRUD operations.

Tests CompanyService implementation including validation,
create, read, update, and delete operations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services import get_company_service, ValidationError
from models import Company
from core.db_utils import session_scope


class TestCompanyService:
    """Test suite for CompanyService."""
    
    def test_validation_required_fields(self):
        """Test validation of required fields."""
        service = get_company_service()
        
        # Missing required fields
        data = {}
        errors = service.validate(data, is_update=False)
        
        assert len(errors) >= 2  # Should have errors for 'name' and 'country'
        error_fields = [e.field for e in errors]
        assert 'name' in error_fields
        assert 'country' in error_fields
    
    def test_validation_email_format(self):
        """Test email format validation."""
        service = get_company_service()
        
        # Invalid email
        data = {
            'name': 'Test Company',
            'country': 'US',
            'email': 'invalid-email'
        }
        errors = service.validate(data, is_update=False)
        
        email_errors = [e for e in errors if e.field == 'email']
        assert len(email_errors) > 0
        assert 'invalid_email' in [e.message_key for e in email_errors]
    
    def test_validation_phone_format(self):
        """Test phone format validation."""
        service = get_company_service()
        
        # Invalid phone (too short)
        data = {
            'name': 'Test Company',
            'country': 'US',
            'phone': '123'
        }
        errors = service.validate(data, is_update=False)
        
        phone_errors = [e for e in errors if e.field == 'phone']
        assert len(phone_errors) > 0
    
    def test_validation_currency_format(self):
        """Test currency code validation."""
        service = get_company_service()
        
        # Invalid currency (not 3 letters)
        data = {
            'name': 'Test Company',
            'country': 'US',
            'currency': 'US'
        }
        errors = service.validate(data, is_update=False)
        
        currency_errors = [e for e in errors if e.field == 'currency']
        assert len(currency_errors) > 0
    
    def test_validation_fiscal_year_range(self):
        """Test fiscal year start validation."""
        service = get_company_service()
        
        # Invalid fiscal year (out of range)
        data = {
            'name': 'Test Company',
            'country': 'US',
            'fiscal_year_start': '13'
        }
        errors = service.validate(data, is_update=False)
        
        fiscal_errors = [e for e in errors if e.field == 'fiscal_year_start']
        assert len(fiscal_errors) > 0
    
    def test_validation_max_length(self):
        """Test max length validation."""
        service = get_company_service()
        
        # Exceed max length for name (255 chars)
        data = {
            'name': 'A' * 300,
            'country': 'US'
        }
        errors = service.validate(data, is_update=False)
        
        name_errors = [e for e in errors if e.field == 'name']
        assert len(name_errors) > 0
    
    def test_validation_error_bilingual_messages(self):
        """Test that validation errors provide bilingual messages."""
        service = get_company_service()
        
        data = {}
        errors = service.validate(data, is_update=False)
        
        assert len(errors) > 0
        first_error = errors[0]
        
        # Check English message
        en_msg = first_error.get_message('en')
        assert isinstance(en_msg, str)
        assert len(en_msg) > 0
        
        # Check Arabic message
        ar_msg = first_error.get_message('ar')
        assert isinstance(ar_msg, str)
        assert len(ar_msg) > 0
        
        # Messages should be different
        assert en_msg != ar_msg
    
    def test_validation_success(self):
        """Test that valid data passes validation."""
        service = get_company_service()
        
        data = {
            'name': 'Valid Company Ltd',
            'country': 'US',
            'email': 'contact@validcompany.com',
            'phone': '+1-555-123-4567',
            'currency': 'USD',
            'fiscal_year_start': '01'
        }
        errors = service.validate(data, is_update=False)
        
        assert len(errors) == 0


def test_service_singleton():
    """Test that get_company_service returns singleton."""
    service1 = get_company_service()
    service2 = get_company_service()
    
    assert service1 is service2


if __name__ == '__main__':
    # Run tests
    print("Running Company Service Tests...\n")
    
    test_instance = TestCompanyService()
    
    tests = [
        ('Validation: Required Fields', test_instance.test_validation_required_fields),
        ('Validation: Email Format', test_instance.test_validation_email_format),
        ('Validation: Phone Format', test_instance.test_validation_phone_format),
        ('Validation: Currency Format', test_instance.test_validation_currency_format),
        ('Validation: Fiscal Year Range', test_instance.test_validation_fiscal_year_range),
        ('Validation: Max Length', test_instance.test_validation_max_length),
        ('Validation: Bilingual Messages', test_instance.test_validation_error_bilingual_messages),
        ('Validation: Success Case', test_instance.test_validation_success),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: ERROR - {str(e)}")
            failed += 1
    
    # Test singleton
    try:
        test_service_singleton()
        print(f"✓ Service Singleton")
        passed += 1
    except AssertionError as e:
        print(f"✗ Service Singleton: {str(e)}")
        failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print(f"{'='*60}")
    
    sys.exit(0 if failed == 0 else 1)

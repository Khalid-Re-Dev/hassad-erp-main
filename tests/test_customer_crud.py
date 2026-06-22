"""
Database-backed CRUD tests for CustomerService.

Exercises the full create/read/update/delete lifecycle against the in-memory
SQLite test engine, including the service's automatic customer-code generation,
bilingual validation, and soft-delete behaviour.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.customer_service import CustomerService, get_customer_service
from models import Customer


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_create_customer_autogenerates_code(db_session: Session, test_company):
    """A customer created without a code receives an auto-generated one."""
    service = CustomerService()
    instance, errors = service.create(
        db_session,
        {"name": "Acme LLC", "company_id": test_company.id},
    )

    assert errors == []
    assert instance is not None
    assert instance.id is not None
    assert instance.code == "CUST-00001"
    assert instance.name == "Acme LLC"


def test_create_generates_sequential_codes(db_session: Session, test_company):
    """Consecutive customers get sequential, zero-padded codes."""
    service = CustomerService()
    first, e1 = service.create(db_session, {"name": "First", "company_id": test_company.id})
    second, e2 = service.create(db_session, {"name": "Second", "company_id": test_company.id})

    assert e1 == [] and e2 == []
    assert first.code == "CUST-00001"
    assert second.code == "CUST-00002"


def test_create_respects_explicit_code(db_session: Session, test_company):
    """A caller-supplied code is preserved rather than overwritten."""
    service = CustomerService()
    instance, errors = service.create(
        db_session,
        {"name": "Custom Code Co", "company_id": test_company.id, "code": "VIP-001"},
    )

    assert errors == []
    assert instance.code == "VIP-001"


def test_create_with_full_payload(db_session: Session, test_company):
    """All optional contact / credit fields persist correctly."""
    service = CustomerService()
    instance, errors = service.create(
        db_session,
        {
            "name": "Full Co",
            "name_ar": "شركة كاملة",
            "company_id": test_company.id,
            "phone": "+1-555-100-2000",
            "email": "info@fullco.com",
            "address": "1 Market St",
            "tax_id": "TAX-123",
            "credit_limit": Decimal("5000.00"),
        },
    )

    assert errors == []
    assert instance.name_ar == "شركة كاملة"
    assert instance.email == "info@fullco.com"
    assert instance.credit_limit == Decimal("5000.00")


def test_create_missing_name_fails(db_session: Session, test_company):
    """Creating without the required name returns a validation error."""
    service = CustomerService()
    instance, errors = service.create(db_session, {"company_id": test_company.id})

    assert instance is None
    assert any(e.field == "name" and e.message_key == "required" for e in errors)


def test_create_duplicate_explicit_code_rejected(db_session: Session, test_company):
    """A duplicate explicit code surfaces a unique-constraint error."""
    service = CustomerService()
    service.create(db_session, {"name": "A", "company_id": test_company.id, "code": "DUP-1"})
    instance, errors = service.create(
        db_session, {"name": "B", "company_id": test_company.id, "code": "DUP-1"}
    )

    assert instance is None
    assert any(e.message_key == "unique_constraint" for e in errors)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def test_validate_negative_credit_limit():
    """A negative credit limit is rejected with a bilingual message."""
    service = CustomerService()
    errors = service.validate(
        {"name": "X", "company_id": "c", "credit_limit": Decimal("-1.00")}
    )
    credit_errors = [e for e in errors if e.field == "credit_limit"]

    assert credit_errors
    assert credit_errors[0].message_key == "negative_amount"
    assert credit_errors[0].get_message("en") != credit_errors[0].get_message("ar")


def test_validate_invalid_email():
    """An invalid email format is rejected."""
    service = CustomerService()
    errors = service.validate({"name": "X", "company_id": "c", "email": "not-an-email"})

    assert any(e.field == "email" and e.message_key == "invalid_email" for e in errors)


def test_validate_max_length_name():
    """A name longer than 200 chars is rejected."""
    service = CustomerService()
    errors = service.validate({"name": "A" * 201, "company_id": "c"})

    assert any(e.field == "name" and e.message_key == "max_length" for e in errors)


def test_validate_clean_payload_passes():
    """A well-formed payload yields no errors."""
    service = CustomerService()
    errors = service.validate(
        {
            "name": "Clean Co",
            "company_id": "c",
            "email": "ok@clean.co",
            "phone": "+1-555-123-4567",
            "credit_limit": Decimal("100.00"),
        }
    )

    assert errors == []


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_all_and_get_by_id(db_session: Session, test_company):
    """get_all returns created rows and get_by_id fetches a single one."""
    service = CustomerService()
    created, _ = service.create(db_session, {"name": "Readable", "company_id": test_company.id})

    all_rows = service.get_all(db_session)
    fetched = service.get_by_id(db_session, created.id)

    assert len(all_rows) == 1
    assert fetched is not None and fetched.id == created.id


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_customer_fields(db_session: Session, test_company):
    """Updating mutable fields persists the new values."""
    service = CustomerService()
    created, _ = service.create(db_session, {"name": "Old Name", "company_id": test_company.id})

    updated, errors = service.update(
        db_session, created.id, {"name": "New Name", "phone": "+1-555-999-8888"}
    )

    assert errors == []
    assert updated.name == "New Name"
    assert updated.phone == "+1-555-999-8888"


def test_update_negative_credit_limit_fails(db_session: Session, test_company):
    """An update with a negative credit limit is rejected."""
    service = CustomerService()
    created, _ = service.create(db_session, {"name": "Cust", "company_id": test_company.id})

    updated, errors = service.update(db_session, created.id, {"credit_limit": Decimal("-50")})

    assert updated is None
    assert any(e.field == "credit_limit" and e.message_key == "negative_amount" for e in errors)


def test_update_missing_record(db_session: Session):
    """Updating a non-existent id returns a not_found error."""
    import uuid

    service = CustomerService()
    updated, errors = service.update(db_session, uuid.uuid4(), {"name": "Nope"})

    assert updated is None
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# DELETE (soft)
# ---------------------------------------------------------------------------

def test_soft_delete_deactivates(db_session: Session, test_company):
    """Default delete is a soft delete that flips is_active to False."""
    service = CustomerService()
    created, _ = service.create(db_session, {"name": "ToDelete", "company_id": test_company.id})

    success, errors = service.delete(db_session, created.id)

    assert success is True
    assert errors == []
    assert service.get_by_id(db_session, created.id).is_active is False


def test_delete_missing_record(db_session: Session):
    """Deleting a non-existent id returns a not_found error."""
    import uuid

    service = CustomerService()
    success, errors = service.delete(db_session, uuid.uuid4())

    assert success is False
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------

def test_singleton_pattern():
    """get_customer_service returns the same instance."""
    assert get_customer_service() is get_customer_service()

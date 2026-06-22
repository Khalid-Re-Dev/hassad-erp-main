"""
Database-backed CRUD tests for SupplierService.

Exercises the full create/read/update/delete lifecycle against the in-memory
SQLite test engine, including bilingual validation and soft-delete behaviour.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.supplier_service import SupplierService, get_supplier_service
from models import Supplier


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_create_supplier(db_session: Session, test_company):
    """A supplier is created with the supplied fields."""
    service = SupplierService()
    instance, errors = service.create(
        db_session,
        {
            "name": "Acme Supplies",
            "company_id": test_company.id,
            "contact_name": "Jane Doe",
            "email": "jane@acme.com",
            "phone": "+1-555-100-2000",
            "default_payment_terms": Decimal("45"),
            "preferred_currency": "USD",
        },
    )

    assert errors == []
    assert instance is not None and instance.id is not None
    assert instance.name == "Acme Supplies"
    assert instance.contact_name == "Jane Doe"
    assert instance.default_payment_terms == Decimal("45")


def test_create_minimal(db_session: Session, test_company):
    """Only name + company_id are required to create."""
    service = SupplierService()
    instance, errors = service.create(
        db_session, {"name": "Minimal Co", "company_id": test_company.id}
    )

    assert errors == []
    assert instance.name == "Minimal Co"


def test_create_missing_name_fails(db_session: Session, test_company):
    """Creating without the required name returns a validation error."""
    service = SupplierService()
    instance, errors = service.create(db_session, {"company_id": test_company.id})

    assert instance is None
    assert any(e.field == "name" and e.message_key == "required" for e in errors)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def test_validate_invalid_email():
    """An invalid email format is rejected."""
    service = SupplierService()
    errors = service.validate({"name": "X", "company_id": "c", "email": "bad-email"})

    assert any(e.field == "email" and e.message_key == "invalid_email" for e in errors)


def test_validate_negative_payment_terms():
    """Negative payment terms are rejected with a bilingual message."""
    service = SupplierService()
    errors = service.validate(
        {"name": "X", "company_id": "c", "default_payment_terms": Decimal("-5")}
    )
    term_errors = [e for e in errors if e.field == "default_payment_terms"]

    assert term_errors
    assert term_errors[0].message_key == "negative_amount"
    assert term_errors[0].get_message("en") != term_errors[0].get_message("ar")


def test_validate_bad_currency():
    """A currency code that is not 3 alphabetic chars is rejected."""
    service = SupplierService()
    errors = service.validate(
        {"name": "X", "company_id": "c", "preferred_currency": "US"}
    )

    assert any(e.field == "preferred_currency" for e in errors)


def test_validate_max_length_name():
    """A name longer than 255 chars is rejected."""
    service = SupplierService()
    errors = service.validate({"name": "A" * 256, "company_id": "c"})

    assert any(e.field == "name" and e.message_key == "max_length" for e in errors)


def test_validate_clean_payload_passes():
    """A well-formed payload yields no errors."""
    service = SupplierService()
    errors = service.validate(
        {
            "name": "Clean Vendor",
            "company_id": "c",
            "email": "ok@vendor.co",
            "phone": "+1-555-123-4567",
            "default_payment_terms": Decimal("30"),
            "preferred_currency": "SAR",
        }
    )

    assert errors == []


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_all_and_get_by_id(db_session: Session, test_company):
    """get_all returns created rows and get_by_id fetches a single one."""
    service = SupplierService()
    created, _ = service.create(db_session, {"name": "Readable", "company_id": test_company.id})

    all_rows = service.get_all(db_session)
    fetched = service.get_by_id(db_session, created.id)

    assert len(all_rows) == 1
    assert fetched is not None and fetched.id == created.id


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_supplier_fields(db_session: Session, test_company):
    """Updating mutable fields persists the new values."""
    service = SupplierService()
    created, _ = service.create(db_session, {"name": "Old Vendor", "company_id": test_company.id})

    updated, errors = service.update(
        db_session, created.id, {"name": "New Vendor", "phone": "+1-555-999-8888"}
    )

    assert errors == []
    assert updated.name == "New Vendor"
    assert updated.phone == "+1-555-999-8888"


def test_update_negative_payment_terms_fails(db_session: Session, test_company):
    """An update with negative payment terms is rejected."""
    service = SupplierService()
    created, _ = service.create(db_session, {"name": "Vendor", "company_id": test_company.id})

    updated, errors = service.update(
        db_session, created.id, {"default_payment_terms": Decimal("-1")}
    )

    assert updated is None
    assert any(
        e.field == "default_payment_terms" and e.message_key == "negative_amount"
        for e in errors
    )


def test_update_missing_record(db_session: Session):
    """Updating a non-existent id returns a not_found error."""
    import uuid

    service = SupplierService()
    updated, errors = service.update(db_session, uuid.uuid4(), {"name": "Nope"})

    assert updated is None
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# DELETE (soft)
# ---------------------------------------------------------------------------

def test_soft_delete_deactivates(db_session: Session, test_company):
    """Default delete is a soft delete that flips is_active to False."""
    service = SupplierService()
    created, _ = service.create(db_session, {"name": "ToDelete", "company_id": test_company.id})

    success, errors = service.delete(db_session, created.id)

    assert success is True
    assert errors == []
    assert service.get_by_id(db_session, created.id).is_active is False


def test_delete_missing_record(db_session: Session):
    """Deleting a non-existent id returns a not_found error."""
    import uuid

    service = SupplierService()
    success, errors = service.delete(db_session, uuid.uuid4())

    assert success is False
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------

def test_singleton_pattern():
    """get_supplier_service returns the same instance."""
    assert get_supplier_service() is get_supplier_service()

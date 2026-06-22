"""
Database-backed CRUD tests for CategoryService.

Exercises create/read/update/delete against the in-memory SQLite test engine,
including parent-category handling, bilingual validation, the cannot-delete-
with-products rule, and soft-delete behaviour.
"""

import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.category_service import CategoryService, get_category_service
from models import Category, Product, Unit


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_create_category(db_session: Session, test_company):
    """A category is created with the supplied fields."""
    service = CategoryService()
    instance, errors = service.create(
        db_session,
        {"name_en": "Beverages", "name_ar": "مشروبات", "company_id": test_company.id},
    )

    assert errors == []
    assert instance is not None and instance.id is not None
    assert instance.name_en == "Beverages"
    assert instance.name_ar == "مشروبات"


def test_create_with_parent(db_session: Session, test_company):
    """A child category can reference an existing parent."""
    service = CategoryService()
    parent, _ = service.create(db_session, {"name_en": "Food", "company_id": test_company.id})
    child, errors = service.create(
        db_session,
        {"name_en": "Snacks", "company_id": test_company.id, "parent_id": parent.id},
    )

    assert errors == []
    assert child.parent_id == parent.id


def test_create_missing_name_fails(db_session: Session, test_company):
    """Creating without the required name_en returns a validation error."""
    service = CategoryService()
    instance, errors = service.create(db_session, {"company_id": test_company.id})

    assert instance is None
    assert any(e.field == "name_en" and e.message_key == "required" for e in errors)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def test_validate_max_length_name():
    """A name_en longer than 255 chars is rejected."""
    service = CategoryService()
    errors = service.validate({"name_en": "A" * 256, "company_id": "c"})

    assert any(e.field == "name_en" and e.message_key == "max_length" for e in errors)


def test_validate_self_parent_rejected(db_session: Session, test_company):
    """A category cannot be set as its own parent on update."""
    service = CategoryService()
    created, _ = service.create(db_session, {"name_en": "Self", "company_id": test_company.id})

    updated, errors = service.update(db_session, created.id, {"parent_id": created.id})

    assert updated is None
    assert any(e.field == "parent_id" for e in errors)


def test_validate_clean_payload_passes():
    """A well-formed payload yields no errors."""
    service = CategoryService()
    errors = service.validate({"name_en": "Clean", "company_id": "c"})

    assert errors == []


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_all_and_get_by_id(db_session: Session, test_company):
    """get_all returns created rows and get_by_id fetches a single one."""
    service = CategoryService()
    created, _ = service.create(db_session, {"name_en": "Readable", "company_id": test_company.id})

    all_rows = service.get_all(db_session)
    fetched = service.get_by_id(db_session, created.id)

    assert len(all_rows) == 1
    assert fetched is not None and fetched.id == created.id


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_category_fields(db_session: Session, test_company):
    """Updating mutable fields persists the new values."""
    service = CategoryService()
    created, _ = service.create(db_session, {"name_en": "Old", "company_id": test_company.id})

    updated, errors = service.update(
        db_session, created.id, {"name_en": "New", "name_ar": "جديد"}
    )

    assert errors == []
    assert updated.name_en == "New"
    assert updated.name_ar == "جديد"


def test_update_missing_record(db_session: Session):
    """Updating a non-existent id returns a not_found error."""
    service = CategoryService()
    updated, errors = service.update(db_session, uuid.uuid4(), {"name_en": "Nope"})

    assert updated is None
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def test_soft_delete_deactivates(db_session: Session, test_company):
    """Default delete is a soft delete that flips is_active to False."""
    service = CategoryService()
    created, _ = service.create(db_session, {"name_en": "ToDelete", "company_id": test_company.id})

    success, errors = service.delete(db_session, created.id)

    assert success is True
    assert errors == []
    assert service.get_by_id(db_session, created.id).is_active is False


def test_delete_blocked_when_products_exist(db_session: Session, test_company):
    """A category that still has products cannot be deleted."""
    service = CategoryService()
    category, _ = service.create(
        db_session, {"name_en": "Has Products", "company_id": test_company.id}
    )

    # Create a product assigned to the category.
    unit = Unit(id=uuid.uuid4(), company_id=test_company.id, name="Piece", symbol="pc")
    db_session.add(unit)
    db_session.flush()
    product = Product(
        id=uuid.uuid4(),
        company_id=test_company.id,
        base_unit_id=unit.id,
        category_id=category.id,
        sku="CAT-PROD-001",
        name_en="Catted Product",
        track_batches=False,
        track_expiry=False,
    )
    db_session.add(product)
    db_session.flush()

    success, errors = service.delete(db_session, category.id)

    assert success is False
    assert any(e.message_key == "cannot_delete" for e in errors)


def test_delete_missing_record(db_session: Session):
    """Deleting a non-existent id returns a not_found error."""
    service = CategoryService()
    success, errors = service.delete(db_session, uuid.uuid4())

    assert success is False
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------

def test_singleton_pattern():
    """get_category_service returns the same instance."""
    assert get_category_service() is get_category_service()

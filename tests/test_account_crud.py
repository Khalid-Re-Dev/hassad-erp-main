"""
Database-backed CRUD tests for AccountService (Chart of Accounts).

Exercises create/read/update/delete against the in-memory SQLite test engine,
with emphasis on accounting-safety rules: account-type validation, frozen type
after posting, system-account protection, and hard-delete blocking when ledger
data (journal lines / children) exists.
"""

import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.account_service import AccountService, get_account_service
from models import Account, AccountType, JournalEntry, JournalLine


def _make_account(service, db_session, test_company, **overrides):
    """Helper: create a basic account and return it."""
    data = {
        "code": overrides.pop("code", "1000"),
        "name_en": overrides.pop("name_en", "Cash"),
        "account_type": overrides.pop("account_type", AccountType.ASSET),
        "company_id": test_company.id,
    }
    data.update(overrides)
    instance, errors = service.create(db_session, data)
    assert errors == [], f"unexpected errors: {[e.message_key for e in errors]}"
    return instance


def _add_journal_line(db_session, test_company, test_branch, test_user, account):
    """Helper: attach a posted journal line to an account."""
    entry = JournalEntry(
        id=uuid.uuid4(),
        company_id=test_company.id,
        branch_id=test_branch.id,
        entry_number="JE-0001",
        reference="TEST",
        entry_date="2026-01-01",
        created_by=test_user.id,
    )
    db_session.add(entry)
    db_session.flush()
    line = JournalLine(
        id=uuid.uuid4(),
        journal_entry_id=entry.id,
        account_id=account.id,
        debit=Decimal("100.00"),
        credit=Decimal("0.00"),
    )
    db_session.add(line)
    db_session.flush()
    return line


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_create_account(db_session: Session, test_company):
    """An account is created with the supplied fields."""
    service = AccountService()
    instance = _make_account(service, db_session, test_company, code="1010", name_en="Bank")

    assert instance.id is not None
    assert instance.code == "1010"
    assert instance.account_type == AccountType.ASSET


def test_create_with_string_type(db_session: Session, test_company):
    """account_type accepts a string value and is validated."""
    service = AccountService()
    instance, errors = service.create(
        db_session,
        {"code": "4000", "name_en": "Sales", "account_type": "REVENUE", "company_id": test_company.id},
    )
    assert errors == []
    assert instance.account_type == AccountType.REVENUE


def test_create_missing_required(db_session: Session, test_company):
    """Missing required fields produce validation errors."""
    service = AccountService()
    instance, errors = service.create(db_session, {"company_id": test_company.id})

    assert instance is None
    fields = {e.field for e in errors}
    assert {"code", "name_en", "account_type"}.issubset(fields)


def test_create_duplicate_code_same_company_rejected(db_session: Session, test_company):
    """Duplicate code within the same company is rejected (unique per company)."""
    service = AccountService()
    _make_account(service, db_session, test_company, code="1000")
    instance, errors = service.create(
        db_session,
        {"code": "1000", "name_en": "Dup", "account_type": AccountType.ASSET, "company_id": test_company.id},
    )

    assert instance is None
    assert any(e.message_key == "unique_constraint" for e in errors)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def test_validate_invalid_account_type():
    """An unknown account type is rejected."""
    service = AccountService()
    errors = service.validate(
        {"code": "1", "name_en": "X", "account_type": "NONSENSE", "company_id": "c"}
    )
    assert any(e.field == "account_type" and e.message_key == "invalid_type" for e in errors)


def test_validate_max_length_code():
    """A code longer than 50 chars is rejected."""
    service = AccountService()
    errors = service.validate(
        {"code": "X" * 51, "name_en": "X", "account_type": AccountType.ASSET, "company_id": "c"}
    )
    assert any(e.field == "code" and e.message_key == "max_length" for e in errors)


def test_validate_clean_payload_passes():
    """A well-formed payload yields no errors."""
    service = AccountService()
    errors = service.validate(
        {"code": "5000", "name_en": "Rent", "account_type": AccountType.EXPENSE, "company_id": "c"}
    )
    assert errors == []


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_all_and_get_by_id(db_session: Session, test_company):
    """get_all returns created rows and get_by_id fetches a single one."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)

    assert len(service.get_all(db_session)) == 1
    assert service.get_by_id(db_session, created.id).id == created.id


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_account_name(db_session: Session, test_company):
    """Updating mutable fields persists the new values."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)

    updated, errors = service.update(db_session, created.id, {"name_en": "Petty Cash"})

    assert errors == []
    assert updated.name_en == "Petty Cash"


def test_update_self_parent_rejected(db_session: Session, test_company):
    """An account cannot be set as its own parent."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)

    updated, errors = service.update(db_session, created.id, {"parent_id": created.id})

    assert updated is None
    assert any(e.field == "parent_id" for e in errors)


def test_update_type_change_allowed_without_lines(db_session: Session, test_company):
    """Type can be changed while the account has no journal lines."""
    service = AccountService()
    created = _make_account(service, db_session, test_company, account_type=AccountType.ASSET)

    updated, errors = service.update(
        db_session, created.id, {"account_type": AccountType.EXPENSE}
    )

    assert errors == []
    assert updated.account_type == AccountType.EXPENSE


def test_update_type_change_blocked_with_lines(
    db_session: Session, test_company, test_branch, test_user
):
    """Type cannot be changed once the account has journal lines."""
    service = AccountService()
    created = _make_account(service, db_session, test_company, account_type=AccountType.ASSET)
    _add_journal_line(db_session, test_company, test_branch, test_user, created)

    updated, errors = service.update(
        db_session, created.id, {"account_type": AccountType.EXPENSE}
    )

    assert updated is None
    assert any(
        e.field == "account_type" and e.message_key == "cannot_modify_type" for e in errors
    )


def test_update_missing_record(db_session: Session):
    """Updating a non-existent id returns a not_found error."""
    service = AccountService()
    updated, errors = service.update(db_session, uuid.uuid4(), {"name_en": "Nope"})

    assert updated is None
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def test_soft_delete_deactivates(db_session: Session, test_company):
    """Default delete is a soft delete that flips is_active to False."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)

    success, errors = service.delete(db_session, created.id)

    assert success is True
    assert errors == []
    assert service.get_by_id(db_session, created.id).is_active is False


def test_system_account_cannot_be_deleted(db_session: Session, test_company):
    """System accounts are protected from deletion."""
    service = AccountService()
    created = _make_account(service, db_session, test_company, is_system=True)

    success, errors = service.delete(db_session, created.id)

    assert success is False
    assert any(e.message_key == "system_protected" for e in errors)


def test_hard_delete_blocked_with_journal_lines(
    db_session: Session, test_company, test_branch, test_user
):
    """An account with journal lines cannot be hard-deleted."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)
    _add_journal_line(db_session, test_company, test_branch, test_user, created)

    success, errors = service.delete(db_session, created.id, soft_delete=False)

    assert success is False
    assert any(e.message_key == "cannot_delete" for e in errors)


def test_hard_delete_blocked_with_children(db_session: Session, test_company):
    """A parent account cannot be hard-deleted while it has children."""
    service = AccountService()
    parent = _make_account(service, db_session, test_company, code="1000", name_en="Assets")
    _make_account(
        service, db_session, test_company, code="1100", name_en="Cash", parent_id=parent.id
    )

    success, errors = service.delete(db_session, parent.id, soft_delete=False)

    assert success is False
    assert any(e.message_key == "cannot_delete" for e in errors)


def test_hard_delete_allowed_when_unused(db_session: Session, test_company):
    """An unused, non-system account can be hard-deleted."""
    service = AccountService()
    created = _make_account(service, db_session, test_company)

    success, errors = service.delete(db_session, created.id, soft_delete=False)

    assert success is True
    assert errors == []
    assert service.get_by_id(db_session, created.id) is None


def test_delete_missing_record(db_session: Session):
    """Deleting a non-existent id returns a not_found error."""
    service = AccountService()
    success, errors = service.delete(db_session, uuid.uuid4())

    assert success is False
    assert any(e.message_key == "not_found" for e in errors)


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------

def test_singleton_pattern():
    """get_account_service returns the same instance."""
    assert get_account_service() is get_account_service()

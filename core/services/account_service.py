"""
Account Service Layer.

Provides business logic and CRUD operations for the Chart of Accounts.

Because this is an accounting system, account integrity is treated as
non-negotiable. The service enforces several accounting-safety rules:

* ``account_type`` must be one of the defined :class:`AccountType` values.
* An account's ``account_type`` cannot be changed once it has journal entries
  (changing it would silently corrupt historical financial reports).
* System accounts (``is_system``) can never be deleted.
* An account cannot be hard-deleted while it still has journal lines, payments,
  or child accounts; doing so would orphan ledger data. Such accounts may only
  be deactivated (soft delete).
* An account cannot be its own parent.

``code`` uniqueness is scoped per company (enforced by a composite unique index
on the model) and surfaces as a ``unique_constraint`` error on conflict.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Account, AccountType, JournalLine, Payment


class AccountService(BaseService):
    """Service for managing Chart of Accounts records."""

    def __init__(self) -> None:
        """Initialize account service."""
        super().__init__(Account)

    # ========================
    # Validation
    # ========================

    def validate(
        self,
        data: Dict[str, Any],
        is_update: bool = False,
        instance: Optional[Account] = None,
    ) -> List[ValidationError]:
        """
        Validate account data.

        Args:
            data: Dictionary of field values.
            is_update: True if this is an update operation.
            instance: Existing account instance (for updates).

        Returns:
            List of validation errors (empty if valid).
        """
        errors: List[ValidationError] = []

        # Required fields (only on create).
        if not is_update:
            required_fields = ["code", "name_en", "account_type", "company_id"]
            errors.extend(self._validate_required(data, required_fields))

        # Max length validation (mirrors the Account model column sizes).
        field_limits = {"code": 50, "name_en": 255, "name_ar": 255}
        errors.extend(self._validate_max_length(data, field_limits))

        # Account type must be a defined AccountType value.
        if data.get("account_type") is not None and str(data["account_type"]).strip() != "":
            if self._coerce_account_type(data["account_type"]) is None:
                errors.append(ValidationError("account_type", "invalid_type"))

        # A account cannot be its own parent (prevents a trivial cycle).
        if is_update and instance is not None and data.get("parent_id") is not None:
            if data["parent_id"] == instance.id:
                errors.append(ValidationError("parent_id", "invalid_data"))

        return errors

    @staticmethod
    def _coerce_account_type(value: Any) -> Optional[AccountType]:
        """
        Coerce a raw value into an :class:`AccountType`, or ``None`` if invalid.

        Accepts an ``AccountType`` member directly, or its string value/name
        (case-insensitive), so the UI can pass either form safely.
        """
        if isinstance(value, AccountType):
            return value
        if isinstance(value, str):
            key = value.strip().upper()
            for member in AccountType:
                if key in (member.value.upper(), member.name.upper()):
                    return member
        return None

    # ========================
    # Update (block type change after posting)
    # ========================

    def update(
        self, session: Session, record_id: Any, data: Dict[str, Any]
    ) -> Tuple[Optional[Account], List[ValidationError]]:
        """
        Update an account, guarding against unsafe ``account_type`` changes.

        Once an account has journal lines, its type is frozen to preserve the
        integrity of historical financial statements.
        """
        instance = self.get_by_id(session, record_id)
        if instance is not None and data.get("account_type") is not None:
            new_type = self._coerce_account_type(data["account_type"])
            if new_type is not None and new_type != instance.account_type:
                has_lines = (
                    session.query(JournalLine)
                    .filter(JournalLine.account_id == instance.id)
                    .count()
                )
                if has_lines:
                    return None, [ValidationError("account_type", "cannot_modify_type")]
        return super().update(session, record_id, data)

    # ========================
    # Delete (accounting-safe)
    # ========================

    def delete(
        self, session: Session, record_id: Any, soft_delete: bool = True
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Delete an account with accounting-safety rules.

        - System accounts can never be removed or deactivated.
        - Soft delete simply deactivates a non-system account (safe archiving),
          which is always allowed.
        - Hard delete is blocked while the account still has journal lines,
          payments, or child accounts, to avoid orphaning ledger data.

        Args:
            session: Database session.
            record_id: Account id.
            soft_delete: If True (default), deactivate instead of removing.

        Returns:
            Tuple of (success, validation_errors).
        """
        instance = self.get_by_id(session, record_id)
        if not instance:
            return False, [ValidationError("id", "not_found")]

        # System accounts are protected from any deletion/deactivation.
        if getattr(instance, "is_system", False):
            return False, [ValidationError("_general", "system_protected")]

        if soft_delete:
            instance.is_active = False
            session.flush()
            self.logger.info(f"Soft deleted (deactivated) Account ID {record_id}")
            return True, []

        # Hard delete safety checks.
        blockers = self._hard_delete_blockers(session, instance)
        if blockers:
            return False, blockers

        session.delete(instance)
        session.flush()
        self.logger.info(f"Hard deleted Account ID {record_id}")
        return True, []

    def _hard_delete_blockers(
        self, session: Session, instance: Account
    ) -> List[ValidationError]:
        """Return blocking errors that prevent hard-deleting an account."""
        line_count = (
            session.query(JournalLine)
            .filter(JournalLine.account_id == instance.id)
            .count()
        )
        if line_count > 0:
            return [ValidationError("_general", "cannot_delete")]

        payment_count = (
            session.query(Payment).filter(Payment.account_id == instance.id).count()
        )
        if payment_count > 0:
            return [ValidationError("_general", "cannot_delete")]

        child_count = (
            session.query(Account).filter(Account.parent_id == instance.id).count()
        )
        if child_count > 0:
            return [ValidationError("_general", "cannot_delete")]

        return []


# Singleton instance
_account_service: Optional[AccountService] = None


def get_account_service() -> AccountService:
    """Get or create account service singleton."""
    global _account_service
    if _account_service is None:
        _account_service = AccountService()
    return _account_service

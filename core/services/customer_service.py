"""
Customer Service Layer.

Provides business logic and CRUD operations for Customer management.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Customer


class CustomerService(BaseService):
    """
    Customer service for managing customer records.

    Handles:
    - Customer CRUD operations
    - Automatic customer code generation (``CUST-00001`` ...)
    - Data validation (bilingual)
    - Business rules enforcement

    Note on the data model: the ``Customer`` model requires a NOT NULL, globally
    unique ``code``. The UI is not required to supply one, so this service
    auto-generates a sequential code on create when it is omitted. All business
    logic lives here, never in the UI layer.
    """

    #: Prefix used when auto-generating customer codes.
    CODE_PREFIX = "CUST-"
    #: Zero-padding width for the numeric part of an auto-generated code.
    CODE_PAD = 5

    def __init__(self) -> None:
        """Initialize customer service."""
        super().__init__(Customer)

    # ========================
    # Validation
    # ========================

    def validate(
        self,
        data: Dict[str, Any],
        is_update: bool = False,
        instance: Optional[Customer] = None,
    ) -> List[ValidationError]:
        """
        Validate customer data.

        Args:
            data: Dictionary of field values.
            is_update: True if this is an update operation.
            instance: Existing customer instance (for updates).

        Returns:
            List of validation errors (empty if valid).
        """
        errors: List[ValidationError] = []

        # Required fields (only on create). ``code`` is intentionally NOT
        # required from the caller because it is auto-generated in ``create``.
        if not is_update:
            required_fields = ["name", "company_id"]
            errors.extend(self._validate_required(data, required_fields))

        # Max length validation (mirrors the Customer model column sizes).
        field_limits = {
            "code": 50,
            "name": 200,
            "name_ar": 200,
            "phone": 50,
            "email": 200,
            "tax_id": 50,
        }
        errors.extend(self._validate_max_length(data, field_limits))

        # Email validation.
        if data.get("email"):
            errors.extend(self._validate_email(data, "email"))

        # Phone validation.
        if data.get("phone"):
            errors.extend(self._validate_phone(data, "phone"))

        # Credit limit must not be negative.
        errors.extend(self._validate_non_negative(data, "credit_limit"))
        # Credit balance, when explicitly provided, must not be negative.
        errors.extend(self._validate_non_negative(data, "credit_balance"))

        return errors

    def _validate_non_negative(
        self, data: Dict[str, Any], field: str
    ) -> List[ValidationError]:
        """
        Validate that a monetary field, if provided, is not negative.

        Args:
            data: Input data dictionary.
            field: Field name to check.

        Returns:
            List of validation errors (empty if valid or field absent/empty).
        """
        errors: List[ValidationError] = []
        if field in data and data[field] is not None and str(data[field]).strip() != "":
            try:
                if Decimal(str(data[field])) < 0:
                    errors.append(ValidationError(field, "negative_amount"))
            except (InvalidOperation, ValueError, TypeError):
                errors.append(ValidationError(field, "invalid_data"))
        return errors

    # ========================
    # Create (with code auto-generation)
    # ========================

    def create(
        self, session: Session, data: Dict[str, Any]
    ) -> Tuple[Optional[Customer], List[ValidationError]]:
        """
        Create a new customer, auto-generating ``code`` when not supplied.

        Args:
            session: Database session.
            data: Dictionary of field values.

        Returns:
            Tuple of (created_instance, validation_errors).
        """
        data = dict(data)  # never mutate the caller's dict
        code = data.get("code")
        if code is None or str(code).strip() == "":
            data["code"] = self.generate_code(session)
        return super().create(session, data)

    def generate_code(self, session: Session) -> str:
        """
        Generate the next sequential, unique customer code.

        Reads the highest existing code with the standard prefix, increments it,
        and guarantees uniqueness before returning (handles non-standard or
        manually entered codes gracefully).

        Args:
            session: Database session.

        Returns:
            A unique customer code such as ``CUST-00001``.
        """
        prefix = self.CODE_PREFIX
        last = (
            session.query(Customer)
            .filter(Customer.code.like(f"{prefix}%"))
            .order_by(Customer.code.desc())
            .first()
        )

        next_num = 1
        if last and last.code:
            suffix = last.code[len(prefix):]
            try:
                next_num = int(suffix) + 1
            except (ValueError, TypeError):
                next_num = session.query(Customer).count() + 1

        # Guarantee uniqueness even with gaps or manually inserted codes.
        candidate = f"{prefix}{next_num:0{self.CODE_PAD}d}"
        while session.query(Customer).filter(Customer.code == candidate).first():
            next_num += 1
            candidate = f"{prefix}{next_num:0{self.CODE_PAD}d}"
        return candidate


# Singleton instance
_customer_service: Optional[CustomerService] = None


def get_customer_service() -> CustomerService:
    """Get or create customer service singleton."""
    global _customer_service
    if _customer_service is None:
        _customer_service = CustomerService()
    return _customer_service

"""
Supplier Service Layer.

Provides business logic and CRUD operations for Supplier management.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Supplier


class SupplierService(BaseService):
    """
    Supplier service for managing supplier (vendor) records.

    Handles:
    - Supplier CRUD operations
    - Data validation (bilingual)
    - Business rules enforcement

    All business logic lives here; the UI layer only collects/presents data.
    """

    def __init__(self) -> None:
        """Initialize supplier service."""
        super().__init__(Supplier)

    def validate(
        self,
        data: Dict[str, Any],
        is_update: bool = False,
        instance: Optional[Supplier] = None,
    ) -> List[ValidationError]:
        """
        Validate supplier data.

        Args:
            data: Dictionary of field values.
            is_update: True if this is an update operation.
            instance: Existing supplier instance (for updates).

        Returns:
            List of validation errors (empty if valid).
        """
        errors: List[ValidationError] = []

        # Required fields (only on create).
        if not is_update:
            required_fields = ["name", "company_id"]
            errors.extend(self._validate_required(data, required_fields))

        # Max length validation (mirrors the Supplier model column sizes).
        field_limits = {
            "name": 255,
            "tax_id": 50,
            "contact_name": 255,
            "email": 255,
            "phone": 50,
            "preferred_currency": 3,
        }
        errors.extend(self._validate_max_length(data, field_limits))

        # Email validation.
        if data.get("email"):
            errors.extend(self._validate_email(data, "email"))

        # Phone validation.
        if data.get("phone"):
            errors.extend(self._validate_phone(data, "phone"))

        # Payment terms (days) must not be negative.
        errors.extend(self._validate_non_negative(data, "default_payment_terms"))

        # Preferred currency, when provided, must be a 3-letter ISO 4217 code.
        if data.get("preferred_currency"):
            currency = str(data["preferred_currency"]).strip()
            if len(currency) != 3 or not currency.isalpha():
                errors.append(ValidationError("preferred_currency", "invalid_data"))

        return errors


# Singleton instance
_supplier_service: Optional[SupplierService] = None


def get_supplier_service() -> SupplierService:
    """Get or create supplier service singleton."""
    global _supplier_service
    if _supplier_service is None:
        _supplier_service = SupplierService()
    return _supplier_service

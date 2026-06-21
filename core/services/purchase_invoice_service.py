"""
PurchaseInvoice Service Layer.

Provides business logic and CRUD operations for PurchaseInvoice management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import PurchaseInvoice, PurchaseOrder


class PurchaseInvoiceService(BaseService):
    """
    PurchaseInvoice service for managing purchase_invoice records.
    
    Handles:
    - PurchaseInvoice CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize purchase_invoice service."""
        super().__init__(PurchaseInvoice)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[PurchaseInvoice] = None
    ) -> List[ValidationError]:
        """
        Validate purchase_invoice data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing purchase_invoice instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['invoice_number', 'purchase_order_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'invoice_number': 50, 'supplier_invoice_number': 100}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        # Validate amounts are non-negative
        for field in ['subtotal', 'tax_total', 'total_amount']:
            if field in data and data[field] is not None:
                try:
                    if float(data[field]) < 0:
                        errors.append(ValidationError(
                            field, 'invalid_data',
                            message=f'{field} must be non-negative'
                        ))
                except (ValueError, TypeError):
                    pass
        
        return errors


# Singleton instance
_purchase_invoice_service = None

def get_purchase_invoice_service() -> PurchaseInvoiceService:
    """Get or create purchase_invoice service singleton."""
    global _purchase_invoice_service
    if _purchase_invoice_service is None:
        _purchase_invoice_service = PurchaseInvoiceService()
    return _purchase_invoice_service

"""
PurchaseOrder Service Layer.

Provides business logic and CRUD operations for PurchaseOrder management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import PurchaseOrder, PurchaseOrderLine, Supplier


class PurchaseOrderService(BaseService):
    """
    PurchaseOrder service for managing purchase_order records.
    
    Handles:
    - PurchaseOrder CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize purchase_order service."""
        super().__init__(PurchaseOrder)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[PurchaseOrder] = None
    ) -> List[ValidationError]:
        """
        Validate purchase_order data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing purchase_order instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['po_number', 'company_id', 'branch_id', 'supplier_id', 'created_by']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'po_number': 50}
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
_purchase_order_service = None

def get_purchase_order_service() -> PurchaseOrderService:
    """Get or create purchase_order service singleton."""
    global _purchase_order_service
    if _purchase_order_service is None:
        _purchase_order_service = PurchaseOrderService()
    return _purchase_order_service

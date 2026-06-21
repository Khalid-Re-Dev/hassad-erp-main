"""
GoodsReceipt Service Layer.

Provides business logic and CRUD operations for GoodsReceipt management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import GoodsReceipt, PurchaseOrder


class GoodsReceiptService(BaseService):
    """
    GoodsReceipt service for managing goods_receipt records.
    
    Handles:
    - GoodsReceipt CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize goods_receipt service."""
        super().__init__(GoodsReceipt)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[GoodsReceipt] = None
    ) -> List[ValidationError]:
        """
        Validate goods_receipt data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing goods_receipt instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['grn_number', 'purchase_order_id']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'grn_number': 50}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        return errors


# Singleton instance
_goods_receipt_service = None

def get_goods_receipt_service() -> GoodsReceiptService:
    """Get or create goods_receipt service singleton."""
    global _goods_receipt_service
    if _goods_receipt_service is None:
        _goods_receipt_service = GoodsReceiptService()
    return _goods_receipt_service

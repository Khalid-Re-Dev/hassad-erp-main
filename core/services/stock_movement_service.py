"""
StockMovement Service Layer.

Provides business logic and CRUD operations for StockMovement management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import StockMovement, Product, Branch


class StockMovementService(BaseService):
    """
    StockMovement service for managing stock_movement records.
    
    Handles:
    - StockMovement CRUD operations
    - Data validation
    - Business rules enforcement
    """
    
    def __init__(self):
        """Initialize stock_movement service."""
        super().__init__(StockMovement)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[StockMovement] = None
    ) -> List[ValidationError]:
        """
        Validate stock_movement data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing stock_movement instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            required_fields = ['product_id', 'branch_id', 'movement_type', 'quantity', 'unit_cost']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {'reference_type': 50}
        if field_limits:
            errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        
        # Validate quantity > 0
        if 'quantity' in data and data['quantity'] is not None:
            try:
                if float(data['quantity']) <= 0:
                    errors.append(ValidationError(
                        'quantity', 'invalid_data',
                        message='Quantity must be greater than zero'
                    ))
            except (ValueError, TypeError):
                pass
        
        return errors


# Singleton instance
_stock_movement_service = None

def get_stock_movement_service() -> StockMovementService:
    """Get or create stock_movement service singleton."""
    global _stock_movement_service
    if _stock_movement_service is None:
        _stock_movement_service = StockMovementService()
    return _stock_movement_service

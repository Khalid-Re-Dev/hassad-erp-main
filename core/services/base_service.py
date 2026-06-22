"""
Base Service Layer for Hassad ERP System.

Provides abstract base classes for service layer implementation with:
- Common CRUD operations
- Input validation
- Bilingual error messages
- Transaction management
- Error handling
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.base import BaseModel
import logging

logger = logging.getLogger(__name__)


# Bilingual validation messages
VALIDATION_MESSAGES = {
    'required': {
        'en': 'This field is required',
        'ar': 'هذا الحقل مطلوب'
    },
    'invalid_email': {
        'en': 'Invalid email format',
        'ar': 'تنسيق البريد الإلكتروني غير صالح'
    },
    'invalid_phone': {
        'en': 'Invalid phone number format',
        'ar': 'تنسيق رقم الهاتف غير صالح'
    },
    'max_length': {
        'en': 'Maximum length exceeded',
        'ar': 'تم تجاوز الطول الأقصى'
    },
    'unique_constraint': {
        'en': 'This value already exists',
        'ar': 'هذه القيمة موجودة بالفعل'
    },
    'not_found': {
        'en': 'Record not found',
        'ar': 'السجل غير موجود'
    },
    'cannot_delete': {
        'en': 'Cannot delete record with dependencies',
        'ar': 'لا يمكن حذف سجل له تبعيات'
    },
    'database_error': {
        'en': 'Database operation failed',
        'ar': 'فشلت عملية قاعدة البيانات'
    },
    'invalid_data': {
        'en': 'Invalid data provided',
        'ar': 'البيانات المقدمة غير صالحة'
    },
    'negative_amount': {
        'en': 'Amount cannot be negative',
        'ar': 'لا يمكن أن تكون القيمة سالبة'
    }
}


class ValidationError:
    """Validation error representation."""
    
    def __init__(self, field: str, message_key: str, **kwargs):
        """
        Initialize validation error.
        
        Args:
            field: Field name that failed validation
            message_key: Key to lookup bilingual message
            **kwargs: Additional parameters for message formatting
        """
        self.field = field
        self.message_key = message_key
        self.kwargs = kwargs
    
    def get_message(self, lang: str = 'en') -> str:
        """
        Get error message in specified language.
        
        Args:
            lang: Language code ('en' or 'ar')
            
        Returns:
            Formatted error message
        """
        messages = VALIDATION_MESSAGES.get(self.message_key, {})
        base_message = messages.get(lang, messages.get('en', 'Validation error'))
        
        if self.kwargs:
            return f"{base_message} ({', '.join(f'{k}={v}' for k, v in self.kwargs.items())})"
        return base_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'field': self.field,
            'message_en': self.get_message('en'),
            'message_ar': self.get_message('ar')
        }


class BaseService(ABC):
    """
    Abstract base service class.
    
    Provides common CRUD operations and validation logic
    for all service layer implementations.
    """
    
    def __init__(self, model_class: Type[BaseModel]):
        """
        Initialize service.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.logger = logging.getLogger(f"{__name__}.{model_class.__name__}Service")
    
    # ========================
    # READ Operations
    # ========================
    
    def get_all(
        self, 
        session: Session, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[BaseModel]:
        """
        Get all records with optional filters.
        
        Args:
            session: Database session
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        try:
            query = session.query(self.model_class)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        query = query.filter(getattr(self.model_class, field) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching all {self.model_class.__name__}: {e}")
            raise
    
    def get_by_id(self, session: Session, record_id: int) -> Optional[BaseModel]:
        """
        Get single record by ID.
        
        Args:
            session: Database session
            record_id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        try:
            return session.query(self.model_class).filter_by(id=record_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching {self.model_class.__name__} by ID {record_id}: {e}")
            raise
    
    # ========================
    # CREATE Operations
    # ========================
    
    def create(
        self, 
        session: Session, 
        data: Dict[str, Any]
    ) -> Tuple[Optional[BaseModel], List[ValidationError]]:
        """
        Create new record with validation.
        
        Args:
            session: Database session
            data: Dictionary of field values
            
        Returns:
            Tuple of (created_instance, validation_errors)
            If validation fails, instance is None and errors list is populated
        """
        try:
            # Validate input
            errors = self.validate(data, is_update=False)
            if errors:
                return None, errors
            
            # Create instance
            instance = self.model_class(**self._prepare_data(data))
            
            # Add to session
            session.add(instance)
            session.flush()  # Flush to get ID without committing
            
            self.logger.info(f"Created {self.model_class.__name__} with ID {instance.id}")
            return instance, []
            
        except IntegrityError as e:
            self.logger.warning(f"Integrity error creating {self.model_class.__name__}: {e}")
            error = ValidationError('_general', 'unique_constraint')
            return None, [error]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            error = ValidationError('_general', 'database_error')
            return None, [error]
    
    # ========================
    # UPDATE Operations
    # ========================
    
    def update(
        self, 
        session: Session, 
        record_id: int, 
        data: Dict[str, Any]
    ) -> Tuple[Optional[BaseModel], List[ValidationError]]:
        """
        Update existing record.
        
        Args:
            session: Database session
            record_id: Record ID to update
            data: Dictionary of field values to update
            
        Returns:
            Tuple of (updated_instance, validation_errors)
        """
        try:
            # Get existing record
            instance = self.get_by_id(session, record_id)
            if not instance:
                error = ValidationError('id', 'not_found')
                return None, [error]
            
            # Validate input
            errors = self.validate(data, is_update=True, instance=instance)
            if errors:
                return None, errors
            
            # Update fields
            prepared_data = self._prepare_data(data)
            for field, value in prepared_data.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            session.flush()
            
            self.logger.info(f"Updated {self.model_class.__name__} ID {record_id}")
            return instance, []
            
        except IntegrityError as e:
            self.logger.warning(f"Integrity error updating {self.model_class.__name__}: {e}")
            error = ValidationError('_general', 'unique_constraint')
            return None, [error]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating {self.model_class.__name__}: {e}")
            error = ValidationError('_general', 'database_error')
            return None, [error]
    
    # ========================
    # DELETE Operations
    # ========================
    
    def delete(
        self, 
        session: Session, 
        record_id: int,
        soft_delete: bool = True
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Delete record (soft or hard delete).
        
        Args:
            session: Database session
            record_id: Record ID to delete
            soft_delete: If True, set is_active=False instead of deleting
            
        Returns:
            Tuple of (success, validation_errors)
        """
        try:
            # Get existing record
            instance = self.get_by_id(session, record_id)
            if not instance:
                error = ValidationError('id', 'not_found')
                return False, [error]
            
            # Check if can delete
            can_delete, errors = self._can_delete(session, instance)
            if not can_delete:
                return False, errors
            
            if soft_delete and hasattr(instance, 'is_active'):
                # Soft delete - mark as inactive
                instance.is_active = False
                session.flush()
                self.logger.info(f"Soft deleted {self.model_class.__name__} ID {record_id}")
            else:
                # Hard delete
                session.delete(instance)
                session.flush()
                self.logger.info(f"Hard deleted {self.model_class.__name__} ID {record_id}")
            
            return True, []
            
        except IntegrityError as e:
            self.logger.warning(f"Cannot delete {self.model_class.__name__} with dependencies: {e}")
            error = ValidationError('_general', 'cannot_delete')
            return False, [error]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting {self.model_class.__name__}: {e}")
            error = ValidationError('_general', 'database_error')
            return False, [error]
    
    # ========================
    # Validation Methods
    # ========================
    
    @abstractmethod
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[BaseModel] = None
    ) -> List[ValidationError]:
        """
        Validate input data before create/update.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    def _validate_required(
        self, 
        data: Dict[str, Any], 
        required_fields: List[str]
    ) -> List[ValidationError]:
        """
        Validate required fields.
        
        Args:
            data: Input data dictionary
            required_fields: List of required field names
            
        Returns:
            List of validation errors
        """
        errors = []
        for field in required_fields:
            if field not in data or not data[field] or str(data[field]).strip() == '':
                errors.append(ValidationError(field, 'required'))
        return errors
    
    def _validate_max_length(
        self,
        data: Dict[str, Any],
        field_limits: Dict[str, int]
    ) -> List[ValidationError]:
        """
        Validate maximum field lengths.
        
        Args:
            data: Input data dictionary
            field_limits: Dictionary of field:max_length
            
        Returns:
            List of validation errors
        """
        errors = []
        for field, max_len in field_limits.items():
            if field in data and data[field] and len(str(data[field])) > max_len:
                errors.append(
                    ValidationError(field, 'max_length', max=max_len, actual=len(str(data[field])))
                )
        return errors
    
    def _validate_email(self, data: Dict[str, Any], field: str) -> List[ValidationError]:
        """
        Validate email format.
        
        Args:
            data: Input data dictionary
            field: Email field name
            
        Returns:
            List of validation errors
        """
        import re
        errors = []
        
        if field in data and data[field]:
            email = str(data[field]).strip()
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors.append(ValidationError(field, 'invalid_email'))
        
        return errors
    
    def _validate_phone(self, data: Dict[str, Any], field: str) -> List[ValidationError]:
        """
        Validate phone number format.
        
        Args:
            data: Input data dictionary
            field: Phone field name
            
        Returns:
            List of validation errors
        """
        import re
        errors = []
        
        if field in data and data[field]:
            phone = str(data[field]).strip()
            # Basic phone validation - digits, spaces, dashes, parentheses, plus
            phone_pattern = r'^[\d\s\-\(\)\+]+$'
            if not re.match(phone_pattern, phone) or len(phone.replace(' ', '').replace('-', '')) < 7:
                errors.append(ValidationError(field, 'invalid_phone'))
        
        return errors
    
    def _validate_non_negative(
        self, data: Dict[str, Any], field: str
    ) -> List[ValidationError]:
        """
        Validate that a numeric/monetary field, if provided, is not negative.

        Args:
            data: Input data dictionary.
            field: Field name to check.

        Returns:
            List of validation errors (empty if valid, or field absent/empty).
        """
        from decimal import Decimal, InvalidOperation

        errors: List[ValidationError] = []
        if field in data and data[field] is not None and str(data[field]).strip() != "":
            try:
                if Decimal(str(data[field])) < 0:
                    errors.append(ValidationError(field, 'negative_amount'))
            except (InvalidOperation, ValueError, TypeError):
                errors.append(ValidationError(field, 'invalid_data'))
        return errors

    # ========================
    # Helper Methods
    # ========================
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for database insertion (strip strings, handle nulls, etc.).
        
        Args:
            data: Raw input data
            
        Returns:
            Cleaned data dictionary
        """
        prepared = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Strip whitespace
                value = value.strip()
                # Convert empty strings to None
                if value == '':
                    value = None
            prepared[key] = value
        return prepared
    
    def _can_delete(
        self, 
        session: Session, 
        instance: BaseModel
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if record can be deleted (override in subclasses for custom logic).
        
        Args:
            session: Database session
            instance: Instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        # Default implementation - always allow delete
        # Override in subclasses to add dependency checks
        return True, []

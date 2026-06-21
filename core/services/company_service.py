"""
Company Service Layer.

Provides business logic and CRUD operations for Company management.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.services.base_service import BaseService, ValidationError
from models import Company, Branch


class CompanyService(BaseService):
    """
    Company service for managing company records.
    
    Handles:
    - Company profile creation and updates
    - Business information validation
    - Contact information validation
    - Dependency checking (branches, users, etc.)
    """
    
    def __init__(self):
        """Initialize company service."""
        super().__init__(Company)
    
    def validate(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False,
        instance: Optional[Company] = None
    ) -> List[ValidationError]:
        """
        Validate company data.
        
        Args:
            data: Dictionary of field values
            is_update: True if this is an update operation
            instance: Existing company instance (for updates)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields (only for create, not update)
        if not is_update:
            required_fields = ['name', 'country']
            errors.extend(self._validate_required(data, required_fields))
        
        # Max length validation
        field_limits = {
            'name': 255,
            'trade_name': 255,
            'tax_id': 50,
            'registration_number': 50,
            'email': 255,
            'phone': 50,
            'city': 100,
            'state': 100,
            'country': 100,
            'postal_code': 20,
            'currency': 3,
            'fiscal_year_start': 2,
            'logo_url': 500,
            'website': 255
        }
        errors.extend(self._validate_max_length(data, field_limits))
        
        # Email validation
        if 'email' in data and data['email']:
            errors.extend(self._validate_email(data, 'email'))
        
        # Phone validation
        if 'phone' in data and data['phone']:
            errors.extend(self._validate_phone(data, 'phone'))
        
        # Currency validation (ISO 4217 - 3 letter codes)
        if 'currency' in data and data['currency']:
            currency = str(data['currency']).upper().strip()
            if len(currency) != 3 or not currency.isalpha():
                errors.append(ValidationError(
                    'currency', 
                    'invalid_data',
                    message='Currency must be 3-letter ISO code (e.g., USD, EUR, SAR)'
                ))
        
        # Fiscal year start validation (01-12)
        if 'fiscal_year_start' in data and data['fiscal_year_start']:
            try:
                month = int(data['fiscal_year_start'])
                if month < 1 or month > 12:
                    errors.append(ValidationError(
                        'fiscal_year_start',
                        'invalid_data',
                        message='Fiscal year start must be between 01 and 12'
                    ))
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    'fiscal_year_start',
                    'invalid_data',
                    message='Fiscal year start must be a number between 01 and 12'
                ))
        
        return errors
    
    def _can_delete(
        self, 
        session: Session, 
        instance: Company
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Check if company can be deleted.
        
        Companies with active branches cannot be deleted.
        
        Args:
            session: Database session
            instance: Company instance to check
            
        Returns:
            Tuple of (can_delete, validation_errors)
        """
        errors = []
        
        # Check for active branches
        branch_count = session.query(Branch).filter(
            Branch.company_id == instance.id,
            Branch.is_active == True
        ).count()
        
        if branch_count > 0:
            errors.append(ValidationError(
                '_general',
                'cannot_delete',
                message=f'Company has {branch_count} active branch(es). Deactivate or delete branches first.'
            ))
            return False, errors
        
        return True, []
    
    def get_active_companies(self, session: Session) -> List[Company]:
        """
        Get all active companies.
        
        Args:
            session: Database session
            
        Returns:
            List of active companies
        """
        return self.get_all(
            session,
            filters={'is_active': True},
            order_by='name'
        )
    
    def get_by_tax_id(self, session: Session, tax_id: str) -> Optional[Company]:
        """
        Get company by tax ID.
        
        Args:
            session: Database session
            tax_id: Tax identification number
            
        Returns:
            Company instance or None
        """
        try:
            return session.query(Company).filter_by(tax_id=tax_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching company by tax_id {tax_id}: {e}")
            return None
    
    def activate(
        self, 
        session: Session, 
        company_id: int
    ) -> Tuple[Optional[Company], List[ValidationError]]:
        """
        Activate a company.
        
        Args:
            session: Database session
            company_id: Company ID
            
        Returns:
            Tuple of (company_instance, validation_errors)
        """
        company = self.get_by_id(session, company_id)
        if not company:
            return None, [ValidationError('id', 'not_found')]
        
        company.is_active = True
        session.flush()
        
        self.logger.info(f"Activated company ID {company_id}")
        return company, []
    
    def deactivate(
        self, 
        session: Session, 
        company_id: int
    ) -> Tuple[Optional[Company], List[ValidationError]]:
        """
        Deactivate a company.
        
        Args:
            session: Database session
            company_id: Company ID
            
        Returns:
            Tuple of (company_instance, validation_errors)
        """
        company = self.get_by_id(session, company_id)
        if not company:
            return None, [ValidationError('id', 'not_found')]
        
        # Check if can deactivate (has active branches)
        can_deactivate, errors = self._can_delete(session, company)
        if not can_deactivate:
            return None, errors
        
        company.is_active = False
        session.flush()
        
        self.logger.info(f"Deactivated company ID {company_id}")
        return company, []


# Singleton instance
_company_service = None

def get_company_service() -> CompanyService:
    """Get or create company service singleton."""
    global _company_service
    if _company_service is None:
        _company_service = CompanyService()
    return _company_service

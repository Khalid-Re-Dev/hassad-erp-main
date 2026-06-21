"""
Custom exceptions for Purchases module
"""


class PurchaseError(Exception):
    """Base exception for purchase-related errors"""
    pass


class SupplierNotFoundError(PurchaseError):
    """Raised when supplier is not found"""
    pass


class PONotFoundError(PurchaseError):
    """Raised when purchase order is not found"""
    pass


class InvalidPOStatusError(PurchaseError):
    """Raised when operation is invalid for current PO status"""
    pass


class InsufficientPermissionError(PurchaseError):
    """Raised when user lacks permission for operation"""
    pass


class ApprovalRequiredError(PurchaseError):
    """Raised when approval is required but not obtained"""
    pass


class ThreeWayMatchError(PurchaseError):
    """Raised when 3-way matching fails (PO-GRN-Invoice)"""
    pass

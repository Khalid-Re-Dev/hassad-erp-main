"""
POS Module
Handles point-of-sale operations, sales processing, and cashier interface
"""
from core.pos.schemas import (
    POSItemLine,
    POSTender,
    POSCreateRequest,
    POSCreateResponse,
    POSReturnRequest,
    POSReturnResponse,
)
from core.pos.pos_service import (
    calculate_totals,
    create_pos_sale,
    process_return,
    get_sale_details,
)
from core.pos.payment import (
    validate_payments,
    calculate_change,
)

__all__ = [
    "POSItemLine",
    "POSTender",
    "POSCreateRequest",
    "POSCreateResponse",
    "POSReturnRequest",
    "POSReturnResponse",
    "calculate_totals",
    "create_pos_sale",
    "process_return",
    "get_sale_details",
    "validate_payments",
    "calculate_change",
]

"""
Inventory service functions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Optional
from uuid import UUID
from decimal import Decimal
import uuid

from models.inventory import Product, StockMovement, ProductBatch, MovementType


def calc_weighted_average(
    previous_qty: Decimal,
    previous_cost: Decimal,
    incoming_qty: Decimal,
    incoming_cost: Decimal
) -> Decimal:
    """
    Calculate weighted average unit cost.
    
    Args:
        previous_qty: Previous quantity in stock
        previous_cost: Previous unit cost
        incoming_qty: Incoming quantity
        incoming_cost: Incoming unit cost
        
    Returns:
        New weighted average unit cost (4 decimals)
        
    Example:
        >>> calc_weighted_average(Decimal('100'), Decimal('10.00'), Decimal('50'), Decimal('12.00'))
        Decimal('10.6667')
    """
    if previous_qty + incoming_qty == 0:
        return Decimal('0.0000')
    
    total_cost = (previous_qty * previous_cost) + (incoming_qty * incoming_cost)
    return (total_cost / (previous_qty + incoming_qty)).quantize(Decimal('0.0001'))


def get_product_stock(
    session: Session,
    product_id: UUID,
    branch_id: UUID
) -> Dict:
    """
    Get current stock level and average cost for a product at a branch.
    
    Args:
        session: Database session
        product_id: Product UUID
        branch_id: Branch UUID
        
    Returns:
        Dictionary with available_qty and avg_cost
    """
    # Calculate total IN movements
    in_qty = session.query(
        func.coalesce(func.sum(StockMovement.quantity), 0)
    ).filter(
        StockMovement.product_id == product_id,
        StockMovement.branch_id == branch_id,
        StockMovement.movement_type.in_([MovementType.IN, MovementType.RETURN])
    ).scalar() or Decimal('0.0000')
    
    # Calculate total OUT movements (note: SALE movements are negative)
    out_qty = session.query(
        func.coalesce(func.sum(StockMovement.quantity), 0)
    ).filter(
        StockMovement.product_id == product_id,
        StockMovement.branch_id == branch_id,
        StockMovement.movement_type.in_([MovementType.OUT, MovementType.ADJUSTMENT])
    ).scalar() or Decimal('0.0000')
    
    # SALE movements are stored as negative quantities
    sale_qty = session.query(
        func.coalesce(func.sum(StockMovement.quantity), 0)
    ).filter(
        StockMovement.product_id == product_id,
        StockMovement.branch_id == branch_id,
        StockMovement.movement_type == MovementType.SALE
    ).scalar() or Decimal('0.0000')
    
    available_qty = in_qty + out_qty + sale_qty  # sale_qty is negative
    
    # Calculate weighted average cost from IN movements
    avg_cost = session.query(
        func.avg(StockMovement.unit_cost)
    ).filter(
        StockMovement.product_id == product_id,
        StockMovement.branch_id == branch_id,
        StockMovement.movement_type == MovementType.IN
    ).scalar() or Decimal('0.0000')
    
    return {
        'available_qty': available_qty.quantize(Decimal('0.0001')),
        'avg_cost': Decimal(str(avg_cost)).quantize(Decimal('0.0001'))
    }


def record_stock_movement(
    session: Session,
    product_id: UUID,
    branch_id: UUID,
    movement_type: MovementType,
    quantity: Decimal,
    unit_cost: Decimal,
    reference_type: Optional[str] = None,
    reference_id: Optional[UUID] = None,
    batch_id: Optional[UUID] = None,
    notes: Optional[str] = None
) -> UUID:
    """
    Record a stock movement.
    
    Args:
        session: Database session
        product_id: Product UUID
        branch_id: Branch UUID
        movement_type: Type of movement
        quantity: Quantity (positive for IN, negative for OUT/SALE)
        unit_cost: Unit cost
        reference_type: Reference type (SALE, PURCHASE, etc.)
        reference_id: Reference UUID
        batch_id: Batch UUID if applicable
        notes: Optional notes
        
    Returns:
        UUID of created stock movement
    """
    total_cost = (quantity * unit_cost).quantize(Decimal('0.01'))
    
    movement = StockMovement(
        id=uuid.uuid4(),
        product_id=product_id,
        branch_id=branch_id,
        batch_id=batch_id,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes
    )
    
    session.add(movement)
    session.flush()
    
    return movement.id

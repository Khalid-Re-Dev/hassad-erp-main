"""
Inventory and Product Management models (Phase 3).
"""
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Index, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import enum

from models.base import Base, TimestampMixin


class MovementType(str, enum.Enum):
    """Stock movement types"""
    IN = "IN"  # Inbound (purchase, production)
    OUT = "OUT"  # Outbound (manual)
    SALE = "SALE"  # Sale transaction
    RETURN = "RETURN"  # Customer return
    ADJUSTMENT = "ADJUSTMENT"  # Inventory adjustment
    TRANSFER = "TRANSFER"  # Branch transfer


class Category(Base, TimestampMixin):
    """Product categories"""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    company = relationship("Company")
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
    
    __table_args__ = (
        Index("idx_categories_company", "company_id"),
    )


class Unit(Base, TimestampMixin):
    """Units of measure"""
    __tablename__ = "units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    conversion_to_base = Column(Numeric(10, 4), nullable=False, default=Decimal('1.0000'))
    
    is_base_unit = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    company = relationship("Company")
    
    __table_args__ = (
        Index("idx_units_company", "company_id"),
    )


class Product(Base, TimestampMixin):
    """Products/Items master"""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    base_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    sku = Column(String(100), nullable=False)
    barcode = Column(String(100), nullable=True)
    
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    track_batches = Column(Boolean, default=False, nullable=False)
    track_expiry = Column(Boolean, default=False, nullable=False)
    
    # UOM conversions (JSON: {unit_id: conversion_factor})
    uom_conversions = Column(JSON, nullable=True)
    
    # Default accounting accounts
    default_purchase_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_sales_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    default_stock_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    company = relationship("Company")
    category = relationship("Category", back_populates="products")
    base_unit = relationship("Unit")
    stock_movements = relationship("StockMovement", back_populates="product")
    batches = relationship("ProductBatch", back_populates="product")
    sale_lines = relationship("SaleLine", back_populates="product")
    
    __table_args__ = (
        Index("idx_products_company_sku", "company_id", "sku", unique=True),
        Index("idx_products_barcode", "barcode"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.sku} - {self.name_en}>"


class ProductBatch(Base, TimestampMixin):
    """Product batches for batch tracking"""
    __tablename__ = "product_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    batch_no = Column(String(100), nullable=False)
    received_quantity = Column(Numeric(18, 4), nullable=False)
    available_quantity = Column(Numeric(18, 4), nullable=False)
    
    expiry_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    purchase_price = Column(Numeric(18, 4), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="batches")
    sale_lines = relationship("SaleLine", back_populates="batch")
    
    __table_args__ = (
        Index("idx_batches_product", "product_id"),
        Index("idx_batches_batch_no", "batch_no"),
    )


class StockMovement(Base, TimestampMixin):
    """Stock movements (in/out transactions)"""
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("product_batches.id"), nullable=True)
    
    movement_type = Column(SQLEnum(MovementType), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    total_cost = Column(Numeric(18, 2), nullable=False)
    
    reference_type = Column(String(50), nullable=True)  # SALE, PURCHASE, MANUAL, etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    branch = relationship("Branch")
    batch = relationship("ProductBatch")
    
    __table_args__ = (
        Index("idx_stock_movements_product", "product_id"),
        Index("idx_stock_movements_branch", "branch_id"),
        Index("idx_stock_movements_type", "movement_type"),
        Index("idx_stock_movements_reference", "reference_type", "reference_id"),
    )

    def __repr__(self) -> str:
        return f"<StockMovement {self.movement_type} {self.quantity} of {self.product_id}>"

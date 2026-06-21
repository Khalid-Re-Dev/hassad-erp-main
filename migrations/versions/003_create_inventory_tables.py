"""create inventory tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-27 11:00:00.000000

Phase 3: Inventory & Product Management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_ar', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_categories_company', 'categories', ['company_id'])

    # Create units table
    op.create_table(
        'units',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('conversion_to_base', sa.Numeric(precision=10, scale=4), nullable=False, server_default='1.0000'),
        sa.Column('is_base_unit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_units_company', 'units', ['company_id'])

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('base_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_ar', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('track_batches', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('track_expiry', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('uom_conversions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('default_purchase_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_sales_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_stock_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['base_unit_id'], ['units.id'], ),
        sa.ForeignKeyConstraint(['default_purchase_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['default_sales_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['default_stock_account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_products_company_sku', 'products', ['company_id', 'sku'], unique=True)
    op.create_index('idx_products_barcode', 'products', ['barcode'])

    # Create product_batches table
    op.create_table(
        'product_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_no', sa.String(length=100), nullable=False),
        sa.Column('received_quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('available_quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('expiry_date', sa.String(length=10), nullable=True),
        sa.Column('purchase_price', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_batches_product', 'product_batches', ['product_id'])
    op.create_index('idx_batches_batch_no', 'product_batches', ['batch_no'])

    # Create stock_movements table
    op.create_table(
        'stock_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('movement_type', sa.Enum('IN', 'OUT', 'SALE', 'RETURN', 'ADJUSTMENT', 'TRANSFER', name='movementtype'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['product_batches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_stock_movements_product', 'stock_movements', ['product_id'])
    op.create_index('idx_stock_movements_branch', 'stock_movements', ['branch_id'])
    op.create_index('idx_stock_movements_type', 'stock_movements', ['movement_type'])
    op.create_index('idx_stock_movements_reference', 'stock_movements', ['reference_type', 'reference_id'])


def downgrade() -> None:
    op.drop_index('idx_stock_movements_reference', table_name='stock_movements')
    op.drop_index('idx_stock_movements_type', table_name='stock_movements')
    op.drop_index('idx_stock_movements_branch', table_name='stock_movements')
    op.drop_index('idx_stock_movements_product', table_name='stock_movements')
    op.drop_table('stock_movements')
    op.execute('DROP TYPE movementtype')
    
    op.drop_index('idx_batches_batch_no', table_name='product_batches')
    op.drop_index('idx_batches_product', table_name='product_batches')
    op.drop_table('product_batches')
    
    op.drop_index('idx_products_barcode', table_name='products')
    op.drop_index('idx_products_company_sku', table_name='products')
    op.drop_table('products')
    
    op.drop_index('idx_units_company', table_name='units')
    op.drop_table('units')
    
    op.drop_index('idx_categories_company', table_name='categories')
    op.drop_table('categories')

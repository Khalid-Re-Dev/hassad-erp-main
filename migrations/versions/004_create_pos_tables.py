"""create pos tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('name_ar', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('credit_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('credit_balance', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_customers_company', 'customers', ['company_id'])
    op.create_index('idx_customers_code', 'customers', ['code'])
    
    # Create sales table
    op.create_table(
        'sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('invoice_no', sa.String(50), nullable=False, unique=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=True),
        sa.Column('cashier_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('subtotal', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('discount_total', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('tax_total', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('grand_total', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('global_discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('global_discount_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('journal_entries.id'), nullable=True),
        sa.Column('original_sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales.id'), nullable=True),
        sa.Column('is_return', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('grand_total >= 0', name='check_grand_total_positive'),
    )
    op.create_index('idx_sales_company_branch', 'sales', ['company_id', 'branch_id'])
    op.create_index('idx_sales_invoice_no', 'sales', ['invoice_no'])
    op.create_index('idx_sales_invoice_date', 'sales', ['invoice_date'])
    op.create_index('idx_sales_status', 'sales', ['status'])
    op.create_index('idx_sales_cashier', 'sales', ['cashier_user_id'])
    
    # Create sale_lines table
    op.create_table(
        'sale_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_batches.id'), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 2), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('discount_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('line_total', sa.Numeric(18, 2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(18, 4), nullable=False),
        sa.Column('total_cost', sa.Numeric(18, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('quantity > 0', name='check_quantity_positive'),
        sa.CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
    )
    op.create_index('idx_sale_lines_sale', 'sale_lines', ['sale_id'])
    op.create_index('idx_sale_lines_product', 'sale_lines', ['product_id'])
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales.id'), nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('card_reference', sa.String(100), nullable=True),
        sa.Column('card_type', sa.String(50), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('amount > 0', name='check_payment_amount_positive'),
    )
    op.create_index('idx_payments_sale', 'payments', ['sale_id'])
    op.create_index('idx_payments_method', 'payments', ['method'])
    
    # Create pos_settings table
    op.create_table(
        'pos_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False, unique=True),
        sa.Column('auto_stock_deduct', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('allow_negative_stock', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('auto_post_journal', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('default_cash_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_card_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_receivable_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_revenue_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_vat_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_cogs_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('default_inventory_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('rounding_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('receipt_paper_width', sa.String(10), nullable=False, server_default='80mm'),
        sa.Column('receipt_header_text', sa.Text, nullable=True),
        sa.Column('receipt_footer_text', sa.Text, nullable=True),
        sa.Column('print_receipt_auto', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('default_tax_rate', sa.Numeric(5, 2), nullable=False, server_default='15.00'),
        sa.Column('tax_inclusive', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('allow_partial_payment', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('allow_overpayment', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('allow_returns', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('return_window_days', sa.Integer, nullable=False, server_default='30'),
        sa.Column('printer_device_path', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_pos_settings_company', 'pos_settings', ['company_id'])


def downgrade():
    op.drop_table('pos_settings')
    op.drop_table('payments')
    op.drop_table('sale_lines')
    op.drop_table('sales')
    op.drop_table('customers')

"""create purchases and suppliers tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('default_payment_terms', sa.Numeric(10, 0), server_default='30', nullable=False),
        sa.Column('preferred_currency', sa.String(3), server_default='SAR', nullable=False),
        sa.Column('ledger_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_supplier_company', 'suppliers', ['company_id'])
    op.create_index('idx_supplier_tax_id', 'suppliers', ['tax_id'])
    
    # Create supplier_catalog table
    op.create_table(
        'supplier_catalog',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('supplier_sku', sa.String(100), nullable=True),
        sa.Column('lead_time_days', sa.Numeric(10, 0), server_default='0', nullable=False),
        sa.Column('purchase_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('min_order_qty', sa.Numeric(18, 4), server_default='1', nullable=False),
        sa.Column('is_preferred', sa.Boolean, server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_catalog_supplier_product', 'supplier_catalog', ['supplier_id', 'product_id'])
    
    # Create purchase_orders table
    op.create_table(
        'purchase_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('po_number', sa.String(50), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('subtotal', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('tax_total', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('total_amount', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expected_delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_po_company_branch', 'purchase_orders', ['company_id', 'branch_id'])
    op.create_index('idx_po_supplier', 'purchase_orders', ['supplier_id'])
    op.create_index('idx_po_status', 'purchase_orders', ['status'])
    op.create_index('idx_po_number', 'purchase_orders', ['po_number'])
    
    # Create purchase_order_lines table
    op.create_table(
        'purchase_order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('ordered_qty', sa.Numeric(18, 4), nullable=False),
        sa.Column('received_qty', sa.Numeric(18, 4), server_default='0', nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('line_subtotal', sa.Numeric(18, 2), nullable=False),
        sa.Column('line_tax', sa.Numeric(18, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(18, 2), nullable=False),
        sa.Column('expected_delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_po_line_po', 'purchase_order_lines', ['purchase_order_id'])
    op.create_index('idx_po_line_product', 'purchase_order_lines', ['product_id'])
    
    # Create goods_receipts table
    op.create_table(
        'goods_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('grn_number', sa.String(50), nullable=False, unique=True),
        sa.Column('related_po_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='RECEIVED'),
        sa.Column('received_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_grn_company_branch', 'goods_receipts', ['company_id', 'branch_id'])
    op.create_index('idx_grn_supplier', 'goods_receipts', ['supplier_id'])
    op.create_index('idx_grn_po', 'goods_receipts', ['related_po_id'])
    op.create_index('idx_grn_number', 'goods_receipts', ['grn_number'])
    
    # Create goods_receipt_lines table
    op.create_table(
        'goods_receipt_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('goods_receipt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('goods_receipts.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('po_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_order_lines.id'), nullable=True),
        sa.Column('batch_no', sa.String(100), nullable=True),
        sa.Column('received_qty', sa.Numeric(18, 4), nullable=False),
        sa.Column('accepted_qty', sa.Numeric(18, 4), nullable=False),
        sa.Column('rejected_qty', sa.Numeric(18, 4), server_default='0', nullable=False),
        sa.Column('unit_cost', sa.Numeric(18, 4), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_grn_line_grn', 'goods_receipt_lines', ['goods_receipt_id'])
    op.create_index('idx_grn_line_product', 'goods_receipt_lines', ['product_id'])
    
    # Create purchase_invoices table
    op.create_table(
        'purchase_invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('internal_reference', sa.String(50), nullable=True),
        sa.Column('related_po_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('subtotal', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('tax_total', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('total_amount', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('paid_amount', sa.Numeric(18, 2), server_default='0', nullable=False),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_pi_company_branch', 'purchase_invoices', ['company_id', 'branch_id'])
    op.create_index('idx_pi_supplier', 'purchase_invoices', ['supplier_id'])
    op.create_index('idx_pi_po', 'purchase_invoices', ['related_po_id'])
    op.create_index('idx_pi_status', 'purchase_invoices', ['status'])
    op.create_index('idx_pi_invoice_number', 'purchase_invoices', ['supplier_id', 'invoice_number'])
    
    # Create purchase_invoice_lines table
    op.create_table(
        'purchase_invoice_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('purchase_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_invoices.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('line_subtotal', sa.Numeric(18, 2), nullable=False),
        sa.Column('line_tax', sa.Numeric(18, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(18, 2), nullable=False),
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_pi_line_invoice', 'purchase_invoice_lines', ['purchase_invoice_id'])
    op.create_index('idx_pi_line_product', 'purchase_invoice_lines', ['product_id'])
    
    # Create approval_requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('approval_level', sa.Numeric(2, 0), server_default='1', nullable=False),
        sa.Column('request_notes', sa.Text, nullable=True),
        sa.Column('approval_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_approval_entity', 'approval_requests', ['entity_type', 'entity_id'])
    op.create_index('idx_approval_status', 'approval_requests', ['status'])
    op.create_index('idx_approval_approver', 'approval_requests', ['approver_id'])
    
    # Create supplier_payments table
    op.create_table(
        'supplier_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('purchase_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_invoices.id'), nullable=True),
        sa.Column('payment_number', sa.String(50), nullable=False, unique=True),
        sa.Column('payment_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('paid_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_payment_supplier', 'supplier_payments', ['supplier_id'])
    op.create_index('idx_payment_invoice', 'supplier_payments', ['purchase_invoice_id'])
    op.create_index('idx_payment_date', 'supplier_payments', ['payment_date'])


def downgrade() -> None:
    op.drop_table('supplier_payments')
    op.drop_table('approval_requests')
    op.drop_table('purchase_invoice_lines')
    op.drop_table('purchase_invoices')
    op.drop_table('goods_receipt_lines')
    op.drop_table('goods_receipts')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('supplier_catalog')
    op.drop_table('suppliers')

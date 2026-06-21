"""create accounting tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-27 10:00:00.000000

Phase 2: Accounting Engine - Chart of Accounts and Journal Entries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_ar', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.Enum('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE', name='accounttype'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_accounts_company_code', 'accounts', ['company_id', 'code'], unique=True)
    op.create_index('idx_accounts_type', 'accounts', ['account_type'])

    # Create journal_entries table
    op.create_table(
        'journal_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_number', sa.String(length=50), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('entry_date', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('posted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('posted_at', sa.String(length=30), nullable=True),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['posted_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_journal_company_number', 'journal_entries', ['company_id', 'entry_number'], unique=True)
    op.create_index('idx_journal_posted', 'journal_entries', ['posted'])
    op.create_index('idx_journal_date', 'journal_entries', ['entry_date'])

    # Create journal_lines table
    op.create_table(
        'journal_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('debit', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0.00'),
        sa.Column('credit', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0.00'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=30), nullable=False),
        sa.Column('updated_at', sa.String(length=30), nullable=False),
        sa.Column('deleted_at', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_journal_lines_entry', 'journal_lines', ['journal_entry_id'])
    op.create_index('idx_journal_lines_account', 'journal_lines', ['account_id'])


def downgrade() -> None:
    op.drop_index('idx_journal_lines_account', table_name='journal_lines')
    op.drop_index('idx_journal_lines_entry', table_name='journal_lines')
    op.drop_table('journal_lines')
    
    op.drop_index('idx_journal_date', table_name='journal_entries')
    op.drop_index('idx_journal_posted', table_name='journal_entries')
    op.drop_index('idx_journal_company_number', table_name='journal_entries')
    op.drop_table('journal_entries')
    
    op.drop_index('idx_accounts_type', table_name='accounts')
    op.drop_index('idx_accounts_company_code', table_name='accounts')
    op.drop_table('accounts')
    
    op.execute('DROP TYPE accounttype')

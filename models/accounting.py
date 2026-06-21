"""
Accounting models for double-entry bookkeeping system (Phase 2).
"""
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Index, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import enum

from models.base import Base, TimestampMixin


class AccountType(str, enum.Enum):
    """Account types for chart of accounts"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class Account(Base, TimestampMixin):
    """
    Chart of Accounts - defines all accounting accounts
    """
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    code = Column(String(50), nullable=False)
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    
    account_type = Column(SQLEnum(AccountType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System accounts cannot be deleted
    
    description = Column(Text, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="accounts")
    parent = relationship("Account", remote_side=[id], backref="children")
    journal_lines = relationship("JournalLine", back_populates="account")
    payments = relationship("Payment", back_populates="account")
    
    __table_args__ = (
        Index("idx_accounts_company_code", "company_id", "code", unique=True),
        Index("idx_accounts_type", "account_type"),
    )

    def __repr__(self) -> str:
        return f"<Account {self.code} - {self.name_en}>"


class JournalEntry(Base, TimestampMixin):
    """
    Journal Entry header - represents a complete accounting transaction
    """
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    
    entry_number = Column(String(50), nullable=False)
    reference = Column(String(255), nullable=False)
    entry_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    
    description = Column(Text, nullable=True)
    
    posted = Column(Boolean, default=False, nullable=False)
    posted_at = Column(String(30), nullable=True)
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Version for conflict detection
    version = Column(String(64), nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    company = relationship("Company")
    branch = relationship("Branch")
    lines = relationship("JournalLine", back_populates="journal_entry", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    poster = relationship("User", foreign_keys=[posted_by])
    sales = relationship("Sale", back_populates="journal_entry")
    
    __table_args__ = (
        Index("idx_journal_company_number", "company_id", "entry_number", unique=True),
        Index("idx_journal_posted", "posted"),
        Index("idx_journal_date", "entry_date"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_number} - {self.reference}>"


class JournalLine(Base, TimestampMixin):
    """
    Journal Entry line - individual debit/credit entries
    """
    __tablename__ = "journal_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    debit = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    credit = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    description = Column(Text, nullable=True)
    
    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")
    
    __table_args__ = (
        Index("idx_journal_lines_entry", "journal_entry_id"),
        Index("idx_journal_lines_account", "account_id"),
    )

    def __repr__(self) -> str:
        return f"<JournalLine {self.account_id} Dr:{self.debit} Cr:{self.credit}>"

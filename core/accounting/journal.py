"""
Journal entry creation and management.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timezone
from decimal import Decimal
import uuid

from models.accounting import JournalEntry, JournalLine, Account
from core.accounting.schemas import JournalLineSchema


class AccountingError(Exception):
    """Base exception for accounting operations"""
    pass


class InvalidAccountError(AccountingError):
    """Raised when account is invalid"""
    pass


class ImbalanceError(AccountingError):
    """Raised when journal entry is not balanced"""
    pass


def _generate_entry_number(session: Session, company_id: UUID) -> str:
    """Generate next journal entry number"""
    year = datetime.now(timezone.utc).year
    prefix = f"JE-{year}-"
    
    last_entry = session.query(JournalEntry).filter(
        JournalEntry.company_id == company_id,
        JournalEntry.entry_number.like(f"{prefix}%")
    ).order_by(JournalEntry.entry_number.desc()).first()
    
    if last_entry:
        try:
            last_num = int(last_entry.entry_number.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:05d}"


def create_journal_entry(
    session: Session,
    company_id: UUID,
    branch_id: UUID,
    reference: str,
    lines: List[JournalLineSchema],
    posted: bool = False,
    entry_date: Optional[date] = None,
    created_by: Optional[UUID] = None,
    description: Optional[str] = None
) -> UUID:
    """
    Create a journal entry with validation.
    
    Args:
        session: Database session
        company_id: Company UUID
        branch_id: Branch UUID
        reference: Reference description
        lines: List of journal lines
        posted: Whether to post immediately
        entry_date: Entry date (defaults to today)
        created_by: User creating the entry
        description: Optional description
        
    Returns:
        UUID of created journal entry
        
    Raises:
        ImbalanceError: If debits != credits
        InvalidAccountError: If account doesn't exist or belong to company
    """
    # Validate balance
    total_debit = sum(line.debit for line in lines)
    total_credit = sum(line.credit for line in lines)
    
    if total_debit != total_credit:
        raise ImbalanceError(
            f"Journal entry not balanced: Debits={total_debit}, Credits={total_credit}"
        )
    
    # Validate all accounts exist and belong to company
    account_ids = [line.account_id for line in lines]
    accounts = session.query(Account).filter(
        Account.id.in_(account_ids),
        Account.company_id == company_id
    ).all()
    
    if len(accounts) != len(set(account_ids)):
        raise InvalidAccountError("One or more accounts not found or don't belong to company")
    
    # Generate entry number
    entry_number = _generate_entry_number(session, company_id)
    
    # Create journal entry
    entry = JournalEntry(
        id=uuid.uuid4(),
        company_id=company_id,
        branch_id=branch_id,
        entry_number=entry_number,
        reference=reference,
        entry_date=str(entry_date or date.today()),
        description=description,
        posted=posted,
        created_by=created_by or uuid.uuid4(),  # Placeholder if not provided
    )
    
    session.add(entry)
    session.flush()
    
    # Create journal lines
    for line in lines:
        journal_line = JournalLine(
            id=uuid.uuid4(),
            journal_entry_id=entry.id,
            account_id=line.account_id,
            debit=line.debit,
            credit=line.credit,
            description=line.description
        )
        session.add(journal_line)
    
    session.flush()
    return entry.id


def get_journal_entry(session: Session, journal_id: UUID) -> JournalEntry:
    """Get journal entry by ID"""
    entry = session.query(JournalEntry).filter(JournalEntry.id == journal_id).first()
    if not entry:
        raise AccountingError(f"Journal entry {journal_id} not found")
    return entry

"""
Journal entry posting and reversal logic.
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from typing import List

from models.accounting import JournalEntry, JournalLine
from models.audit_log import AuditLog
from core.accounting.journal import get_journal_entry, AccountingError, create_journal_entry
from core.accounting.schemas import JournalLineSchema


def post_journal_entry(
    session: Session,
    journal_id: UUID,
    posted_by_user_id: UUID
) -> JournalEntry:
    """
    Post a journal entry (make it permanent).
    
    Args:
        session: Database session
        journal_id: Journal entry UUID
        posted_by_user_id: User posting the entry
        
    Returns:
        Posted JournalEntry
        
    Raises:
        AccountingError: If entry already posted or validation fails
    """
    entry = get_journal_entry(session, journal_id)
    
    if entry.posted:
        raise AccountingError(f"Journal entry {journal_id} already posted")
    
    # Mark as posted
    entry.posted = True
    entry.posted_at = datetime.now(timezone.utc).isoformat()
    entry.posted_by = posted_by_user_id
    
    # Create audit log
    audit = AuditLog(
        company_id=entry.company_id,
        user_id=posted_by_user_id,
        action="POST_JOURNAL",
        entity_type="JournalEntry",
        entity_id=entry.id,
        changes={"posted": True, "entry_number": entry.entry_number}
    )
    session.add(audit)
    
    session.flush()
    return entry


def reverse_journal_entry(
    session: Session,
    journal_id: UUID,
    reversed_by_user_id: UUID,
    reversal_date: str = None
) -> UUID:
    """
    Reverse a journal entry by creating an inverse entry.
    
    Args:
        session: Database session
        journal_id: Original journal entry UUID
        reversed_by_user_id: User reversing the entry
        reversal_date: Date for reversal (defaults to today)
        
    Returns:
        UUID of reversal journal entry
        
    Raises:
        AccountingError: If entry not posted or already reversed
    """
    original = get_journal_entry(session, journal_id)
    
    if not original.posted:
        raise AccountingError("Cannot reverse unposted journal entry")
    
    # Create reverse lines (swap debit/credit)
    reverse_lines = []
    for line in original.lines:
        reverse_lines.append(JournalLineSchema(
            account_id=line.account_id,
            debit=line.credit,  # Swap
            credit=line.debit,  # Swap
            description=f"Reversal of {original.entry_number}: {line.description or ''}"
        ))
    
    # Create reversal entry
    reversal_id = create_journal_entry(
        session=session,
        company_id=original.company_id,
        branch_id=original.branch_id,
        reference=f"REV-{original.reference}",
        lines=reverse_lines,
        posted=True,
        entry_date=reversal_date,
        created_by=reversed_by_user_id,
        description=f"Reversal of {original.entry_number}"
    )
    
    # Post immediately
    post_journal_entry(session, reversal_id, reversed_by_user_id)
    
    # Create audit log
    audit = AuditLog(
        company_id=original.company_id,
        user_id=reversed_by_user_id,
        action="REVERSE_JOURNAL",
        entity_type="JournalEntry",
        entity_id=original.id,
        changes={"reversed_by": str(reversal_id)}
    )
    session.add(audit)
    
    session.flush()
    return reversal_id

"""
Accounting service utilities.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from models.accounting import Account, JournalEntry, JournalLine, AccountType


def compute_trial_balance(
    session: Session,
    company_id: UUID,
    as_of_date: Optional[date] = None
) -> List[Dict]:
    """
    Compute trial balance for a company.
    
    Args:
        session: Database session
        company_id: Company UUID
        as_of_date: Date to compute balance (defaults to today)
        
    Returns:
        List of account balances with debit/credit totals
    """
    as_of = as_of_date or date.today()
    
    # Get all accounts
    accounts = session.query(Account).filter(
        Account.company_id == company_id,
        Account.deleted_at.is_(None)
    ).order_by(Account.code).all()
    
    trial_balance = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')
    
    for account in accounts:
        # Sum debits and credits from posted journal lines
        debit_sum = session.query(
            func.coalesce(func.sum(JournalLine.debit), 0)
        ).join(JournalEntry).filter(
            JournalLine.account_id == account.id,
            JournalEntry.posted == True,
            JournalEntry.entry_date <= str(as_of)
        ).scalar() or Decimal('0.00')
        
        credit_sum = session.query(
            func.coalesce(func.sum(JournalLine.credit), 0)
        ).join(JournalEntry).filter(
            JournalLine.account_id == account.id,
            JournalEntry.posted == True,
            JournalEntry.entry_date <= str(as_of)
        ).scalar() or Decimal('0.00')
        
        if debit_sum == credit_sum == Decimal('0.00'):
            continue
        
        trial_balance.append({
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name_en,
            'account_type': account.account_type.value,
            'debit': debit_sum,
            'credit': credit_sum
        })
        
        total_debits += debit_sum
        total_credits += credit_sum
    
    return {
        'accounts': trial_balance,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'balanced': total_debits == total_credits
    }


def validate_balance_integrity(session: Session, company_id: UUID) -> bool:
    """
    Validate that all posted journal entries are balanced.
    
    Args:
        session: Database session
        company_id: Company UUID
        
    Returns:
        True if all entries balanced, False otherwise
    """
    entries = session.query(JournalEntry).filter(
        JournalEntry.company_id == company_id,
        JournalEntry.posted == True
    ).all()
    
    for entry in entries:
        total_debit = sum(line.debit for line in entry.lines)
        total_credit = sum(line.credit for line in entry.lines)
        
        if total_debit != total_credit:
            return False
    
    return True

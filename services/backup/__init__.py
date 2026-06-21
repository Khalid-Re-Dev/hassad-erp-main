"""
Hassad ERP System - Backup & Restore Module
Phase 6: Backup, Sync & Packaging

This module provides encrypted backup and restore capabilities with:
- Full database backups (pg_dump)
- Partial/config backups (settings, users, COA, products)
- AES-256 encryption
- Scheduled backup support
- Retention policies
"""

from .backup_service import (
    BackupService,
    create_backup,
    restore_backup,
    list_backups,
    delete_old_backups
)
from .scheduler import BackupScheduler, schedule_backup

__all__ = [
    'BackupService',
    'create_backup',
    'restore_backup',
    'list_backups',
    'delete_old_backups',
    'BackupScheduler',
    'schedule_backup',
]

"""
Backup scheduling utilities.
Provides hooks for cron/Windows Task Scheduler integration.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path

from .backup_service import BackupService


class BackupScheduler:
    """
    Backup scheduler with retention policies.
    
    Note: This provides the logic for scheduled backups.
    Actual scheduling should be done via:
    - Linux/Mac: crontab
    - Windows: Task Scheduler
    - Or use APScheduler library for in-process scheduling
    """

    def __init__(self, backup_dir: str = "./backups"):
        self.service = BackupService(backup_dir)

    def run_scheduled_backup(
        self,
        backup_type: str = 'full',
        encryption_key: Optional[str] = None,
        retention_days: int = 30,
        retention_count: int = 10
    ) -> dict:
        """
        Run a scheduled backup with retention policy.
        
        Args:
            backup_type: 'full' or 'partial'
            encryption_key: Master encryption key
            retention_days: Delete backups older than N days
            retention_count: Keep at least N most recent backups
            
        Returns:
            Dict with backup metadata and cleanup results
        """
        from core.database import SessionLocal
        
        # Create backup
        session = SessionLocal()
        try:
            metadata = self.service.create_backup(
                session,
                backup_type=backup_type,
                encryption_key=encryption_key
            )
        finally:
            session.close()
        
        # Apply retention policy
        deleted = self._apply_retention_policy(retention_days, retention_count)
        
        return {
            'backup': metadata,
            'cleanup': {
                'deleted_count': deleted,
                'retention_days': retention_days,
                'retention_count': retention_count
            }
        }

    def _apply_retention_policy(self, retention_days: int, retention_count: int) -> int:
        """Apply retention policy to delete old backups."""
        backups = self.service.list_backups()
        
        if len(backups) <= retention_count:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        
        # Keep at least retention_count backups
        for backup in backups[retention_count:]:
            backup_date = datetime.fromisoformat(backup['created'])
            
            if backup_date < cutoff_date:
                try:
                    Path(backup['path']).unlink()
                    deleted += 1
                except Exception as e:
                    print(f"Failed to delete {backup['filename']}: {e}")
        
        return deleted


def schedule_backup(
    backup_type: str = 'full',
    encryption_key: Optional[str] = None,
    retention_days: int = 30
) -> dict:
    """
    Convenience function for scheduled backup execution.
    
    This function is designed to be called by cron or Task Scheduler.
    
    Example crontab entry (daily at 2 AM):
        0 2 * * * cd /path/to/hassad && python -c "from services.backup import schedule_backup; schedule_backup()"
    
    Example Windows Task Scheduler:
        Program: python
        Arguments: -c "from services.backup import schedule_backup; schedule_backup()"
        Start in: C:\\path\\to\\hassad
    """
    encryption_key = encryption_key or os.getenv('BACKUP_MASTER_KEY')
    
    scheduler = BackupScheduler()
    return scheduler.run_scheduled_backup(
        backup_type=backup_type,
        encryption_key=encryption_key,
        retention_days=retention_days
    )

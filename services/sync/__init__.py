"""
Hassad ERP System - Branch Synchronization Module
Phase 6: Backup, Sync & Packaging

This module provides branch-to-branch data synchronization with:
- Export/import of transactional data
- Conflict detection and resolution
- HMAC signatures for data integrity
- Offline-first design
"""

from .sync_service import (
    SyncService,
    export_sync_data,
    import_sync_data,
    create_sync_envelope
)
from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy

__all__ = [
    'SyncService',
    'export_sync_data',
    'import_sync_data',
    'create_sync_envelope',
    'ConflictResolver',
    'ConflictResolutionStrategy',
]

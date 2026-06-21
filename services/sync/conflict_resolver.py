"""
Conflict resolution strategies for branch synchronization.
"""

from enum import Enum
from typing import Dict, Any, List
from datetime import datetime


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving sync conflicts."""
    LATEST_WINS = "latest_wins"  # Most recent timestamp wins
    LOCAL_WINS = "local_wins"  # Keep local data, ignore remote
    REMOTE_WINS = "remote_wins"  # Accept remote data, overwrite local
    MANUAL = "manual"  # Flag for manual resolution


class ConflictResolver:
    """
    Resolves conflicts between local and remote data during sync.
    
    Conflicts occur when:
    - Same entity modified in both branches
    - Version hashes don't match
    - Timestamps indicate concurrent modifications
    """

    def resolve_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        strategy: ConflictResolutionStrategy
    ) -> Dict[str, Any]:
        """
        Resolve a conflict between local and remote data.
        
        Args:
            local_data: Local entity data
            remote_data: Remote entity data
            strategy: Resolution strategy
            
        Returns:
            Resolved data to use
        """
        if strategy == ConflictResolutionStrategy.LOCAL_WINS:
            return local_data
        
        elif strategy == ConflictResolutionStrategy.REMOTE_WINS:
            return remote_data
        
        elif strategy == ConflictResolutionStrategy.LATEST_WINS:
            local_updated = self._parse_timestamp(local_data.get('updated_at'))
            remote_updated = self._parse_timestamp(remote_data.get('updated_at'))
            
            if remote_updated and local_updated:
                return remote_data if remote_updated > local_updated else local_data
            
            return remote_data if remote_updated else local_data
        
        elif strategy == ConflictResolutionStrategy.MANUAL:
            # Return both for manual resolution
            return {
                'requires_manual_resolution': True,
                'local': local_data,
                'remote': remote_data
            }
        
        return local_data

    def detect_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> bool:
        """
        Detect if there's a conflict between local and remote data.
        
        Returns:
            True if conflict detected
        """
        # Check version hash
        if 'version_hash' in local_data and 'version_hash' in remote_data:
            if local_data['version_hash'] != remote_data['version_hash']:
                return True
        
        # Check timestamps
        local_updated = self._parse_timestamp(local_data.get('updated_at'))
        remote_updated = self._parse_timestamp(remote_data.get('updated_at'))
        
        if local_updated and remote_updated:
            # If both modified recently, it's a conflict
            time_diff = abs((local_updated - remote_updated).total_seconds())
            if time_diff < 60:  # Within 1 minute
                return True
        
        return False

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Parse timestamp string to datetime."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        
        if isinstance(timestamp_str, str):
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                pass
        
        return None

"""Backup and restore functionality."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def create_backup(db_path: Path, backup_dir: Path) -> Optional[Path]:
    """Create a backup of the database.
    
    Args:
        db_path: Path to database file
        backup_dir: Directory to store backups
        
    Returns:
        Path to backup file, or None if failed
    """
    if not db_path.exists():
        logger.error("Database file not found: %s", db_path)
        return None
    
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"promirror_backup_{timestamp}.db"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(db_path, backup_path)
        
        logger.info("Created backup: %s", backup_path)
        return backup_path
    except Exception as e:
        logger.error("Error creating backup: %s", e, exc_info=True)
        return None


def restore_backup(backup_path: Path, db_path: Path) -> bool:
    """Restore database from backup.
    
    Args:
        backup_path: Path to backup file
        db_path: Path to database file to restore
        
    Returns:
        True if successful, False otherwise
    """
    if not backup_path.exists():
        logger.error("Backup file not found: %s", backup_path)
        return False
    
    try:
        # Create backup of current database before restore
        if db_path.exists():
            current_backup = db_path.parent / f"{db_path.stem}_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, current_backup)
            logger.info("Created safety backup: %s", current_backup)
        
        shutil.copy2(backup_path, db_path)
        
        logger.info("Restored database from backup: %s", backup_path)
        return True
    except Exception as e:
        logger.error("Error restoring backup: %s", e, exc_info=True)
        return False


def list_backups(backup_dir: Path) -> list[Path]:
    """List available backup files.
    
    Args:
        backup_dir: Directory containing backups
        
    Returns:
        List of backup file paths, sorted by modification time (newest first)
    """
    if not backup_dir.exists():
        return []
    
    backups = sorted(
        backup_dir.glob("promirror_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    
    return backups


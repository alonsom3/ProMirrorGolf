"""Comprehensive project cleanup script."""

import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def remove_pycache():
    """Remove all __pycache__ directories."""
    removed = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = Path(root) / '__pycache__'
            try:
                shutil.rmtree(cache_dir)
                removed += 1
                logger.info(f"Removed: {cache_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove {cache_dir}: {e}")
    return removed

def remove_temp_files():
    """Remove temporary test files."""
    temp_files = [
        'test.db',
        'test_shot_sender.py',
    ]
    
    removed = 0
    for file_path in temp_files:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                removed += 1
                logger.info(f"Removed: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove {path}: {e}")
    return removed

def main():
    """Main cleanup function."""
    logger.info("Starting project cleanup...")
    logger.info("=" * 60)
    
    pycache_count = remove_pycache()
    temp_count = remove_temp_files()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Cleanup complete:")
    logger.info(f"  - Removed {pycache_count} __pycache__ directories")
    logger.info(f"  - Removed {temp_count} temporary files")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()


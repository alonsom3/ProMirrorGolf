"""Column preferences manager for table customization."""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ColumnPreferencesManager:
    """Manages column visibility and order preferences for tables."""
    
    def __init__(self, config_file: Path) -> None:
        """Initialize column preferences manager."""
        self.config_file = config_file
        self.preferences: dict[str, dict] = {}  # table_id -> {visible_columns: [], column_order: []}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load column preferences from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.preferences = json.load(f)
                logger.debug("Loaded column preferences from %s", self.config_file)
            except Exception as e:
                logger.warning("Failed to load column preferences: %s, using defaults", e)
                self.preferences = {}
        else:
            self.preferences = {}
            self._save_config()
    
    def _save_config(self) -> None:
        """Save column preferences to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2)
            logger.info("Saved column preferences to %s", self.config_file)
        except Exception as e:
            logger.error("Failed to save column preferences: %s", e, exc_info=True)
    
    def get_preferences(self, table_id: str) -> dict:
        """Get preferences for a table."""
        return self.preferences.get(table_id, {
            "visible_columns": None,  # None means all visible
            "column_order": None,  # None means default order
        })
    
    def save_preferences(self, table_id: str, visible_columns: Optional[list[int]], column_order: Optional[list[int]]) -> None:
        """Save preferences for a table."""
        self.preferences[table_id] = {
            "visible_columns": visible_columns,
            "column_order": column_order,
        }
        self._save_config()


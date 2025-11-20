"""Recent shots tracking functionality."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RecentShotsTracker:
    """Tracks recently viewed shots."""
    
    def __init__(self, cache_file: Path, max_items: int = 20):
        self.cache_file = cache_file
        self.max_items = max_items
        self.recent_shots: list[dict] = []
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load recent shots from cache file."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.recent_shots = data.get("recent_shots", [])
        except Exception as e:
            logger.error("Error loading recent shots cache: %s", e)
            self.recent_shots = []
    
    def _save_cache(self) -> None:
        """Save recent shots to cache file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {"recent_shots": self.recent_shots},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error("Error saving recent shots cache: %s", e)
    
    def add_shot(self, shot_id: int, session_id: int, shot_data: Optional[dict] = None) -> None:
        """Add a shot to recent list."""
        # Remove if already exists
        self.recent_shots = [s for s in self.recent_shots if s.get("shot_id") != shot_id]
        
        # Add to front
        entry = {
            "shot_id": shot_id,
            "session_id": session_id,
            "viewed_at": datetime.now().isoformat(),
            "shot_data": shot_data or {},
        }
        self.recent_shots.insert(0, entry)
        
        # Limit size
        if len(self.recent_shots) > self.max_items:
            self.recent_shots = self.recent_shots[:self.max_items]
        
        self._save_cache()
    
    def get_recent_shots(self, limit: Optional[int] = None) -> list[dict]:
        """Get recent shots list."""
        shots = self.recent_shots.copy()
        if limit:
            shots = shots[:limit]
        return shots
    
    def clear(self) -> None:
        """Clear recent shots list."""
        self.recent_shots = []
        self._save_cache()


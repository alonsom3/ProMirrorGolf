"""Smart filter management for saving and reusing filter combinations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FilterPreset:
    """Represents a saved filter preset."""
    
    def __init__(
        self,
        name: str,
        query: str = "",
        quick_filter: str = "all",
        club_filter: Optional[str] = None,
        date_range: Optional[tuple] = None,
    ):
        self.name = name
        self.query = query
        self.quick_filter = quick_filter
        self.club_filter = club_filter
        self.date_range = date_range
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "query": self.query,
            "quick_filter": self.quick_filter,
            "club_filter": self.club_filter,
            "date_range": self.date_range,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FilterPreset":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            query=data.get("query", ""),
            quick_filter=data.get("quick_filter", "all"),
            club_filter=data.get("club_filter"),
            date_range=tuple(data["date_range"]) if data.get("date_range") else None,
        )


class FilterManager:
    """Manages saved filter presets."""
    
    def __init__(self, presets_file: Path):
        self.presets_file = presets_file
        self.presets: list[FilterPreset] = []
        self._load_presets()
    
    def _load_presets(self) -> None:
        """Load presets from file."""
        if not self.presets_file.exists():
            return
        
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.presets = [FilterPreset.from_dict(p) for p in data.get("presets", [])]
        except Exception as e:
            logger.error("Error loading filter presets: %s", e)
            self.presets = []
    
    def _save_presets(self) -> None:
        """Save presets to file."""
        try:
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {"presets": [p.to_dict() for p in self.presets]},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error("Error saving filter presets: %s", e)
    
    def add_preset(self, preset: FilterPreset) -> None:
        """Add a new preset."""
        # Remove existing preset with same name
        self.presets = [p for p in self.presets if p.name != preset.name]
        self.presets.append(preset)
        self._save_presets()
    
    def remove_preset(self, name: str) -> None:
        """Remove a preset by name."""
        self.presets = [p for p in self.presets if p.name != name]
        self._save_presets()
    
    def get_preset(self, name: str) -> Optional[FilterPreset]:
        """Get a preset by name."""
        for preset in self.presets:
            if preset.name == name:
                return preset
        return None
    
    def list_presets(self) -> list[FilterPreset]:
        """List all presets."""
        return self.presets.copy()


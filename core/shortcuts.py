"""Keyboard shortcut management system."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ShortcutManager:
    """Manages keyboard shortcuts with save/load functionality."""
    
    # Default shortcuts for each window/context
    DEFAULT_SHORTCUTS = {
        "main_window": {
            "start_session": "Ctrl+S",
            "stop_session": "Ctrl+Shift+S",
            "browse_sessions": "Ctrl+B",
            "analysis": "Ctrl+A",
            "comparison": "Ctrl+C",
            "settings": "Ctrl+,",
            "review_shot": "Return",
            "delete_shot": "Delete",
        },
        "shot_review": {
            "play_pause": "Space",
            "stop": "S",
            "rewind": "Left",
            "forward": "Right",
            "seek_backward": "Ctrl+Left",
            "seek_forward": "Ctrl+Right",
            "speed_0.1x": "1",
            "speed_0.25x": "2",
            "speed_0.5x": "3",
            "speed_1x": "4",
            "speed_2x": "5",
            "speed_4x": "6",
            "toggle_favorite": "F",
            "edit_tags": "T",
            "edit_notes": "N",
            "tool_freehand": "D",
            "tool_swing_plane": "P",
            "tool_reference": "R",
            "tool_select": "E",
            "clear_drawings": "C",
            "pick_color": "Ctrl+C",
        },
    }
    
    def __init__(self, config_file: Path) -> None:
        """Initialize shortcut manager with config file."""
        self.config_file = config_file
        self.shortcuts: dict[str, dict[str, str]] = {}
        self._load_shortcuts()
    
    def _load_shortcuts(self) -> None:
        """Load shortcuts from config file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.shortcuts = json.load(f)
                logger.info("Loaded shortcuts from %s", self.config_file)
            except Exception as e:
                logger.warning("Failed to load shortcuts: %s, using defaults", e)
                self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
        else:
            self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
            self._save_shortcuts()
    
    def _save_shortcuts(self) -> None:
        """Save shortcuts to config file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.shortcuts, f, indent=2)
            logger.info("Saved shortcuts to %s", self.config_file)
        except Exception as e:
            logger.error("Failed to save shortcuts: %s", e, exc_info=True)
    
    def get_shortcut(self, context: str, action: str) -> str:
        """Get shortcut for a specific action in a context."""
        return self.shortcuts.get(context, {}).get(action, "")
    
    def set_shortcut(self, context: str, action: str, key_sequence: str) -> bool:
        """Set shortcut for an action. Returns True if successful."""
        if context not in self.shortcuts:
            self.shortcuts[context] = {}
        self.shortcuts[context][action] = key_sequence
        self._save_shortcuts()
        return True
    
    def get_all_shortcuts(self) -> dict[str, dict[str, str]]:
        """Get all shortcuts."""
        return self.shortcuts.copy()
    
    def get_context_shortcuts(self, context: str) -> dict[str, str]:
        """Get all shortcuts for a specific context."""
        return self.shortcuts.get(context, {}).copy()
    
    def reset_to_defaults(self, context: Optional[str] = None) -> None:
        """Reset shortcuts to defaults for a context or all contexts."""
        if context:
            if context in self.DEFAULT_SHORTCUTS:
                self.shortcuts[context] = self.DEFAULT_SHORTCUTS[context].copy()
        else:
            self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
        self._save_shortcuts()
    
    def export_shortcuts(self, export_path: Path) -> bool:
        """Export shortcuts to a file."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.shortcuts, f, indent=2)
            logger.info("Exported shortcuts to %s", export_path)
            return True
        except Exception as e:
            logger.error("Failed to export shortcuts: %s", e, exc_info=True)
            return False
    
    def import_shortcuts(self, import_path: Path) -> bool:
        """Import shortcuts from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            self.shortcuts.update(imported)
            self._save_shortcuts()
            logger.info("Imported shortcuts from %s", import_path)
            return True
        except Exception as e:
            logger.error("Failed to import shortcuts: %s", e, exc_info=True)
            return False


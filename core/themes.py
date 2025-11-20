"""Custom theme management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Theme:
    """Represents a custom theme."""
    
    def __init__(self, name: str, colors: dict):
        self.name = name
        self.colors = colors
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "colors": self.colors,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Theme":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            colors=data.get("colors", {}),
        )
    
    def to_stylesheet(self) -> str:
        """Convert to Qt stylesheet."""
        # This is a simplified version - full implementation would map all colors
        bg = self.colors.get("background", "#0f1116")
        fg = self.colors.get("foreground", "#c9d1d9")
        accent = self.colors.get("accent", "#ff4d4d")
        
        return f"""
            QWidget {{
                background-color: {bg};
                color: {fg};
            }}
            QPushButton {{
                background-color: {accent};
                color: #ffffff;
            }}
        """


class ThemeManager:
    """Manages custom themes."""
    
    def __init__(self, themes_file: Path):
        self.themes_file = themes_file
        self.themes: list[Theme] = []
        self.current_theme: Optional[str] = None
        self._load_themes()
    
    def _load_themes(self) -> None:
        """Load themes from file."""
        if not self.themes_file.exists():
            self._create_default_themes()
            return
        
        try:
            with open(self.themes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.themes = [Theme.from_dict(t) for t in data.get("themes", [])]
                self.current_theme = data.get("current_theme")
        except Exception as e:
            logger.error("Error loading themes: %s", e)
            self._create_default_themes()
    
    def _create_default_themes(self) -> None:
        """Create default themes."""
        self.themes = [
            Theme("Dark", {
                "background": "#0f1116",
                "foreground": "#c9d1d9",
                "accent": "#ff4d4d",
            }),
            Theme("Light", {
                "background": "#ffffff",
                "foreground": "#000000",
                "accent": "#0066cc",
            }),
        ]
        self.current_theme = "Dark"
        self._save_themes()
    
    def _save_themes(self) -> None:
        """Save themes to file."""
        try:
            self.themes_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "themes": [t.to_dict() for t in self.themes],
                        "current_theme": self.current_theme,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error("Error saving themes: %s", e)
    
    def add_theme(self, theme: Theme) -> None:
        """Add a new theme."""
        # Remove existing theme with same name
        self.themes = [t for t in self.themes if t.name != theme.name]
        self.themes.append(theme)
        self._save_themes()
    
    def remove_theme(self, name: str) -> None:
        """Remove a theme."""
        self.themes = [t for t in self.themes if t.name != name]
        if self.current_theme == name:
            self.current_theme = self.themes[0].name if self.themes else None
        self._save_themes()
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get a theme by name."""
        for theme in self.themes:
            if theme.name == name:
                return theme
        return None
    
    def set_current_theme(self, name: str) -> None:
        """Set current theme."""
        if self.get_theme(name):
            self.current_theme = name
            self._save_themes()
            # Clear caches in app modules when theme changes
            try:
                from app.design_constants import clear_colors_cache
                from app.theme import clear_theme_cache
                clear_colors_cache()
                clear_theme_cache()
            except ImportError:
                pass  # Ignore if modules aren't loaded yet


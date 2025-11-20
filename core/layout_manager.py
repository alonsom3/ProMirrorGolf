"""Layout management for saving and loading window layouts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LayoutManager:
    """Manages window layouts and panel arrangements."""
    
    def __init__(self, layouts_file: Path):
        """Initialize layout manager.
        
        Args:
            layouts_file: Path to JSON file storing layouts
        """
        self.layouts_file = layouts_file
        self.layouts: dict[str, dict] = {}
        self._load_layouts()
    
    def _load_layouts(self) -> None:
        """Load layouts from file."""
        if not self.layouts_file.exists():
            return
        
        try:
            with open(self.layouts_file, 'r', encoding='utf-8') as f:
                self.layouts = json.load(f)
        except Exception as e:
            logger.error("Error loading layouts: %s", e)
            self.layouts = {}
    
    def _save_layouts(self) -> None:
        """Save layouts to file."""
        try:
            self.layouts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.layouts_file, 'w', encoding='utf-8') as f:
                json.dump(self.layouts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving layouts: %s", e)
    
    def save_layout(self, name: str, layout_data: dict) -> None:
        """Save a layout.
        
        Args:
            name: Layout name
            layout_data: Dictionary containing layout configuration
        """
        self.layouts[name] = layout_data
        self._save_layouts()
        logger.info("Saved layout: %s", name)
    
    def load_layout(self, name: str) -> Optional[dict]:
        """Load a layout.
        
        Args:
            name: Layout name
            
        Returns:
            Layout data dictionary or None if not found
        """
        return self.layouts.get(name)
    
    def list_layouts(self) -> list[str]:
        """List all saved layout names.
        
        Returns:
            List of layout names
        """
        return list(self.layouts.keys())
    
    def delete_layout(self, name: str) -> bool:
        """Delete a layout.
        
        Args:
            name: Layout name
            
        Returns:
            True if deleted, False if not found
        """
        if name in self.layouts:
            del self.layouts[name]
            self._save_layouts()
            logger.info("Deleted layout: %s", name)
            return True
        return False
    
    def get_default_layout(self) -> dict:
        """Get default layout configuration.
        
        Returns:
            Default layout dictionary
        """
        return {
            "sidebar_width": 250,
            "main_splitter": [1, 2],
            "panel_visibility": {
                "sidebar": True,
                "toolbar": True,
                "statusbar": True,
            },
            "window_geometry": {
                "width": 1400,
                "height": 900,
                "x": 100,
                "y": 100,
            },
            "multi_monitor": {
                "primary_monitor": 0,
                "secondary_monitor": None,
            },
        }
    
    def save_window_layout(self, window_name: str, geometry: dict, splitter_sizes: Optional[list] = None) -> None:
        """Save window layout including geometry and splitter sizes.
        
        Args:
            window_name: Name of the window (e.g., "main_window", "shot_review")
            geometry: Window geometry dict with x, y, width, height
            splitter_sizes: Optional list of splitter section sizes
        """
        if window_name not in self.layouts:
            self.layouts[window_name] = {}
        
        self.layouts[window_name]["geometry"] = geometry
        if splitter_sizes:
            self.layouts[window_name]["splitter_sizes"] = splitter_sizes
        
        self._save_layouts()
        logger.info("Saved layout for window: %s", window_name)
    
    def load_window_layout(self, window_name: str) -> Optional[dict]:
        """Load window layout.
        
        Args:
            window_name: Name of the window
            
        Returns:
            Layout dict with geometry and splitter_sizes, or None
        """
        return self.layouts.get(window_name)


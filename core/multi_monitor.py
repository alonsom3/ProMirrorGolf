"""
Multi-monitor support for optimized window layouts.

This module provides functionality to detect and utilize multiple monitors
for optimal window positioning. It supports:
- Automatic monitor detection (single or dual monitor setups)
- Optimal window positioning based on monitor layout
- Different layout strategies (side-by-side, stacked, fullscreen)
- Window size optimization for different window types

Usage:
    from core.multi_monitor import get_optimal_window_rect, detect_monitors
    
    # Get optimal position for main window
    rect = get_optimal_window_rect(main_window, layout_type="main", monitor_index=0)
    main_window.setGeometry(rect)
    
    # Detect available monitors
    layouts = detect_monitors()
    for layout in layouts:
        print(f"Monitor: {layout.name}, Has secondary: {layout.has_secondary()}")
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import QRect, QPoint
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)


class MonitorLayout:
    """Represents a monitor layout configuration."""
    
    def __init__(self, name: str, primary_rect: QRect, secondary_rect: Optional[QRect] = None):
        self.name = name
        self.primary_rect = primary_rect
        self.secondary_rect = secondary_rect
    
    def has_secondary(self) -> bool:
        """Check if secondary monitor is available."""
        return self.secondary_rect is not None


def detect_monitors() -> list[MonitorLayout]:
    """
    Detect available monitors and return layout configurations.
    
    Returns:
        List of MonitorLayout objects
    """
    app = QApplication.instance()
    if not app:
        logger.warning("No QApplication instance available for monitor detection")
        return []
    
    screens = app.screens()
    layouts = []
    
    if len(screens) == 0:
        logger.warning("No screens detected")
        return layouts
    
    # Primary screen
    primary_screen = app.primaryScreen()
    if primary_screen:
        primary_geometry = primary_screen.geometry()
        
        # Check for secondary screens
        secondary_screen = None
        for screen in screens:
            if screen != primary_screen:
                secondary_screen = screen
                break
        
        if secondary_screen:
            secondary_geometry = secondary_screen.geometry()
            layouts.append(MonitorLayout(
                "Dual Monitor",
                primary_geometry,
                secondary_geometry
            ))
        else:
            layouts.append(MonitorLayout(
                "Single Monitor",
                primary_geometry
            ))
    
    return layouts


def get_optimal_window_rect(
    widget: QWidget,
    layout_type: str = "main",
    monitor_index: int = 0
) -> QRect:
    """
    Get optimal window rectangle for a widget based on monitor layout.
    
    Args:
        widget: Widget to position
        layout_type: Type of layout ("main", "review", "analysis", "comparison")
        monitor_index: Index of monitor to use (0 = primary, 1 = secondary)
    
    Returns:
        QRect for optimal window position and size
    """
    app = QApplication.instance()
    if not app:
        return QRect(100, 100, 1200, 700)
    
    screens = app.screens()
    if monitor_index >= len(screens):
        monitor_index = 0
    
    screen = screens[monitor_index]
    screen_geometry = screen.geometry()
    
    # Default sizes for different layout types
    default_sizes = {
        "main": (1400, 900),
        "review": (1600, 1000),
        "analysis": (1800, 1200),
        "comparison": (2000, 1200),
    }
    
    width, height = default_sizes.get(layout_type, (1200, 700))
    
    # Ensure window fits on screen
    width = min(width, screen_geometry.width() - 100)
    height = min(height, screen_geometry.height() - 100)
    
    # Center on screen
    x = screen_geometry.x() + (screen_geometry.width() - width) // 2
    y = screen_geometry.y() + (screen_geometry.height() - height) // 2
    
    return QRect(x, y, width, height)


def apply_multi_monitor_layout(
    primary_widget: QWidget,
    secondary_widget: Optional[QWidget] = None,
    layout_type: str = "side_by_side"
) -> None:
    """
    Apply multi-monitor layout to widgets.
    
    Args:
        primary_widget: Primary widget (main window)
        secondary_widget: Optional secondary widget (review window, etc.)
        layout_type: Layout type ("side_by_side", "stacked", "fullscreen_secondary")
    """
    layouts = detect_monitors()
    
    if not layouts:
        logger.warning("No monitor layouts detected, using defaults")
        return
    
    layout = layouts[0]
    
    if layout.has_secondary() and secondary_widget:
        if layout_type == "side_by_side":
            # Primary on first monitor, secondary on second
            primary_rect = get_optimal_window_rect(primary_widget, "main", 0)
            secondary_rect = get_optimal_window_rect(secondary_widget, "review", 1)
            
            primary_widget.setGeometry(primary_rect)
            secondary_widget.setGeometry(secondary_rect)
            
        elif layout_type == "stacked":
            # Both on primary monitor, stacked
            primary_rect = get_optimal_window_rect(primary_widget, "main", 0)
            primary_rect.moveTop(primary_rect.top() - primary_rect.height() // 2)
            
            secondary_rect = get_optimal_window_rect(secondary_widget, "review", 0)
            secondary_rect.moveTop(primary_rect.bottom() + 20)
            
            primary_widget.setGeometry(primary_rect)
            secondary_widget.setGeometry(secondary_rect)
            
        elif layout_type == "fullscreen_secondary":
            # Primary on first, secondary fullscreen on second
            primary_rect = get_optimal_window_rect(primary_widget, "main", 0)
            secondary_rect = layout.secondary_rect
            
            primary_widget.setGeometry(primary_rect)
            secondary_widget.setGeometry(secondary_rect)
            secondary_widget.showMaximized()
    else:
        # Single monitor - use default positioning
        primary_rect = get_optimal_window_rect(primary_widget, "main", 0)
        primary_widget.setGeometry(primary_rect)
        
        if secondary_widget:
            # Stack on same monitor
            secondary_rect = get_optimal_window_rect(secondary_widget, "review", 0)
            secondary_rect.moveTop(primary_rect.bottom() + 20)
            secondary_widget.setGeometry(secondary_rect)


def get_monitor_info() -> dict:
    """
    Get information about available monitors.
    
    Returns:
        Dictionary with monitor information
    """
    app = QApplication.instance()
    if not app:
        return {"count": 0, "monitors": []}
    
    screens = app.screens()
    monitors = []
    
    for i, screen in enumerate(screens):
        geometry = screen.geometry()
        monitors.append({
            "index": i,
            "name": screen.name(),
            "is_primary": screen == app.primaryScreen(),
            "geometry": {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height(),
            },
            "dpi": screen.physicalDotsPerInch(),
        })
    
    return {
        "count": len(screens),
        "monitors": monitors,
    }


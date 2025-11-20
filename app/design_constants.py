"""
Design system constants for ProMirrorGolf.

This module provides centralized constants for colors, spacing, typography,
and other design tokens used throughout the application. These constants
should be used instead of hardcoded values to maintain consistency.

Usage:
    from app.design_constants import COLORS, SPACING, TYPOGRAPHY
    
    # Use color constants
    widget.setStyleSheet(f"background-color: {COLORS.BACKGROUND_BASE};")
    
    # Use spacing constants
    layout.setSpacing(SPACING.MEDIUM)
    layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
    
    # Use typography constants
    label.setStyleSheet(f"font-size: {TYPOGRAPHY.BODY}px;")
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    """Color palette constants matching DESIGN_SYSTEM.md."""
    
    # Backgrounds (GitHub-inspired dark theme)
    BACKGROUND_BASE: str = "#0f1116"  # Main window background
    BACKGROUND_SURFACE: str = "#161b22"  # Cards, panels, elevated surfaces
    BACKGROUND_SURFACE_ELEVATED: str = "#1c2128"  # Selected items, hover states
    BACKGROUND_CONTROL: str = "#0d1117"  # Input fields, buttons, controls
    
    # Borders & Dividers
    BORDER_DEFAULT: str = "#21262d"  # Standard borders
    BORDER_HOVER: str = "#30363d"  # Hover state borders
    BORDER_ACTIVE: str = "#484f58"  # Active/focus borders (general active states)
    BORDER_ICON: str = "#7d8799"  # Gray for icons/arrows (combobox dropdown arrow)
    
    # Text Colors
    TEXT_PRIMARY: str = "#c9d1d9"  # Main content text (87% white opacity equivalent)
    TEXT_SECONDARY: str = "#8b949e"  # Labels, hints, metadata (60% white opacity equivalent)
    TEXT_DISABLED: str = "#484f58"  # Disabled state text (38% white opacity equivalent)
    TEXT_PLACEHOLDER: str = "rgba(255, 255, 255, 0.38)"  # Input placeholders
    WHITE_TEXT: str = "#ffffff"  # Pure white for text on colored backgrounds
    
    # Accent (Primary) - Red accent per design system
    ACCENT: str = "#ff4d4d"  # Primary actions, highlights, focus indicators
    ACCENT_HOVER: str = "#ff5c5c"  # Hover state
    ACCENT_ACTIVE: str = "#da3633"  # Active/pressed state
    ACCENT_LIGHT: str = "rgba(255, 77, 77, 0.1)"  # Subtle backgrounds
    
    # Success
    SUCCESS: str = "#238636"
    SUCCESS_HOVER: str = "#2ea043"
    SUCCESS_ACTIVE: str = "#1e6e2e"
    
    # Danger
    DANGER: str = "#da3633"
    DANGER_HOVER: str = "#b62324"
    DANGER_TEXT: str = "#f85149"
    
    # Interactive States (RGBA overlays)
    OVERLAY_HOVER: str = "rgba(255, 255, 255, 0.08)"  # 8% white
    OVERLAY_ACTIVE: str = "rgba(255, 255, 255, 0.16)"  # 16% white
    OVERLAY_DISABLED: float = 0.38  # 38% opacity


@dataclass(frozen=True)
class Spacing:
    """Spacing constants following the 8px grid system."""
    
    # Base unit
    BASE_UNIT: int = 8
    
    # Common spacing values (multiples of 8px)
    XS: int = 4  # 0.5x base
    SMALL: int = 8  # 1x base
    MEDIUM: int = 16  # 2x base
    LARGE: int = 24  # 3x base
    XL: int = 32  # 4x base
    XXL: int = 48  # 6x base
    
    # Component padding (following 8px grid)
    BUTTON_PADDING_V: int = 8  # 1x base unit
    BUTTON_PADDING_H: int = 16  # 2x base unit
    INPUT_PADDING_V: int = 8  # 1x base unit
    INPUT_PADDING_H: int = 12  # 1.5x base unit (rounded to 12 for better UX)
    CARD_PADDING: int = 16  # 2x base unit
    PANEL_PADDING_V: int = 16  # 2x base unit
    PANEL_PADDING_H: int = 24  # 3x base unit
    DIALOG_PADDING: int = 24  # 3x base unit
    
    # Layout spacing (following 8px grid)
    SECTION_SPACING: int = 24  # 3x base unit
    CARD_SPACING: int = 16  # 2x base unit
    FORM_FIELD_SPACING: int = 16  # 2x base unit
    BUTTON_SPACING: int = 8  # 1x base unit


@dataclass(frozen=True)
class Typography:
    """Typography constants matching DESIGN_SYSTEM.md."""
    
    # Font family
    FONT_FAMILY: str = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif'
    
    # Font sizes (px) - matching design system
    H1: int = 28  # Page titles, major headings
    H2: int = 24  # Section headings
    H3: int = 18  # Subsection headings
    BODY: int = 13  # Default body text
    SMALL: int = 12  # Labels, metadata, secondary text
    TINY: int = 11  # Tooltips, fine print
    
    # Font weights
    BOLD: int = 600
    MEDIUM: int = 500
    REGULAR: int = 400
    
    # Line heights
    TIGHT: float = 1.2
    NORMAL: float = 1.5
    LOOSE: float = 1.6


@dataclass(frozen=True)
class ComponentSizes:
    """Standard component size constants matching DESIGN_SYSTEM.md."""
    
    # Minimum heights (matching design system)
    BUTTON_MIN_HEIGHT: int = 32  # Design system standard
    INPUT_MIN_HEIGHT: int = 32  # Design system standard
    TABLE_ROW_MIN_HEIGHT: int = 40  # Design system standard
    
    # Minimum widths (compact desktop optimized)
    BUTTON_MIN_WIDTH: int = 70  # Allow buttons to size to content
    INPUT_MIN_WIDTH: int = 120
    
    # Border radius
    BORDER_RADIUS_SMALL: int = 6  # Buttons, inputs
    BORDER_RADIUS_MEDIUM: int = 8  # Cards, panels
    BORDER_RADIUS_LARGE: int = 12  # Large containers
    
    # Focus outline
    FOCUS_OUTLINE_WIDTH: int = 2
    FOCUS_OUTLINE_OFFSET: int = 2


@dataclass(frozen=True)
class Animation:
    """Animation timing constants."""
    
    # Duration (milliseconds)
    FAST: int = 100  # Active/pressed states
    NORMAL: int = 150  # Hover states, color changes
    SLOW: int = 200  # Complex animations
    
    # Timing functions
    EASE: str = "ease"
    EASE_IN_OUT: str = "ease-in-out"


@dataclass(frozen=True)
class Layout:
    """Layout constants."""
    
    # Maximum widths
    CONTENT_MAX_WIDTH: int = 1400
    FORM_MAX_WIDTH: int = 600
    CARD_MAX_WIDTH: int = 400
    
    # Responsive breakpoints
    BREAKPOINT_SMALL: int = 1024
    BREAKPOINT_MEDIUM: int = 1440


@dataclass(frozen=True)
class LightColors:
    """Light theme color palette."""
    
    # Backgrounds (light grays and whites)
    BACKGROUND_BASE: str = "#ffffff"  # Pure white main background
    BACKGROUND_SURFACE: str = "#f5f5f5"  # Sidebar, cards
    BACKGROUND_SURFACE_ELEVATED: str = "#e8e8e8"  # Hover states
    BACKGROUND_CONTROL: str = "#fafafa"  # Input fields, controls
    
    # Borders (light grays)
    BORDER_DEFAULT: str = "#d0d0d0"
    BORDER_HOVER: str = "#b0b0b0"
    BORDER_ACTIVE: str = "#999999"  # Active/focus borders (general active states)
    BORDER_ICON: str = "#666666"  # Gray for icons/arrows
    
    # Text (dark for light backgrounds)
    TEXT_PRIMARY: str = "#1a1a1a"  # Near black
    TEXT_SECONDARY: str = "#666666"
    TEXT_DISABLED: str = "#999999"
    TEXT_PLACEHOLDER: str = "#999999"
    WHITE_TEXT: str = "#ffffff"  # White for text on colored backgrounds
    
    # Accent (Primary) - Red accent matching dark theme
    ACCENT: str = "#ff4d4d"  # Primary actions, highlights, focus indicators
    ACCENT_HOVER: str = "#ff5c5c"  # Hover state
    ACCENT_ACTIVE: str = "#da3633"  # Active/pressed state
    ACCENT_LIGHT: str = "rgba(255, 77, 77, 0.1)"  # Subtle backgrounds
    
    # Success
    SUCCESS: str = "#238636"
    SUCCESS_HOVER: str = "#1e6e2e"
    SUCCESS_ACTIVE: str = "#1a5c28"
    
    # Danger
    DANGER: str = "#da3633"
    DANGER_HOVER: str = "#b62324"
    DANGER_TEXT: str = "#c91a1a"
    
    # Interactive States (RGBA overlays)
    OVERLAY_HOVER: str = "rgba(0, 0, 0, 0.08)"  # 8% black
    OVERLAY_ACTIVE: str = "rgba(0, 0, 0, 0.16)"  # 16% black
    OVERLAY_DISABLED: float = 0.38  # 38% opacity


# Singleton instances for easy access
COLORS = Colors()
LIGHT_COLORS = LightColors()
SPACING = Spacing()
TYPOGRAPHY = Typography()
SIZES = ComponentSizes()
ANIMATION = Animation()
LAYOUT = Layout()

# Cache for theme colors to avoid repeated file I/O
_colors_cache: dict[str, Colors | LightColors] = {}
_theme_manager_cache = None


def get_current_colors() -> Colors | LightColors:
    """
    Get the current color constants based on ThemeManager settings.
    Cached to avoid repeated file I/O.
    
    Returns:
        Colors or LightColors: The color constants for the current theme
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        from pathlib import Path
        from core.themes import ThemeManager
        
        # Use cached theme manager if available
        global _theme_manager_cache
        if _theme_manager_cache is None:
            themes_file = Path("data/themes.json")
            _theme_manager_cache = ThemeManager(themes_file)
        
        current_theme_name = _theme_manager_cache.current_theme or "Dark"
        
        # Check cache first
        if current_theme_name in _colors_cache:
            return _colors_cache[current_theme_name]
        
        logger.debug(f"Loading colors for theme: {current_theme_name}")
        
        if current_theme_name.lower() == "light":
            result = LIGHT_COLORS
            logger.debug("Returning LIGHT_COLORS")
        else:
            result = COLORS
            logger.debug("Returning COLORS (dark)")
        
        # Cache the result
        _colors_cache[current_theme_name] = result
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading theme colors: {e}", exc_info=True)
        # Default to dark theme if there's any error
        return COLORS


def clear_colors_cache() -> None:
    """Clear the colors cache (useful when theme changes)."""
    global _colors_cache, _theme_manager_cache
    _colors_cache.clear()
    _theme_manager_cache = None


# Convenience exports
__all__ = [
    "COLORS",
    "LIGHT_COLORS",
    "SPACING",
    "TYPOGRAPHY",
    "SIZES",
    "ANIMATION",
    "LAYOUT",
    "get_current_colors",
    "Colors",
    "LightColors",
    "Spacing",
    "Typography",
    "ComponentSizes",
    "Animation",
    "Layout",
]


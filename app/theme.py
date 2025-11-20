"""
Refined dark and light UI themes.

This module provides the global theme stylesheets for the application.
The themes use design constants to ensure consistency.

Usage:
    from app.theme import DARK_THEME, LIGHT_THEME, get_current_theme
    
    # Use specific theme
    widget.setStyleSheet(DARK_THEME)
    
    # Use current theme from settings
    widget.setStyleSheet(get_current_theme())
"""

from pathlib import Path
from app.design_constants import COLORS, LIGHT_COLORS, SPACING, TYPOGRAPHY, SIZES

# Generate theme from constants
DARK_THEME = f"""
* {{
    font-family: {TYPOGRAPHY.FONT_FAMILY};
    font-size: {TYPOGRAPHY.BODY}px;
    background-color: {COLORS.BACKGROUND_BASE};
    color: {COLORS.TEXT_PRIMARY};
}}

QMainWindow, QWidget {{
    background-color: {COLORS.BACKGROUND_BASE};
    color: {COLORS.TEXT_PRIMARY};
}}

QWidget:!window {{
    background-color: {COLORS.BACKGROUND_BASE};
}}

QWidget#controlContainer {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    border: 1px solid {COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
}}

QWidget#sidebar {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    border-right: 1px solid {COLORS.BORDER_DEFAULT};
}}

QWidget#buttonToolbar {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border: 1px solid {COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
}}

QWidget#cameraView,
QWidget[panel="true"] {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border: 1px solid {COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
}}

QLabel {{
    color: {COLORS.TEXT_PRIMARY};
    background: transparent;
}}

QLabel[secondary="true"] {{
    color: {COLORS.TEXT_SECONDARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.BOLD};
}}

/* Buttons */
QPushButton {{
    min-height: {SIZES.BUTTON_MIN_HEIGHT}px;
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
    background-color: {COLORS.BACKGROUND_SURFACE};
    border: 1px solid {COLORS.BORDER_DEFAULT};
    color: {COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.MEDIUM};
}}

QPushButton:hover {{
    background-color: {COLORS.BACKGROUND_SURFACE_ELEVATED};
    border-color: {COLORS.BORDER_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLORS.BORDER_DEFAULT};
}}

QPushButton:disabled {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border-color: {COLORS.BORDER_DEFAULT};
    color: {COLORS.TEXT_DISABLED};
    opacity: {COLORS.OVERLAY_DISABLED};
}}

QPushButton#accentButton {{
    background-color: {COLORS.ACCENT};
    border: none;
    color: {COLORS.WHITE_TEXT};
    font-weight: {TYPOGRAPHY.MEDIUM};
}}

QPushButton#accentButton:hover {{
    background-color: {COLORS.ACCENT_HOVER};
}}

QPushButton#accentButton:pressed {{
    background-color: {COLORS.ACCENT_ACTIVE};
}}

QPushButton#accentButton:focus {{
    outline: 2px solid {COLORS.ACCENT};
    outline-offset: 2px;
}}

QPushButton#dangerButton {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    border: 1px solid {COLORS.DANGER};
    color: {COLORS.DANGER_TEXT};
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS.DANGER_HOVER};
    border-color: {COLORS.DANGER};
    color: {COLORS.WHITE_TEXT};
}}

QPushButton#outlineButton {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    border: 1px solid {COLORS.BORDER_HOVER};
    color: {COLORS.TEXT_PRIMARY};
}}

/* Inputs - matching web UI */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border: 1px solid {COLORS.BORDER_HOVER};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    padding: {SPACING.INPUT_PADDING_V}px {SPACING.INPUT_PADDING_H}px;
    color: {COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.BODY}px;
    min-height: {SIZES.INPUT_MIN_HEIGHT}px;
    selection-background-color: {COLORS.ACCENT};
    selection-color: {COLORS.WHITE_TEXT};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 2px solid {COLORS.ACCENT};
    background-color: {COLORS.BACKGROUND_CONTROL};
}}

QComboBox:hover {{
    border-color: {COLORS.BORDER_ACTIVE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS.BORDER_ICON};
    margin-right: 8px;
}}

/* Sliders */
QSlider::groove:horizontal {{
    background: {COLORS.BORDER_DEFAULT};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLORS.ACCENT};
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

/* Tables */
QTableWidget, QTreeWidget {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border: 1px solid {COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
    gridline-color: transparent;
    color: {COLORS.TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    color: {COLORS.TEXT_SECONDARY};
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border: none;
    border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.BOLD};
}}

QTableWidget::item {{
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border: none;
    border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
    color: {COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.SMALL}px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS.BACKGROUND_SURFACE_ELEVATED};
}}

QTableWidget::item:hover {{
    background-color: {COLORS.BACKGROUND_SURFACE};
}}

/* Tabs */
QTabBar::tab {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    color: {COLORS.TEXT_SECONDARY};
    padding: {SPACING.SMALL}px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border: 1px solid {COLORS.BORDER_DEFAULT};
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS.BACKGROUND_BASE};
    color: {COLORS.ACCENT};
    border-bottom: 1px solid {COLORS.BACKGROUND_BASE};
}}

QTabBar::tab:hover {{
    background-color: {COLORS.BORDER_HOVER};
}}

/* Scrollbars */
QScrollBar:vertical, QScrollBar:horizontal {{
    background-color: {COLORS.BACKGROUND_CONTROL};
    border: none;
    width: 12px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {COLORS.BORDER_HOVER};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS.BORDER_ACTIVE};
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    border-top: 1px solid {COLORS.BORDER_DEFAULT};
    color: {COLORS.TEXT_SECONDARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS.BACKGROUND_SURFACE};
    color: {COLORS.TEXT_PRIMARY};
    border: 1px solid {COLORS.BORDER_HOVER};
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    font-size: {TYPOGRAPHY.SMALL}px;
}}
"""

# Generate light theme from constants
LIGHT_THEME = f"""
* {{
    font-family: {TYPOGRAPHY.FONT_FAMILY};
    font-size: {TYPOGRAPHY.BODY}px;
    background-color: {LIGHT_COLORS.BACKGROUND_BASE};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
}}

QMainWindow, QWidget {{
    background-color: {LIGHT_COLORS.BACKGROUND_BASE};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
}}

QWidget:!window {{
    background-color: {LIGHT_COLORS.BACKGROUND_BASE};
}}

QWidget#controlContainer {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
}}

QWidget#sidebar {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border-right: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
}}

QWidget#buttonToolbar {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
}}

QWidget#cameraView,
QWidget[panel="true"] {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
}}

QLabel {{
    color: {LIGHT_COLORS.TEXT_PRIMARY};
    background: transparent;
}}

QLabel[secondary="true"] {{
    color: {LIGHT_COLORS.TEXT_SECONDARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.BOLD};
}}

/* Buttons */
QPushButton {{
    min-height: {SIZES.BUTTON_MIN_HEIGHT}px;
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.MEDIUM};
}}

QPushButton:hover {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE_ELEVATED};
    border-color: {LIGHT_COLORS.BORDER_HOVER};
}}

QPushButton:pressed {{
    background-color: {LIGHT_COLORS.BORDER_DEFAULT};
}}

QPushButton:disabled {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border-color: {LIGHT_COLORS.BORDER_DEFAULT};
    color: {LIGHT_COLORS.TEXT_DISABLED};
    opacity: {LIGHT_COLORS.OVERLAY_DISABLED};
}}

QPushButton#accentButton {{
    background-color: {LIGHT_COLORS.ACCENT};
    border: none;
    color: {LIGHT_COLORS.WHITE_TEXT};
    font-weight: {TYPOGRAPHY.MEDIUM};
}}

QPushButton#accentButton:hover {{
    background-color: {LIGHT_COLORS.ACCENT_HOVER};
}}

QPushButton#accentButton:pressed {{
    background-color: {LIGHT_COLORS.ACCENT_ACTIVE};
}}

QPushButton#accentButton:focus {{
    outline: 2px solid {LIGHT_COLORS.ACCENT};
    outline-offset: 2px;
}}

QPushButton#dangerButton {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border: 1px solid {LIGHT_COLORS.DANGER};
    color: {LIGHT_COLORS.DANGER_TEXT};
}}

QPushButton#dangerButton:hover {{
    background-color: {LIGHT_COLORS.DANGER_HOVER};
    border-color: {LIGHT_COLORS.DANGER};
    color: {LIGHT_COLORS.WHITE_TEXT};
}}

QPushButton#outlineButton {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border: 1px solid {LIGHT_COLORS.BORDER_HOVER};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
}}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border: 1px solid {LIGHT_COLORS.BORDER_HOVER};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    padding: {SPACING.INPUT_PADDING_V}px {SPACING.INPUT_PADDING_H}px;
    color: {LIGHT_COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.BODY}px;
    min-height: {SIZES.INPUT_MIN_HEIGHT}px;
    selection-background-color: {LIGHT_COLORS.ACCENT};
    selection-color: {LIGHT_COLORS.WHITE_TEXT};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 2px solid {LIGHT_COLORS.ACCENT};
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
}}

QComboBox:hover {{
    border-color: {LIGHT_COLORS.BORDER_ACTIVE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {LIGHT_COLORS.BORDER_ICON};
    margin-right: 8px;
}}

/* Sliders */
QSlider::groove:horizontal {{
    background: {LIGHT_COLORS.BORDER_DEFAULT};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {LIGHT_COLORS.ACCENT};
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

/* Tables */
QTableWidget, QTreeWidget {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
    gridline-color: transparent;
    color: {LIGHT_COLORS.TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    color: {LIGHT_COLORS.TEXT_SECONDARY};
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border: none;
    border-bottom: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    font-size: {TYPOGRAPHY.SMALL}px;
    font-weight: {TYPOGRAPHY.BOLD};
}}

QTableWidget::item {{
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border: none;
    border-bottom: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.SMALL}px;
}}

QTableWidget::item:selected {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE_ELEVATED};
}}

QTableWidget::item:hover {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
}}

/* Tabs */
QTabBar::tab {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    color: {LIGHT_COLORS.TEXT_SECONDARY};
    padding: {SPACING.SMALL}px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {LIGHT_COLORS.BACKGROUND_BASE};
    color: {LIGHT_COLORS.ACCENT};
    border-bottom: 1px solid {LIGHT_COLORS.BACKGROUND_BASE};
}}

QTabBar::tab:hover {{
    background-color: {LIGHT_COLORS.BORDER_HOVER};
}}

/* Scrollbars */
QScrollBar:vertical, QScrollBar:horizontal {{
    background-color: {LIGHT_COLORS.BACKGROUND_CONTROL};
    border: none;
    width: 12px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {LIGHT_COLORS.BORDER_HOVER};
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background-color: {LIGHT_COLORS.BORDER_ACTIVE};
}}

/* Status Bar */
QStatusBar {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    border-top: 1px solid {LIGHT_COLORS.BORDER_DEFAULT};
    color: {LIGHT_COLORS.TEXT_SECONDARY};
    font-size: {TYPOGRAPHY.SMALL}px;
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
}}

/* Tooltips */
QToolTip {{
    background-color: {LIGHT_COLORS.BACKGROUND_SURFACE};
    color: {LIGHT_COLORS.TEXT_PRIMARY};
    border: 1px solid {LIGHT_COLORS.BORDER_HOVER};
    padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
    font-size: {TYPOGRAPHY.SMALL}px;
}}
"""


# Cache for theme stylesheets to avoid repeated file I/O
_theme_cache: dict[str, str] = {}
_theme_manager_cache = None


def get_current_theme() -> str:
    """
    Get the current theme stylesheet based on ThemeManager settings.
    Cached to avoid repeated file I/O.
    
    Returns:
        str: The stylesheet for the current theme (DARK_THEME or LIGHT_THEME)
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        from core.themes import ThemeManager
        
        # Use cached theme manager if available
        global _theme_manager_cache
        if _theme_manager_cache is None:
            themes_file = Path("data/themes.json")
            _theme_manager_cache = ThemeManager(themes_file)
        
        current_theme_name = _theme_manager_cache.current_theme or "Dark"
        
        # Check cache first
        if current_theme_name in _theme_cache:
            return _theme_cache[current_theme_name]
        
        logger.debug(f"Loading theme: {current_theme_name}")
        
        if current_theme_name.lower() == "light":
            result = LIGHT_THEME
            logger.debug("Returning LIGHT_THEME")
        else:
            result = DARK_THEME
            logger.debug("Returning DARK_THEME")
        
        # Cache the result
        _theme_cache[current_theme_name] = result
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading theme: {e}", exc_info=True)
        # Default to dark theme if there's any error
        return DARK_THEME


def clear_theme_cache() -> None:
    """Clear the theme cache (useful when theme changes)."""
    global _theme_cache, _theme_manager_cache
    _theme_cache.clear()
    _theme_manager_cache = None

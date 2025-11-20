"""
Style helper functions for consistent widget styling.

This module provides helper functions to generate stylesheets using design constants,
reducing boilerplate and ensuring consistency across the application.

Usage:
    from app.style_helpers import style_label, style_button, style_input, style_card
    
    # Style a label
    label.setStyleSheet(style_label(secondary=True))
    
    # Style a button
    btn.setStyleSheet(style_button(variant="primary"))
    
    # Style an input
    input_field.setStyleSheet(style_input())
    
    # Style a card/panel
    card.setStyleSheet(style_card())
"""

from __future__ import annotations

from typing import Optional

from app.design_constants import SPACING, TYPOGRAPHY, SIZES, get_current_colors


def style_label(
    secondary: bool = False,
    size: Optional[int] = None,
    weight: Optional[int] = None,
    color: Optional[str] = None,
) -> str:
    """
    Generate stylesheet for QLabel.
    
    Args:
        secondary: If True, use secondary text color
        size: Font size in pixels (uses TYPOGRAPHY.BODY if None)
        weight: Font weight (uses TYPOGRAPHY.REGULAR if None)
        color: Custom text color (overrides secondary)
    
    Returns:
        Stylesheet string
    """
    current_colors = get_current_colors()
    text_color = color or (current_colors.TEXT_SECONDARY if secondary else current_colors.TEXT_PRIMARY)
    font_size = size or TYPOGRAPHY.BODY
    font_weight = weight or TYPOGRAPHY.REGULAR
    
    return f"""
        QLabel {{
            color: {text_color};
            font-size: {font_size}px;
            font-weight: {font_weight};
            background: transparent;
        }}
    """.strip()


def style_button(
    variant: str = "secondary",
    min_height: Optional[int] = None,
    min_width: Optional[int] = None,
) -> str:
    """
    Generate stylesheet for QPushButton.
    
    Args:
        variant: Button variant ("primary", "secondary", "danger", "outline")
        min_height: Minimum height (uses SIZES.BUTTON_MIN_HEIGHT if None)
        min_width: Minimum width (uses SIZES.BUTTON_MIN_WIDTH if None)
    
    Returns:
        Stylesheet string
    """
    current_colors = get_current_colors()
    height = min_height or SIZES.BUTTON_MIN_HEIGHT
    width = min_width or SIZES.BUTTON_MIN_WIDTH
    
    if variant == "primary":
        return f"""
            QPushButton {{
                min-height: {height}px;
                min-width: {width}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                background-color: {current_colors.ACCENT};
                border: none;
                color: {current_colors.WHITE_TEXT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {current_colors.ACCENT_ACTIVE};
            }}
            QPushButton:disabled {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                color: {current_colors.TEXT_DISABLED};
                opacity: {current_colors.OVERLAY_DISABLED};
            }}
            QPushButton:focus {{
                outline: {SIZES.FOCUS_OUTLINE_WIDTH}px solid {current_colors.ACCENT};
                outline-offset: {SIZES.FOCUS_OUTLINE_OFFSET}px;
            }}
        """.strip()
    
    elif variant == "danger":
        return f"""
            QPushButton {{
                min-height: {height}px;
                min-width: {width}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.DANGER};
                color: {current_colors.DANGER_TEXT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.DANGER_HOVER};
                border-color: {current_colors.DANGER};
                color: {current_colors.WHITE_TEXT};
            }}
            QPushButton:disabled {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border-color: {current_colors.BORDER_DEFAULT};
                color: {current_colors.TEXT_DISABLED};
                opacity: {current_colors.OVERLAY_DISABLED};
            }}
        """.strip()
    
    elif variant == "success":
        return f"""
            QPushButton {{
                min-height: {height}px;
                min-width: {width}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                background-color: {current_colors.SUCCESS};
                border: 1px solid {current_colors.SUCCESS};
                color: {current_colors.WHITE_TEXT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.SUCCESS_HOVER};
                border-color: {current_colors.SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {current_colors.SUCCESS_ACTIVE};
                border-color: {current_colors.SUCCESS_ACTIVE};
            }}
        """.strip()
    
    else:  # secondary/default
        return f"""
            QPushButton {{
                min-height: {height}px;
                min-width: {width}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                background-color: transparent;
                border: 2px solid {current_colors.ACCENT};
                color: {current_colors.ACCENT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QPushButton:pressed {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                border-color: {current_colors.BORDER_DEFAULT};
                color: {current_colors.TEXT_DISABLED};
                opacity: {current_colors.OVERLAY_DISABLED};
            }}
        """.strip()


def style_input(
    min_height: Optional[int] = None,
    padding_v: Optional[int] = None,
    padding_h: Optional[int] = None,
) -> str:
    """
    Generate stylesheet for input fields (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox).
    
    Args:
        min_height: Minimum height (uses SIZES.INPUT_MIN_HEIGHT if None)
        padding_v: Vertical padding (uses SPACING.INPUT_PADDING_V if None)
        padding_h: Horizontal padding (uses SPACING.INPUT_PADDING_H if None)
    
    Returns:
        Stylesheet string
    """
    height = min_height or SIZES.INPUT_MIN_HEIGHT
    current_colors = get_current_colors()
    pad_v = padding_v or SPACING.INPUT_PADDING_V
    pad_h = padding_h or SPACING.INPUT_PADDING_H
    
    return f"""
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
            background-color: {current_colors.BACKGROUND_CONTROL};
            border: 1px solid {current_colors.BORDER_HOVER};
            border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            padding: {pad_v}px {pad_h}px;
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.BODY}px;
            min-height: {height}px;
            selection-background-color: {current_colors.ACCENT};
            selection-color: {current_colors.WHITE_TEXT};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
            border: 2px solid {current_colors.ACCENT};
            background-color: {current_colors.BACKGROUND_CONTROL};
        }}
        QLineEdit:hover, QComboBox:hover {{
            border-color: {current_colors.BORDER_ACTIVE};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{
            background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            color: {current_colors.TEXT_DISABLED};
            opacity: {current_colors.OVERLAY_DISABLED};
        }}
    """.strip()


def style_card(
    padding: Optional[int] = None,
    border_radius: Optional[int] = None,
) -> str:
    """
    Generate stylesheet for card/panel containers.
    
    Args:
        padding: Padding value (uses SPACING.CARD_PADDING if None)
        border_radius: Border radius (uses SIZES.BORDER_RADIUS_MEDIUM if None)
    
    Returns:
        Stylesheet string
    """
    current_colors = get_current_colors()
    pad = padding or SPACING.CARD_PADDING
    radius = border_radius or SIZES.BORDER_RADIUS_MEDIUM
    
    return f"""
        QWidget {{
            background-color: {current_colors.BACKGROUND_SURFACE};
            border: 1px solid {current_colors.BORDER_DEFAULT};
            border-radius: {radius}px;
            padding: {pad}px;
        }}
        QWidget:hover {{
            border-color: {current_colors.BORDER_HOVER};
        }}
    """.strip()


def style_table() -> str:
    """
    Generate stylesheet for QTableWidget.
    
    Returns:
        Stylesheet string
    """
    current_colors = get_current_colors()
    return f"""
        QTableWidget {{
            background-color: {current_colors.BACKGROUND_CONTROL};
            border: 1px solid {current_colors.BORDER_DEFAULT};
            border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            gridline-color: transparent;
            color: {current_colors.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {current_colors.BACKGROUND_CONTROL};
            color: {current_colors.TEXT_SECONDARY};
            padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
            border: none;
            border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
            font-size: {TYPOGRAPHY.SMALL}px;
            font-weight: {TYPOGRAPHY.BOLD};
        }}
        QTableWidget::item {{
            padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
            border: none;
            border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.BODY}px;
        }}
        QTableWidget::item:selected {{
            background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
        }}
        QTableWidget::item:hover {{
            background-color: {current_colors.BACKGROUND_SURFACE};
        }}
    """.strip()


def style_panel(
    padding_v: Optional[int] = None,
    padding_h: Optional[int] = None,
) -> str:
    """
    Generate stylesheet for panel containers.
    
    Args:
        padding_v: Vertical padding (uses SPACING.PANEL_PADDING_V if None)
        padding_h: Horizontal padding (uses SPACING.PANEL_PADDING_H if None)
    
    Returns:
        Stylesheet string
    """
    current_colors = get_current_colors()
    pad_v = padding_v or SPACING.PANEL_PADDING_V
    pad_h = padding_h or SPACING.PANEL_PADDING_H
    
    return f"""
        QWidget {{
            background-color: {current_colors.BACKGROUND_CONTROL};
            border: 1px solid {current_colors.BORDER_DEFAULT};
            border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            padding: {pad_v}px {pad_h}px;
        }}
    """.strip()


# Convenience exports
__all__ = [
    "style_label",
    "style_button",
    "style_input",
    "style_card",
    "style_table",
    "style_panel",
]


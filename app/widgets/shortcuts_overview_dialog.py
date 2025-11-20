"""Keyboard shortcuts overview dialog showing all available shortcuts."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.shortcuts import ShortcutManager


class ShortcutsOverviewDialog(QDialog):
    """Dialog showing all keyboard shortcuts in an organized view."""
    
    def __init__(self, shortcut_manager: ShortcutManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.shortcut_manager = shortcut_manager
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header_label = QLabel("Keyboard Shortcuts Reference")
        header_label.setStyleSheet(f"""
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.H2}px;
            font-weight: {TYPOGRAPHY.BOLD};
            padding-bottom: {SPACING.MEDIUM}px;
        """)
        layout.addWidget(header_label)
        
        # Tabs for different contexts
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {current_colors.BORDER_DEFAULT};
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
            QTabBar::tab {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-bottom: none;
                border-top-left-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                border-top-right-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QTabBar::tab:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
                border-color: {current_colors.ACCENT};
            }}
        """)
        
        # Action names mapping
        action_names = {
            "main_window": {
                "start_session": "Start Session",
                "stop_session": "Stop Session",
                "browse_sessions": "Browse Sessions",
                "analysis": "Open Analysis",
                "comparison": "Compare Sessions",
                "settings": "Open Settings",
                "review_shot": "Review Shot",
                "delete_shot": "Delete Shot",
            },
            "shot_review": {
                "play_pause": "Play/Pause",
                "stop": "Stop",
                "rewind": "Rewind 10 Frames",
                "forward": "Forward 10 Frames",
                "seek_backward": "Seek Backward 30 Frames",
                "seek_forward": "Seek Forward 30 Frames",
                "speed_0.1x": "Speed 0.1x",
                "speed_0.25x": "Speed 0.25x",
                "speed_0.5x": "Speed 0.5x",
                "speed_1x": "Speed 1x",
                "speed_2x": "Speed 2x",
                "speed_4x": "Speed 4x",
                "toggle_favorite": "Toggle Favorite",
                "edit_tags": "Edit Tags",
                "edit_notes": "Edit Notes",
                "tool_freehand": "Freehand Tool",
                "tool_swing_plane": "Swing Plane Tool",
                "tool_reference": "Reference Line Tool",
                "tool_select": "Select Tool",
                "clear_drawings": "Clear Drawings",
                "pick_color": "Pick Color",
            },
        }
        
        # Create tabs for each context
        for context, shortcuts in self.shortcut_manager.get_all_shortcuts().items():
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Action", "Shortcut"])
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setAlternatingRowColors(True)
            table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                    gridline-color: {current_colors.BORDER_DEFAULT};
                }}
                QTableWidget::item {{
                    padding: {SPACING.SMALL}px;
                    color: {current_colors.TEXT_PRIMARY};
                }}
                QHeaderView::section {{
                    background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                    color: {current_colors.TEXT_PRIMARY};
                    padding: {SPACING.SMALL}px;
                    border: none;
                    border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
                    font-weight: {TYPOGRAPHY.BOLD};
                }}
            """)
            
            names = action_names.get(context, {})
            table.setRowCount(len(shortcuts))
            
            for row, (action, key_sequence) in enumerate(sorted(shortcuts.items())):
                action_name = names.get(action, action.replace("_", " ").title())
                table.setItem(row, 0, QTableWidgetItem(action_name))
                
                shortcut_item = QTableWidgetItem(key_sequence)
                shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, shortcut_item)
            
            table.resizeColumnsToContents()
            table.setColumnWidth(0, 300)
            table.setColumnWidth(1, 150)
            
            context_name = context.replace("_", " ").title()
            tabs.addTab(table, context_name)
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


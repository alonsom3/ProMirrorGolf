"""Shortcut customization dialog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.shortcuts import ShortcutManager

logger = logging.getLogger(__name__)


class ShortcutEditor(QDialog):
    """Dialog for customizing keyboard shortcuts."""
    
    # Human-readable action names
    ACTION_NAMES = {
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
    
    def __init__(self, shortcut_manager: ShortcutManager, parent: Optional[QWidget] = None) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        self.pending_changes: dict[tuple[str, str], str] = {}  # (context, action) -> new_sequence
        self.setWindowTitle("Customize Keyboard Shortcuts")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self._build_ui()
        self._load_shortcuts()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Keyboard Shortcuts")
        title.setAutoFillBackground(True)
        title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setMinimumHeight(32)
        reset_btn.setMaximumHeight(40)
        reset_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        reset_btn.clicked.connect(self._reset_to_defaults)
        header_layout.addWidget(reset_btn)
        
        layout.addWidget(header)
        
        # Shortcuts table
        self.shortcuts_table = QTableWidget(0, 3)
        self.shortcuts_table.setHorizontalHeaderLabels(["Context", "Action", "Shortcut"])
        self.shortcuts_table.setAlternatingRowColors(True)
        self.shortcuts_table.verticalHeader().setVisible(False)
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.shortcuts_table.setShowGrid(False)
        self.shortcuts_table.setSortingEnabled(True)
        self.shortcuts_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.shortcuts_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        header_view = self.shortcuts_table.horizontalHeader()
        header_view.setVisible(True)
        header_view.setSectionsClickable(True)
        header_view.setStretchLastSection(True)
        
        self.shortcuts_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                gridline-color: transparent;
                color: {current_colors.TEXT_PRIMARY};
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
            QHeaderView::section {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                border: none;
                border-bottom: 2px solid {current_colors.BORDER_DEFAULT};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.BOLD};
            }}
            QHeaderView::section:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
            }}
        """)
        
        # Make shortcut column editable
        self.shortcuts_table.itemDoubleClicked.connect(self._edit_shortcut)
        
        layout.addWidget(self.shortcuts_table, 1)
        
        # Instructions
        instructions = QLabel("Double-click a shortcut cell to edit. Press Escape to cancel editing.")
        instructions.setAutoFillBackground(True)
        instructions.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-style: italic; padding: {SPACING.SMALL}px; margin: 0px;")
        instructions.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout.addWidget(instructions)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self._save_shortcuts)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_shortcuts(self) -> None:
        """Load shortcuts into table."""
        self.shortcuts_table.setRowCount(0)
        
        all_shortcuts = self.shortcut_manager.get_all_shortcuts()
        row = 0
        
        for context, actions in sorted(all_shortcuts.items()):
            context_name = context.replace("_", " ").title()
            action_names = self.ACTION_NAMES.get(context, {})
            
            for action, key_sequence in sorted(actions.items()):
                self.shortcuts_table.insertRow(row)
                
                # Context
                context_item = QTableWidgetItem(context_name)
                context_item.setData(Qt.ItemDataRole.UserRole, context)
                context_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.shortcuts_table.setItem(row, 0, context_item)
                
                # Action
                action_name = action_names.get(action, action.replace("_", " ").title())
                action_item = QTableWidgetItem(action_name)
                action_item.setData(Qt.ItemDataRole.UserRole, action)
                action_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.shortcuts_table.setItem(row, 1, action_item)
                
                # Shortcut (editable)
                shortcut_item = QTableWidgetItem(key_sequence)
                shortcut_item.setData(Qt.ItemDataRole.UserRole, (context, action))
                self.shortcuts_table.setItem(row, 2, shortcut_item)
                
                row += 1
        
        # Set column widths
        self.shortcuts_table.setColumnWidth(0, 150)
        self.shortcuts_table.setColumnWidth(1, 250)
        self.shortcuts_table.setColumnWidth(2, 200)
    
    def _edit_shortcut(self, item: QTableWidgetItem) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()

        """Edit shortcut for selected row."""
        if item.column() != 2:  # Only shortcut column is editable
            return
        
        row = item.row()
        shortcut_item = self.shortcuts_table.item(row, 2)
        if not shortcut_item:
            return
        
        context_item = self.shortcuts_table.item(row, 0)
        action_item = self.shortcuts_table.item(row, 1)
        if not context_item or not action_item:
            return
        
        context = context_item.data(Qt.ItemDataRole.UserRole)
        action = action_item.data(Qt.ItemDataRole.UserRole)
        current_shortcut = shortcut_item.text()
        
        # Show dialog to capture new shortcut
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Shortcut")
        dialog.setMinimumSize(400, 150)
        dialog.setStyleSheet(get_current_theme())
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        dialog_layout.setSpacing(SPACING.MEDIUM)
        
        info_label = QLabel(f"Press the key combination for:\n{action_item.text()}")
        info_label.setAutoFillBackground(True)
        info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        dialog_layout.addWidget(info_label)
        
        shortcut_edit = QLineEdit()
        shortcut_edit.setPlaceholderText("Press keys...")
        shortcut_edit.setReadOnly(True)
        shortcut_edit.setStyleSheet(f"""

            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 2px solid {current_colors.ACCENT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY + 1}px;
                font-weight: {TYPOGRAPHY.BOLD};
            }}
        """)
        dialog_layout.addWidget(shortcut_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        
        # Capture key press using event filter
        sequence_ref = [None]
        
        class KeyCaptureFilter(QObject):
            def __init__(self, edit_widget, sequence_var):
                super().__init__()
                self.edit_widget = edit_widget
                self.sequence_var = sequence_var
            
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.KeyPress:
                    modifiers = []
                    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                        modifiers.append("Ctrl")
                    if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                        modifiers.append("Alt")
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                        modifiers.append("Shift")
                    if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
                        modifiers.append("Meta")
                    
                    key = event.key()
                    if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta):
                        return False
                    
                    key_name = QKeySequence(key).toString()
                    if modifiers:
                        self.sequence_var[0] = "+".join(modifiers + [key_name])
                    else:
                        self.sequence_var[0] = key_name
                    
                    self.edit_widget.setText(self.sequence_var[0])
                    return True
                return False
        
        key_filter = KeyCaptureFilter(shortcut_edit, sequence_ref)
        shortcut_edit.installEventFilter(key_filter)
        shortcut_edit.setFocus()
        
        if dialog.exec() == dialog.DialogCode.Accepted and sequence_ref[0]:
            # Validate shortcut
            try:
                captured_sequence = sequence_ref[0]
                QKeySequence(captured_sequence)  # Validate format
                shortcut_item.setText(captured_sequence)
                self.pending_changes[(context, action)] = captured_sequence
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Invalid Shortcut",
                    f"Invalid key sequence: {captured_sequence}\n\n{str(e)}",
                )
    
    def _reset_to_defaults(self) -> None:
        """Reset all shortcuts to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all shortcuts to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.shortcut_manager.reset_to_defaults()
            self.pending_changes.clear()
            self._load_shortcuts()
    
    def _save_shortcuts(self) -> None:
        """Save all pending changes."""
        for (context, action), key_sequence in self.pending_changes.items():
            self.shortcut_manager.set_shortcut(context, action, key_sequence)
        
        self.pending_changes.clear()
        self.accept()
        QMessageBox.information(
            self,
            "Shortcuts Saved",
            "Keyboard shortcuts have been saved.\n\n"
            "Some shortcuts may require restarting the application to take effect.",
        )


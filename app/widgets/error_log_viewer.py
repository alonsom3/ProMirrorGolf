"""Error log viewer widget for settings dialog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme

logger = logging.getLogger(__name__)


class ErrorLogViewer(QWidget):
    """Widget for viewing application error logs."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
        """)
        layout.addWidget(self.log_text, 1)
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        refresh_btn.clicked.connect(self._refresh_log)
        buttons.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        clear_btn.clicked.connect(self._clear_log)
        buttons.addWidget(clear_btn)
        
        layout.addLayout(buttons)
        
        # Load initial log
        self._refresh_log()
    
    def _refresh_log(self):
        """Refresh log display from file."""
        log_file = Path("data/app.log")
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    # Read last 1000 lines
                    lines = f.readlines()
                    recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                    self.log_text.setPlainText(''.join(recent_lines))
                    # Scroll to bottom
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.log_text.setTextCursor(cursor)
            except Exception as e:
                logger.error("Error reading log file: %s", e)
                self.log_text.setPlainText(f"Error reading log file: {e}")
        else:
            self.log_text.setPlainText("No log file found.")
    
    def _clear_log(self):
        """Clear log file."""
        log_file = Path("data/app.log")
        if log_file.exists():
            try:
                log_file.unlink()
                self.log_text.setPlainText("Log file cleared.")
            except Exception as e:
                logger.error("Error clearing log file: %s", e)
                self.log_text.setPlainText(f"Error clearing log file: {e}")


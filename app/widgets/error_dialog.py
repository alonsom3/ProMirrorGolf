"""Enhanced error dialog with better formatting and help text."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme

logger = logging.getLogger(__name__)


class ErrorDialog(QDialog):
    """Enhanced error dialog with detailed information and help."""
    
    def __init__(
        self,
        title: str,
        message: str,
        details: Optional[str] = None,
        help_text: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        self.resize(600, 400)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Error icon and message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            color: {current_colors.DANGER};
            font-size: {TYPOGRAPHY.BODY}px;
            font-weight: {TYPOGRAPHY.BOLD};
            padding: {SPACING.MEDIUM}px;
        """)
        layout.addWidget(message_label)
        
        # Details (collapsible)
        if details:
            details_label = QLabel("Details:")
            details_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: {TYPOGRAPHY.BOLD};")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setPlainText(details)
            details_text.setMaximumHeight(150)
            details_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: {SPACING.SMALL}px;
                    color: {current_colors.TEXT_SECONDARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                    font-family: monospace;
                }}
            """)
            layout.addWidget(details_text)
        
        # Help text
        if help_text:
            help_label = QLabel("Help:")
            help_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: {TYPOGRAPHY.BOLD}; margin-top: {SPACING.SMALL}px;")
            layout.addWidget(help_label)
            
            help_content = QLabel(help_text)
            help_content.setWordWrap(True)
            help_content.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: {SPACING.SMALL}px;")
            layout.addWidget(help_content)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
    
    @staticmethod
    def show_error(
        title: str,
        message: str,
        details: Optional[str] = None,
        help_text: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Show an error dialog."""
        dialog = ErrorDialog(title, message, details, help_text, parent)
        dialog.exec()


"""Onboarding/tutorial dialog for new users."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme

logger = logging.getLogger(__name__)


class OnboardingDialog(QDialog):
    """Onboarding dialog showing key features to new users."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle("Welcome to ProMirror Golf")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.LARGE)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Welcome header
        welcome_label = QLabel("🎯 Welcome to ProMirror Golf!")
        welcome_label.setStyleSheet(f"""
            color: {current_colors.ACCENT};
            font-size: {TYPOGRAPHY.H2}px;
            font-weight: {TYPOGRAPHY.BOLD};
            padding: {SPACING.MEDIUM}px;
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Features list
        features_text = QLabel("""
        <h3>Key Features:</h3>
        <ul>
        <li><b>Session Recording:</b> Start a session and automatically capture shots</li>
        <li><b>Video Review:</b> Review shots with synchronized dual-camera playback</li>
        <li><b>Drawing Tools:</b> Annotate videos with lines and measurements</li>
        <li><b>Analysis Dashboard:</b> View trends, statistics, and performance charts</li>
        <li><b>Advanced Search:</b> Find shots using multiple criteria and saved filters</li>
        <li><b>Export Options:</b> Export data to CSV, Excel, JSON, or PDF</li>
        <li><b>Batch Operations:</b> Tag, export, or modify multiple shots at once</li>
        </ul>
        
        <h3>Quick Start:</h3>
        <ol>
        <li>Click "Start Session" or press <b>Ctrl+S</b></li>
        <li>Enter a session name and select your club</li>
        <li>Shots will be automatically recorded when detected</li>
        <li>Double-click any shot to review it</li>
        </ol>
        """)
        features_text.setWordWrap(True)
        features_text.setStyleSheet(f"""
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.BODY}px;
            padding: {SPACING.MEDIUM}px;
        """)
        layout.addWidget(features_text)
        
        # Don't show again checkbox
        self.dont_show_check = QCheckBox("Don't show this again")
        self.dont_show_check.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px;")
        layout.addWidget(self.dont_show_check)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
    
    def should_show_again(self) -> bool:
        """Check if onboarding should be shown again."""
        return not self.dont_show_check.isChecked()


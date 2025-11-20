"""Empty state widgets for better UX."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme


class EmptyStateWidget(QWidget):
    """Widget for displaying empty states with helpful messages."""
    
    def __init__(
        self,
        icon: str = "📊",
        title: str = "No Data",
        message: str = "There's nothing here yet.",
        action_text: Optional[str] = None,
        action_callback: Optional[callable] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            padding: {SPACING.LARGE}px;
        """)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.H3}px;
            font-weight: {TYPOGRAPHY.BOLD};
            padding: {SPACING.SMALL}px;
        """)
        layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            color: {current_colors.TEXT_SECONDARY};
            font-size: {TYPOGRAPHY.BODY}px;
            padding: {SPACING.SMALL}px {SPACING.LARGE}px;
        """)
        layout.addWidget(message_label)
        
        # Action button
        if action_text and action_callback:
            action_btn = QPushButton(action_text)
            action_btn.setObjectName("accentButton")
            action_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
            action_btn.setMinimumWidth(200)
            action_btn.clicked.connect(action_callback)
            layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()


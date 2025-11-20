"""Loading indicator widget for async operations."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QMovie

from app.design_constants import SPACING, TYPOGRAPHY
from app.theme import get_current_theme


class LoadingIndicator(QWidget):
    """Simple loading indicator widget."""
    
    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.SMALL)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"""
            color: {current_colors.TEXT_SECONDARY};
            font-size: {TYPOGRAPHY.SMALL}px;
            padding: {SPACING.MEDIUM}px;
        """)
        layout.addWidget(self.label)
        
        # Simple animated dots
        self.dots_label = QLabel("...")
        self.dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots_label.setStyleSheet(f"""
            color: {current_colors.ACCENT};
            font-size: {TYPOGRAPHY.H3}px;
            font-weight: {TYPOGRAPHY.BOLD};
        """)
        layout.addWidget(self.dots_label)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_dots)
        self.dot_count = 0
        self.max_dots = 3
    
    def _animate_dots(self) -> None:
        """Animate loading dots."""
        self.dot_count = (self.dot_count + 1) % (self.max_dots + 1)
        dots = "." * self.dot_count
        self.dots_label.setText(dots)
    
    def start(self) -> None:
        """Start the loading animation."""
        self.timer.start(500)  # Update every 500ms
        self.show()
    
    def stop(self) -> None:
        """Stop the loading animation."""
        self.timer.stop()
        self.hide()
    
    def set_message(self, message: str) -> None:
        """Update the loading message."""
        self.label.setText(message)


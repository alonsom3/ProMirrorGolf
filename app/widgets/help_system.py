"""Help system with context-sensitive help."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme

logger = logging.getLogger(__name__)


class HelpDialog(QDialog):
    """Help dialog with documentation."""
    
    HELP_CONTENT = {
        "main": """
        <h2>ProMirror Golf - Help</h2>
        <h3>Getting Started</h3>
        <p><b>Starting a Session:</b> Click "Start Session" or press Ctrl+S. Enter a session name and select your club.</p>
        <p><b>Recording Shots:</b> Shots are automatically recorded when detected by the system.</p>
        <p><b>Reviewing Shots:</b> Double-click a shot in the table to open the shot review window.</p>
        
        <h3>Keyboard Shortcuts</h3>
        <ul>
        <li><b>Ctrl+S:</b> Start session</li>
        <li><b>Ctrl+Shift+S:</b> Stop session</li>
        <li><b>Ctrl+B:</b> Browse sessions</li>
        <li><b>Ctrl+A:</b> Open analysis</li>
        <li><b>Ctrl+,:</b> Open settings</li>
        </ul>
        
        <h3>Features</h3>
        <p><b>Analysis Dashboard:</b> View trends, statistics, and charts for your shots.</p>
        <p><b>Session Browser:</b> Browse and manage past sessions.</p>
        <p><b>Shot Review:</b> Review videos with drawing tools and annotations.</p>
        <p><b>Export:</b> Export data to CSV, JSON, Excel, or PDF formats.</p>
        """,
        "shot_review": """
        <h2>Shot Review Window</h2>
        <h3>Video Controls</h3>
        <ul>
        <li><b>Space:</b> Play/Pause</li>
        <li><b>S:</b> Stop</li>
        <li><b>Left/Right:</b> Navigate frames</li>
        <li><b>Ctrl+Left/Right:</b> Seek 30 frames</li>
        </ul>
        
        <h3>Drawing Tools</h3>
        <ul>
        <li><b>D:</b> Freehand drawing</li>
        <li><b>P:</b> Swing plane line</li>
        <li><b>R:</b> Reference line</li>
        <li><b>E:</b> Select tool</li>
        <li><b>C:</b> Clear all drawings</li>
        </ul>
        
        <h3>Shot Actions</h3>
        <ul>
        <li><b>F:</b> Toggle favorite</li>
        <li><b>T:</b> Edit tags</li>
        <li><b>N:</b> Edit notes</li>
        </ul>
        """,
        "analysis": """
        <h2>Analysis Dashboard</h2>
        <h3>Charts</h3>
        <p>The dashboard shows multiple charts:</p>
        <ul>
        <li><b>Speed Trends:</b> Club and ball speed over time with moving averages</li>
        <li><b>Distance Trends:</b> Carry and total distance over time</li>
        <li><b>Spin Rate:</b> Spin rate trends</li>
        <li><b>Dispersion:</b> Shot dispersion heat map or scatter plot</li>
        <li><b>Club Comparison:</b> Average performance by club</li>
        <li><b>Distribution:</b> Histogram of carry distances</li>
        </ul>
        
        <h3>Filters</h3>
        <p>Use the period and club filters to analyze specific time ranges or clubs.</p>
        
        <h3>Export</h3>
        <p>Export charts as images or export data to CSV/Excel formats.</p>
        """,
    }
    
    def __init__(self, topic: str = "main", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle("Help")
        self.setMinimumSize(700, 600)
        self.resize(900, 700)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        
        # Set content
        content = self.HELP_CONTENT.get(topic, self.HELP_CONTENT["main"])
        self.content_browser.setHtml(content)
        
        layout.addWidget(self.content_browser)
        
        # Topic selector
        topic_layout = QHBoxLayout()
        topic_label = QLabel("Topic:")
        topic_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        topic_layout.addWidget(topic_label)
        
        from PyQt6.QtWidgets import QComboBox
        topic_combo = QComboBox()
        topic_combo.addItems(["Main", "Shot Review", "Analysis"])
        topic_combo.setCurrentText(topic.replace("_", " ").title())
        topic_combo.currentTextChanged.connect(self._change_topic)
        topic_layout.addWidget(topic_combo)
        topic_layout.addStretch()
        layout.addLayout(topic_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _change_topic(self, topic: str) -> None:
        """Change help topic."""
        topic_key = topic.lower().replace(" ", "_")
        content = self.HELP_CONTENT.get(topic_key, self.HELP_CONTENT["main"])
        self.content_browser.setHtml(content)


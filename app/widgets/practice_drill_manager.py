"""Practice drill manager widget."""

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
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.practice_drills import PracticeDrillManager, Drill

logger = logging.getLogger(__name__)


class PracticeDrillDialog(QDialog):
    """Dialog for managing and starting practice drills."""
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session_manager = session_manager
        self.selected_drill: Optional[Drill] = None
        
        drills_file = Path("data/practice_drills.json")
        sessions_file = Path("data/drill_sessions.json")
        self.drill_manager = PracticeDrillManager(drills_file, sessions_file)
        
        self.setWindowTitle("Practice Drills")
        self.setMinimumSize(700, 600)
        self.resize(900, 700)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header_label = QLabel("Practice Drills & Exercises")
        header_label.setStyleSheet(f"""
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.H2}px;
            font-weight: {TYPOGRAPHY.BOLD};
            padding-bottom: {SPACING.MEDIUM}px;
        """)
        layout.addWidget(header_label)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(SPACING.MEDIUM)
        
        # Drill list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Available Drills:")
        list_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        list_layout.addWidget(list_label)
        
        self.drill_list = QListWidget()
        self.drill_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.SMALL}px;
            }}
            QListWidget::item {{
                padding: {SPACING.SMALL}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                margin: {SPACING.XS}px;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
            }}
        """)
        
        for drill in self.drill_manager.get_all_drills():
            item = QListWidgetItem(f"{drill.name} ({drill.category})")
            item.setData(Qt.ItemDataRole.UserRole, drill)
            self.drill_list.addItem(item)
        
        self.drill_list.currentItemChanged.connect(self._on_drill_selected)
        list_layout.addWidget(self.drill_list)
        content_layout.addWidget(list_widget, 1)
        
        # Drill details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Drill Details:")
        details_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        details_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        details_layout.addWidget(self.details_text, 1)
        
        content_layout.addWidget(details_widget, 1)
        layout.addLayout(content_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._start_drill)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_drill_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle drill selection."""
        if current:
            drill = current.data(Qt.ItemDataRole.UserRole)
            if drill:
                self.selected_drill = drill
                details = f"""
<h3>{drill.name}</h3>
<p><b>Category:</b> {drill.category}</p>
<p><b>Difficulty:</b> {drill.difficulty}</p>
<p><b>Duration:</b> {drill.duration_minutes} minutes</p>
<p><b>Description:</b> {drill.description}</p>
<h4>Instructions:</h4>
<ol>
"""
                for instruction in drill.instructions:
                    details += f"<li>{instruction}</li>\n"
                details += "</ol>"
                
                if drill.target_metrics:
                    details += "<h4>Target Metrics:</h4><ul>"
                    for metric, value in drill.target_metrics.items():
                        details += f"<li><b>{metric}:</b> {value}</li>"
                    details += "</ul>"
                
                self.details_text.setHtml(details)
    
    def _start_drill(self) -> None:
        """Start selected drill."""
        if not self.selected_drill:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Drill Selected", "Please select a drill to start.")
            return
        
        # Create drill session
        session_id = None
        if self.session_manager:
            # Get current session ID if available
            # This would need to be passed in or retrieved
            pass
        
        drill_session = self.drill_manager.start_drill_session(
            self.selected_drill.name,
            session_id=session_id
        )
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Drill Started",
            f"Started drill: {self.selected_drill.name}\n\n"
            f"Follow the instructions and take your shots. "
            f"The drill will track your progress."
        )
        
        self.accept()


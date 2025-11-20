"""Dialog for saving a filter preset."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme


class PresetSaveDialog(QDialog):
    """Dialog for saving a filter preset."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle("Save Filter Preset")
        self.setMinimumSize(400, 200)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Name
        name_label = QLabel("Preset Name:")
        name_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter preset name...")
        self.name_edit.setMinimumHeight(SIZES.INPUT_MIN_HEIGHT)
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {current_colors.ACCENT};
            }}
        """)
        layout.addWidget(self.name_edit)
        
        # Description
        desc_label = QLabel("Description (optional):")
        desc_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; margin-top: {SPACING.SMALL}px;")
        layout.addWidget(desc_label)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Describe this filter preset...")
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
        """)
        layout.addWidget(self.desc_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_preset_info(self) -> tuple[str, str]:
        """Get preset name and description."""
        return (
            self.name_edit.text().strip(),
            self.desc_edit.toPlainText().strip(),
        )


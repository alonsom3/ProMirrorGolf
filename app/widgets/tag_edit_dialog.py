"""Tag editing dialog with autocomplete and suggestions."""

from __future__ import annotations

import logging
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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.theme import get_current_theme
from app.widgets.tag_input import TagInputWidget
from core.tag_manager import TagManager

logger = logging.getLogger(__name__)


class TagEditDialog(QDialog):
    """Dialog for editing tags with autocomplete and suggestions."""
    
    def __init__(
        self,
        tag_manager: TagManager,
        current_tags: list[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.tag_manager = tag_manager
        self.current_tags = current_tags.copy()
        self.setWindowTitle("Edit Tags")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import SPACING
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Instructions
        info_label = QLabel(
            "Enter tags below. Use comma to separate multiple tags.\n"
            "Autocomplete suggestions will appear as you type."
        )
        info_label.setAutoFillBackground(True)
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-style: italic; padding: 0px; margin: 0px;")
        info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout.addWidget(info_label)
        
        # Tag input widget
        self.tag_input = TagInputWidget(self.tag_manager, self)
        self.tag_input.set_tags(self.current_tags)
        layout.addWidget(self.tag_input, 1)
        
        # Current tags display
        current_label = QLabel("Current Tags:")
        current_label.setAutoFillBackground(True)
        from app.design_constants import  SPACING, TYPOGRAPHY
        current_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: {TYPOGRAPHY.BOLD}; margin-top: {SPACING.SMALL}px; padding: 0px; margin-bottom: 0px;")
        layout.addWidget(current_label)
        
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(120)
        from app.design_constants import  SIZES, SPACING, TYPOGRAPHY
        self.tags_list.setStyleSheet(f"""

            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QListWidget::item {{
                padding: 6px {SPACING.MEDIUM}px;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
        """)
        self._update_tags_list()
        layout.addWidget(self.tags_list)
        
        # Connect tag changes
        self.tag_input.tags_changed.connect(self._on_tags_changed)
        
        # Remove tag buttons
        remove_layout = QHBoxLayout()
        remove_layout.setContentsMargins(0, 0, 0, 0)
        
        remove_selected_btn = QPushButton("Remove Selected")
        remove_selected_btn.setMinimumHeight(28)
        remove_selected_btn.setMaximumHeight(36)
        remove_selected_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        from app.design_constants import  SIZES, SPACING, TYPOGRAPHY
        remove_selected_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 4px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        remove_selected_btn.clicked.connect(self._remove_selected_tag)
        remove_layout.addWidget(remove_selected_btn)
        
        remove_layout.addStretch()
        layout.addLayout(remove_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_tags_changed(self, tags: list[str]) -> None:
        """Handle tag changes."""
        self.current_tags = tags.copy()
        self._update_tags_list()
    
    def _update_tags_list(self) -> None:
        """Update tags list display."""
        self.tags_list.clear()
        for tag in self.current_tags:
            item = QListWidgetItem(tag)
            self.tags_list.addItem(item)
    
    def _remove_selected_tag(self) -> None:
        """Remove selected tag from list."""
        current_item = self.tags_list.currentItem()
        if current_item:
            tag_to_remove = current_item.text()
            if tag_to_remove in self.current_tags:
                self.current_tags.remove(tag_to_remove)
                self.tag_input.set_tags(self.current_tags)
                self._update_tags_list()
    
    def get_tags(self) -> list[str]:
        """Get current tags."""
        return self.tag_input.get_tags()


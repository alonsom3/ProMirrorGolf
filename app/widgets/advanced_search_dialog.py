"""Advanced search dialog with visual filter builder and saved presets."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.search import FilterOperator

logger = logging.getLogger(__name__)


class AdvancedSearchDialog(QDialog):
    """Dialog for building advanced search queries with visual filter builder.
    
    Features:
    - Visual filter builder with drag-and-drop criteria
    - Saved search presets (save/load functionality)
    - Multiple operators (equals, greater than, between, etc.)
    - Support for all shot data fields
    """
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session_manager = session_manager
        self.setWindowTitle("Advanced Search")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)
        self.setStyleSheet(get_current_theme())
        
        # Load saved presets
        self.presets_file = Path("data/search_presets.json")
        self.presets = self._load_presets()
        
        self.criteria: list[dict] = []
        
        self._build_ui()
    
    def _load_presets(self) -> dict:
        """Load saved search presets."""
        if not self.presets_file.exists():
            return {}
        
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error loading presets: %s", e)
            return {}
    
    def _save_presets(self) -> None:
        """Save search presets."""
        try:
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving presets: %s", e)
    
    def _build_ui(self) -> None:
        """Build the UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Presets section
        presets_label = QLabel("Saved Presets:")
        presets_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(presets_label)
        
        presets_layout = QHBoxLayout()
        self.presets_combo = QComboBox()
        self.presets_combo.addItem("-- Select Preset --", None)
        for name in self.presets.keys():
            self.presets_combo.addItem(name, name)
        self.presets_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        self.presets_combo.currentIndexChanged.connect(self._load_preset)
        presets_layout.addWidget(self.presets_combo)
        
        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        save_preset_btn.clicked.connect(self._save_preset)
        presets_layout.addWidget(save_preset_btn)
        presets_layout.addStretch()
        layout.addLayout(presets_layout)
        
        # Filters section
        filters_label = QLabel("Search Filters:")
        filters_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(filters_label)
        
        # Filter list
        self.filters_list = QListWidget()
        self.filters_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
        """)
        layout.addWidget(self.filters_list, 1)
        
        # Add filter button
        add_filter_btn = QPushButton("+ Add Filter")
        add_filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        add_filter_btn.clicked.connect(self._add_filter)
        layout.addWidget(add_filter_btn)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply_search)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _add_filter(self) -> None:
        """Add a new filter criterion."""
        from app.widgets.filter_criterion_widget import FilterCriterionWidget
        
        widget = FilterCriterionWidget(self)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.filters_list.addItem(item)
        self.filters_list.setItemWidget(item, widget)
        self.criteria.append(widget.get_criterion())
    
    def _load_preset(self, index: int) -> None:
        """Load a saved preset."""
        preset_name = self.presets_combo.itemData(index)
        if not preset_name or preset_name not in self.presets:
            return
        
        preset = self.presets[preset_name]
        self.criteria = preset.get("criteria", [])
        
        # Clear and rebuild filter list
        self.filters_list.clear()
        for criterion in self.criteria:
            from app.widgets.filter_criterion_widget import FilterCriterionWidget
            widget = FilterCriterionWidget(self, criterion)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.filters_list.addItem(item)
            self.filters_list.setItemWidget(item, widget)
    
    def _save_preset(self) -> None:
        """Save current filters as a preset."""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self,
            "Save Preset",
            "Enter preset name:",
        )
        
        if not ok or not name.strip():
            return
        
        # Collect current criteria
        criteria = []
        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            widget = self.filters_list.itemWidget(item)
            if widget and hasattr(widget, 'get_criterion'):
                criteria.append(widget.get_criterion())
        
        self.presets[name.strip()] = {"criteria": criteria}
        self._save_presets()
        
        # Update combo
        self.presets_combo.addItem(name.strip(), name.strip())
        QMessageBox.information(self, "Saved", f"Preset '{name.strip()}' saved successfully.")
    
    def _apply_search(self) -> None:
        """Apply the search and return criteria."""
        # Collect all criteria
        self.criteria = []
        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            widget = self.filters_list.itemWidget(item)
            if widget and hasattr(widget, 'get_criterion'):
                criterion = widget.get_criterion()
                if criterion.get("enabled", True):
                    self.criteria.append(criterion)
        
        self.accept()
    
    def get_criteria(self) -> list[dict]:
        """Get the search criteria."""
        return self.criteria

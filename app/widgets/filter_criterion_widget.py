"""Widget for a single filter criterion in advanced search."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from core.search import FilterOperator


class FilterCriterionWidget(QWidget):
    """Widget for editing a single filter criterion in advanced search.
    
    Supports:
    - Multiple shot data fields (speed, distance, spin, etc.)
    - Various comparison operators
    - Enable/disable individual criteria
    - Remove criteria from search
    """
    
    # Available fields for shots
    SHOT_FIELDS = {
        "club_speed": "Club Speed",
        "ball_speed": "Ball Speed",
        "spin_rate": "Spin Rate",
        "carry_distance": "Carry Distance",
        "total_distance": "Total Distance",
        "launch_angle": "Launch Angle",
        "smash_factor": "Smash Factor",
    }
    
    # Available operators
    OPERATORS = {
        FilterOperator.EQUALS: "Equals",
        FilterOperator.NOT_EQUALS: "Not Equals",
        FilterOperator.GREATER_THAN: "Greater Than",
        FilterOperator.LESS_THAN: "Less Than",
        FilterOperator.GREATER_EQUAL: "Greater or Equal",
        FilterOperator.LESS_EQUAL: "Less or Equal",
        FilterOperator.BETWEEN: "Between",
    }
    
    def __init__(self, parent: Optional[QWidget] = None, criterion: Optional[dict] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.SMALL, SPACING.SMALL, SPACING.SMALL, SPACING.SMALL)
        layout.setSpacing(SPACING.SMALL)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(criterion.get("enabled", True) if criterion else True)
        layout.addWidget(self.enabled_check)
        
        # Field selector
        self.field_combo = QComboBox()
        for field_key, field_label in self.SHOT_FIELDS.items():
            self.field_combo.addItem(field_label, field_key)
        if criterion and criterion.get("field"):
            index = self.field_combo.findData(criterion["field"])
            if index >= 0:
                self.field_combo.setCurrentIndex(index)
        self.field_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                min-width: 120px;
            }}
        """)
        layout.addWidget(self.field_combo)
        
        # Operator selector
        self.operator_combo = QComboBox()
        for op, op_label in self.OPERATORS.items():
            self.operator_combo.addItem(op_label, op.value)
        if criterion and criterion.get("operator"):
            index = self.operator_combo.findData(criterion["operator"])
            if index >= 0:
                self.operator_combo.setCurrentIndex(index)
        self.operator_combo.setStyleSheet(self.field_combo.styleSheet())
        self.operator_combo.currentIndexChanged.connect(self._update_value_widgets)
        layout.addWidget(self.operator_combo)
        
        # Value input
        self.value_widget = QWidget()
        self.value_layout = QHBoxLayout(self.value_widget)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.value_layout.setSpacing(SPACING.SMALL)
        
        self.value_spin = QSpinBox()
        self.value_spin.setMinimum(-999999)
        self.value_spin.setMaximum(999999)
        self.value_spin.setValue(int(criterion.get("value", 0)) if criterion and criterion.get("value") is not None else 0)
        self.value_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                min-width: 80px;
            }}
        """)
        self.value_layout.addWidget(self.value_spin)
        
        self.value2_spin = QSpinBox()
        self.value2_spin.setMinimum(-999999)
        self.value2_spin.setMaximum(999999)
        self.value2_spin.setValue(int(criterion.get("value2", 0)) if criterion and criterion.get("value2") is not None else 0)
        self.value2_spin.setStyleSheet(self.value_spin.styleSheet())
        self.value2_spin.hide()  # Only show for BETWEEN
        self.value_layout.addWidget(self.value2_spin)
        
        layout.addWidget(self.value_widget, 1)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.DANGER};
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                color: {current_colors.WHITE_TEXT};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {current_colors.DANGER_HOVER};
            }}
        """)
        remove_btn.clicked.connect(self._remove)
        layout.addWidget(remove_btn)
        
        self._update_value_widgets()
    
    def _update_value_widgets(self) -> None:
        """Update value widgets based on operator."""
        operator = self.operator_combo.currentData()
        if operator == FilterOperator.BETWEEN.value:
            self.value2_spin.show()
        else:
            self.value2_spin.hide()
    
    def _remove(self) -> None:
        """Remove this criterion."""
        # Find parent list widget and remove item
        parent = self.parent()
        while parent and not hasattr(parent, 'filters_list'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'filters_list'):
            for i in range(parent.filters_list.count()):
                item = parent.filters_list.item(i)
                if parent.filters_list.itemWidget(item) == self:
                    parent.filters_list.takeItem(i)
                    break
    
    def get_criterion(self) -> dict:
        """Get the criterion dictionary."""
        operator = self.operator_combo.currentData()
        value = self.value_spin.value()
        value2 = self.value2_spin.value() if operator == FilterOperator.BETWEEN.value else None
        
        return {
            "field": self.field_combo.currentData(),
            "operator": operator,
            "value": value,
            "value2": value2,
            "enabled": self.enabled_check.isChecked(),
        }

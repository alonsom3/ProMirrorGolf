"""Custom fields form widget for editing custom field values."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.custom_fields import (
    CustomField,
    CustomFieldManager,
    FieldType,
    get_custom_fields_from_json,
    set_custom_fields_to_json,
)

logger = logging.getLogger(__name__)


class CustomFieldsForm(QWidget):
    """Form widget for editing custom field values."""
    
    def __init__(
        self,
        field_manager: CustomFieldManager,
        applies_to: str,  # "shots" or "sessions"
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.field_manager = field_manager
        self.applies_to = applies_to
        self.field_widgets: dict[str, QWidget] = {}  # field_name -> widget
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build UI dynamically based on field definitions."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MEDIUM)
        
        fields = self.field_manager.get_fields_for(self.applies_to)
        
        if not fields:
            # No custom fields defined
            info_label = QLabel(f"No custom fields defined for {self.applies_to}.")
            info_label.setAutoFillBackground(True)
            info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-style: italic; padding: 0px; margin: 0px;")
            info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            layout.addWidget(info_label)
            return
        
        # Group box for custom fields
        group = QGroupBox("Custom Fields")
        group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                margin-top: {SPACING.MEDIUM}px;
                padding-top: {SPACING.MEDIUM}px;
                font-weight: {TYPOGRAPHY.BOLD};
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {SPACING.MEDIUM}px;
                padding: 0 {SPACING.XS}px;
            }}
        """)
        form_layout = QFormLayout(group)
        form_layout.setSpacing(SPACING.MEDIUM)
        form_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        for field in fields:
            widget = self._create_field_widget(field)
            if widget:
                label = QLabel(field.label + (":" if not field.label.endswith(":") else ""))
                label.setAutoFillBackground(True)
                if field.required:
                    label.setText(label.text() + " *")
                    label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
                else:
                    label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
                
                form_layout.addRow(label, widget)
                self.field_widgets[field.name] = widget
        
        layout.addWidget(group)
        layout.addStretch()
    
    def _create_field_widget(self, field: CustomField) -> Optional[QWidget]:
        """Create appropriate widget for field type."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        if field.field_type == FieldType.TEXT:
            widget = QLineEdit()
            widget.setPlaceholderText(field.description or "")
            widget.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 6px {SPACING.SMALL + SPACING.XS}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QLineEdit:focus {{
                    border: 1px solid {current_colors.ACCENT};
                }}
            """)
            if field.default_value:
                widget.setText(str(field.default_value))
            return widget
        
        elif field.field_type == FieldType.NUMBER:
            widget = QDoubleSpinBox()
            widget.setMinimum(-999999.0)
            widget.setMaximum(999999.0)
            widget.setDecimals(2)
            widget.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 6px {SPACING.SMALL + SPACING.XS}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QDoubleSpinBox:focus {{
                    border: 1px solid {current_colors.ACCENT};
                }}
            """)
            if field.default_value is not None:
                try:
                    widget.setValue(float(field.default_value))
                except:
                    pass
            return widget
        
        elif field.field_type == FieldType.BOOLEAN:
            widget = QCheckBox()
            widget.setStyleSheet(f"""
                QCheckBox {{
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    background-color: {current_colors.BACKGROUND_CONTROL};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {current_colors.ACCENT};
                    border-color: {current_colors.ACCENT};
                }}
            """)
            if field.default_value:
                widget.setChecked(bool(field.default_value))
            return widget
        
        elif field.field_type == FieldType.DATE:
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(datetime.now().date())
            widget.setStyleSheet(f"""
                QDateEdit {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 6px {SPACING.SMALL + SPACING.XS}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QDateEdit:focus {{
                    border: 1px solid {current_colors.ACCENT};
                }}
            """)
            return widget
        
        elif field.field_type == FieldType.SELECT:
            widget = QComboBox()
            widget.addItem("", None)  # Empty option
            for option in field.options:
                widget.addItem(option, option)
            widget.setStyleSheet(f"""
                QComboBox {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 6px {SPACING.SMALL + SPACING.XS}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QComboBox:focus {{
                    border: 1px solid {current_colors.ACCENT};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 24px;
                }}
            """)
            if field.default_value and field.default_value in field.options:
                idx = widget.findData(field.default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            return widget
        
        return None
    
    def get_values(self) -> dict[str, Any]:
        """Get current values from all fields."""
        values = {}
        
        for field_name, widget in self.field_widgets.items():
            field = self.field_manager.get_field(field_name)
            if not field:
                continue
            
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
                values[field_name] = value if value else None
            
            elif isinstance(widget, QDoubleSpinBox):
                values[field_name] = widget.value()
            
            elif isinstance(widget, QCheckBox):
                values[field_name] = widget.isChecked()
            
            elif isinstance(widget, QDateEdit):
                values[field_name] = widget.date().toString(Qt.DateFormat.ISODate)
            
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
                values[field_name] = value
        
        return values
    
    def set_values(self, custom_fields_json: Optional[str]) -> None:
        """Set values from JSON string."""
        values = get_custom_fields_from_json(custom_fields_json)
        
        for field_name, widget in self.field_widgets.items():
            value = values.get(field_name)
            if value is None:
                continue
            
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            
            elif isinstance(widget, QDoubleSpinBox):
                try:
                    widget.setValue(float(value))
                except:
                    pass
            
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            
            elif isinstance(widget, QDateEdit):
                try:
                    from PyQt6.QtCore import QDate
                    date = QDate.fromString(str(value), Qt.DateFormat.ISODate)
                    if date.isValid():
                        widget.setDate(date)
                except:
                    pass
            
            elif isinstance(widget, QComboBox):
                idx = widget.findData(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)


"""Custom field definition editor dialog."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.theme import get_current_theme
from core.custom_fields import CustomField, CustomFieldManager, FieldType

logger = logging.getLogger(__name__)


class CustomFieldEditor(QDialog):
    """Dialog for managing custom field definitions."""
    
    def __init__(
        self,
        field_manager: CustomFieldManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.field_manager = field_manager
        self.setWindowTitle("Custom Fields")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self._build_ui()
        self._load_fields()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Custom Fields")
        title.setAutoFillBackground(True)
        title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("Add Field")
        add_btn.setMinimumHeight(32)
        add_btn.setMaximumHeight(40)
        add_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        from app.design_constants import  SIZES, SPACING, TYPOGRAPHY
        add_btn.setStyleSheet(f"""

            QPushButton {{
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.MEDIUM}px;
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        add_btn.clicked.connect(self._add_field)
        header_layout.addWidget(add_btn)
        
        layout.addWidget(header)
        
        # Fields table
        self.fields_table = QTableWidget(0, 6)
        self.fields_table.setHorizontalHeaderLabels(["Name", "Label", "Type", "Applies To", "Required", "Actions"])
        self.fields_table.setAlternatingRowColors(True)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.fields_table.setShowGrid(False)
        self.fields_table.setSortingEnabled(True)
        self.fields_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.fields_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        header_view = self.fields_table.horizontalHeader()
        header_view.setVisible(True)
        header_view.setSectionsClickable(True)
        header_view.setStretchLastSection(True)
        
        from app.style_helpers import style_table
        from app.design_constants import  SPACING, TYPOGRAPHY
        self.fields_table.setStyleSheet(style_table() + f"""
            QTableWidget::item {{
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
            }}
            QHeaderView::section {{
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
        """)
        
        layout.addWidget(self.fields_table, 1)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
    
    def _load_fields(self) -> None:
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        """Load fields into table."""
        self.fields_table.setRowCount(0)
        
        for field in self.field_manager.get_all_fields():
            row = self.fields_table.rowCount()
            self.fields_table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(field.name)
            name_item.setData(Qt.ItemDataRole.UserRole, field.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.fields_table.setItem(row, 0, name_item)
            
            # Label
            label_item = QTableWidgetItem(field.label)
            label_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.fields_table.setItem(row, 1, label_item)
            
            # Type
            type_item = QTableWidgetItem(field.field_type.value.title())
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.fields_table.setItem(row, 2, type_item)
            
            # Applies To
            applies_item = QTableWidgetItem(field.applies_to.title())
            applies_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.fields_table.setItem(row, 3, applies_item)
            
            # Required
            required_item = QTableWidgetItem("Yes" if field.required else "No")
            required_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.fields_table.setItem(row, 4, required_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(SPACING.XS, SPACING.XS, SPACING.XS, SPACING.XS)
            actions_layout.setSpacing(SPACING.XS)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setMinimumHeight(24)
            edit_btn.setMaximumHeight(28)
            from app.style_helpers import style_button
            from app.design_constants import  SPACING, TYPOGRAPHY, SIZES
            edit_btn.setStyleSheet(f"""

                QPushButton {{
                    background-color: {current_colors.BACKGROUND_SURFACE};
                    border: 1px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 2px {SPACING.SMALL}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QPushButton:hover {{
                    background-color: {current_colors.BORDER_HOVER};
                }}
            """)
            edit_btn.clicked.connect(lambda checked, f=field: self._edit_field(f))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setMinimumHeight(24)
            delete_btn.setMaximumHeight(28)
            from app.design_constants import  SPACING, TYPOGRAPHY, SIZES
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {current_colors.DANGER};
                    border: 1px solid {current_colors.DANGER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: 2px {SPACING.SMALL}px;
                    color: {current_colors.WHITE_TEXT};
                    font-size: {TYPOGRAPHY.TINY}px;
                }}
                QPushButton:hover {{
                    background-color: {current_colors.DANGER_HOVER};
                }}
            """)
            delete_btn.clicked.connect(lambda checked, f=field: self._delete_field(f))
            actions_layout.addWidget(delete_btn)
            
            self.fields_table.setCellWidget(row, 5, actions_widget)
        
        # Set column widths
        self.fields_table.setColumnWidth(0, 150)
        self.fields_table.setColumnWidth(1, 200)
        self.fields_table.setColumnWidth(2, 100)
        self.fields_table.setColumnWidth(3, 100)
        self.fields_table.setColumnWidth(4, 80)
    
    def _add_field(self) -> None:
        """Add a new custom field."""
        dialog = self._create_field_dialog()
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._load_fields()
    
    def _edit_field(self, field: CustomField) -> None:
        """Edit an existing field."""
        dialog = self._create_field_dialog(field)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._load_fields()
    
    def _delete_field(self, field: CustomField) -> None:
        """Delete a custom field."""
        reply = QMessageBox.question(
            self,
            "Delete Field",
            f"Are you sure you want to delete the field '{field.label}'?\n\n"
            "This will remove the field definition, but existing data will remain.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.field_manager.remove_field(field.name):
                self._load_fields()
                QMessageBox.information(
                    self,
                    "Field Deleted",
                    f"Field '{field.label}' has been deleted.",
                )
    
    def _create_field_dialog(self, field: Optional[CustomField] = None) -> QDialog:
        """Create field definition dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Custom Field" if field else "Add Custom Field")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        form = QFormLayout()
        form.setSpacing(SPACING.MEDIUM)
        
        # Name (internal)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("field_name (no spaces)")
        if field:
            name_edit.setText(field.name)
            name_edit.setEnabled(False)  # Can't change name after creation
        form.addRow("Field Name:", name_edit)
        
        # Label (display)
        label_edit = QLineEdit()
        if field:
            label_edit.setText(field.label)
        form.addRow("Display Label:", label_edit)
        
        # Type
        type_combo = QComboBox()
        type_combo.addItems([ft.value.title() for ft in FieldType])
        if field:
            type_combo.setCurrentText(field.field_type.value.title())
        form.addRow("Field Type:", type_combo)
        
        # Applies To
        applies_combo = QComboBox()
        applies_combo.addItems(["Shots", "Sessions"])
        if field:
            applies_combo.setCurrentText(field.applies_to.title())
        form.addRow("Applies To:", applies_combo)
        
        # Required
        required_check = QCheckBox()
        if field:
            required_check.setChecked(field.required)
        form.addRow("Required:", required_check)
        
        # Description
        description_edit = QLineEdit()
        if field:
            description_edit.setText(field.description)
        description_edit.setPlaceholderText("Optional description")
        form.addRow("Description:", description_edit)
        
        # Options (for SELECT type)
        options_edit = QLineEdit()
        if field and field.options:
            options_edit.setText(", ".join(field.options))
        options_edit.setPlaceholderText("Option1, Option2, Option3 (for Select type)")
        form.addRow("Options (Select only):", options_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            name = name_edit.text().strip().lower().replace(" ", "_")
            label = label_edit.text().strip()
            field_type = FieldType(type_combo.currentText().lower())
            applies_to = applies_combo.currentText().lower()
            required = required_check.isChecked()
            description = description_edit.text().strip()
            options_text = options_edit.text().strip()
            options = [opt.strip() for opt in options_text.split(",") if opt.strip()] if options_text else []
            
            if not name:
                QMessageBox.warning(dialog, "Invalid Input", "Field name is required.")
                return dialog
            
            if not label:
                QMessageBox.warning(dialog, "Invalid Input", "Display label is required.")
                return dialog
            
            if field_type == FieldType.SELECT and not options:
                QMessageBox.warning(dialog, "Invalid Input", "Select type requires at least one option.")
                return dialog
            
            new_field = CustomField(
                name=name,
                field_type=field_type,
                label=label,
                description=description,
                required=required,
                options=options,
                applies_to=applies_to,
            )
            
            if field:
                # Update existing
                if self.field_manager.update_field(field.name, **new_field.to_dict()):
                    QMessageBox.information(dialog, "Success", "Field updated successfully.")
            else:
                # Add new
                if self.field_manager.add_field(new_field):
                    QMessageBox.information(dialog, "Success", "Field added successfully.")
                else:
                    QMessageBox.warning(dialog, "Error", "Field with this name already exists.")
        
        return dialog


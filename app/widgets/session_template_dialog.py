"""Session template selector and manager dialog."""

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
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.theme import get_current_theme
from core.session_templates import SessionTemplate, TemplateManager

logger = logging.getLogger(__name__)


class SessionTemplateDialog(QDialog):
    """Dialog for selecting and managing session templates."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle("Session Templates")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        templates_file = Path("data/templates.json")
        self.template_manager = TemplateManager(templates_file)
        self.selected_template: Optional[SessionTemplate] = None
        
        self._build_ui()
        self._load_templates()
    
    def _build_ui(self) -> None:
        """Build the UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        info_label = QLabel("Select a template to pre-fill session details, or create a new one:")
        info_label.setAutoFillBackground(True)
        info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: 0px; margin: 0px;")
        layout.addWidget(info_label)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(SPACING.MEDIUM)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(SPACING.SMALL)
        
        list_label = QLabel("Templates:")
        list_label.setAutoFillBackground(True)
        list_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: 0px; margin: 0px;")
        left_layout.addWidget(list_label)
        
        self.template_list = QListWidget()
        self.template_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QListWidget::item {{
                padding: {SPACING.SMALL}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.ACCENT};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        self.template_list.itemClicked.connect(self._on_template_selected)
        self.template_list.itemDoubleClicked.connect(self._on_template_double_clicked)
        left_layout.addWidget(self.template_list)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING.SMALL)
        
        self.new_btn = QPushButton("New")
        self.new_btn.setMinimumHeight(32)
        self.new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.SUCCESS};
                color: white;
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {current_colors.SUCCESS_HOVER};
            }}
        """)
        self.new_btn.clicked.connect(self._create_new_template)
        button_layout.addWidget(self.new_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(32)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.DANGER};
                color: white;
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {current_colors.DANGER_HOVER};
            }}
        """)
        self.delete_btn.clicked.connect(self._delete_template)
        button_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(button_layout)
        main_layout.addLayout(left_layout, 1)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(SPACING.SMALL)
        
        details_label = QLabel("Template Details:")
        details_label.setAutoFillBackground(True)
        details_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: 0px; margin: 0px;")
        right_layout.addWidget(details_label)
        
        name_layout = QVBoxLayout()
        name_layout.setSpacing(SPACING.XS)
        name_label = QLabel("Name:")
        name_label.setAutoFillBackground(True)
        name_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        name_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Template name")
        self.name_edit.setMinimumHeight(32)
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
                border-color: {current_colors.ACCENT};
            }}
        """)
        name_layout.addWidget(self.name_edit)
        right_layout.addLayout(name_layout)
        
        club_layout = QVBoxLayout()
        club_layout.setSpacing(SPACING.XS)
        club_label = QLabel("Club:")
        club_label.setAutoFillBackground(True)
        club_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        club_layout.addWidget(club_label)
        
        self.club_edit = QLineEdit()
        self.club_edit.setPlaceholderText("e.g., Driver, 7 Iron")
        self.club_edit.setMinimumHeight(32)
        self.club_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """)
        club_layout.addWidget(self.club_edit)
        right_layout.addLayout(club_layout)
        
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(SPACING.XS)
        notes_label = QLabel("Notes:")
        notes_label.setAutoFillBackground(True)
        notes_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Template notes...")
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QTextEdit:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """)
        notes_layout.addWidget(self.notes_edit)
        right_layout.addLayout(notes_layout)
        
        right_layout.addStretch()
        main_layout.addLayout(right_layout, 1)
        
        layout.addLayout(main_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_templates(self) -> None:
        """Load templates into the list."""
        self.template_list.clear()
        templates = self.template_manager.list_templates()
        
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
    
    def _on_template_selected(self, item: QListWidgetItem) -> None:
        """Handle template selection."""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.name_edit.setText(template.name)
            self.club_edit.setText(template.club or "")
            self.notes_edit.setText(template.notes or "")
            self.selected_template = template
    
    def _on_template_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to select and accept."""
        self._on_template_selected(item)
        self.accept()
    
    def _create_new_template(self) -> None:
        """Create a new template."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a template name.")
            return
        
        template = SessionTemplate(
            name=name,
            club=self.club_edit.text().strip() or None,
            notes=self.notes_edit.toPlainText().strip() or None,
        )
        
        self.template_manager.add_template(template)
        self._load_templates()
        
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole).name == name:
                self.template_list.setCurrentItem(item)
                self._on_template_selected(item)
                break
    
    def _delete_template(self) -> None:
        """Delete selected template."""
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a template to delete.")
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.remove_template(template.name)
            self._load_templates()
            self.name_edit.clear()
            self.club_edit.clear()
            self.notes_edit.clear()
            self.selected_template = None
    
    def _on_accept(self) -> None:
        """Handle accept button."""
        current_item = self.template_list.currentItem()
        if current_item:
            self.selected_template = current_item.data(Qt.ItemDataRole.UserRole)
        self.accept()


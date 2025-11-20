"""Layout editor dialog for customizing window layouts."""

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
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.layout_manager import LayoutManager

logger = logging.getLogger(__name__)


class LayoutEditorDialog(QDialog):
    """Dialog for managing window layouts."""
    
    def __init__(self, layout_manager: LayoutManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.layout_manager = layout_manager
        self.setWindowTitle("Layout Manager")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        self._build_ui()
        self._load_layouts()
    
    def _build_ui(self) -> None:
        """Build the UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Title
        title_label = QLabel("Saved Layouts")
        title_label.setAutoFillBackground(True)
        title_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(title_label)
        
        # Layouts list
        list_layout = QHBoxLayout()
        list_layout.setSpacing(SPACING.MEDIUM)
        
        self.layouts_list = QListWidget()
        self.layouts_list.setMinimumWidth(200)
        self.layouts_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: {SPACING.SMALL}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        self.layouts_list.itemDoubleClicked.connect(self._load_selected_layout)
        list_layout.addWidget(self.layouts_list)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(SPACING.SMALL)
        
        save_btn = QPushButton("Save Current")
        save_btn.setObjectName("accentButton")
        save_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
        save_btn.setMinimumWidth(150)
        save_btn.clicked.connect(self._save_current_layout)
        buttons_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Selected")
        load_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
        load_btn.setMinimumWidth(150)
        load_btn.clicked.connect(self._load_selected_layout)
        buttons_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
        delete_btn.setMinimumWidth(150)
        delete_btn.clicked.connect(self._delete_selected_layout)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        list_layout.addLayout(buttons_layout)
        
        layout.addLayout(list_layout)
        
        # Layout name input
        name_layout = QHBoxLayout()
        name_layout.setSpacing(SPACING.SMALL)
        
        name_label = QLabel("Layout Name:")
        name_label.setAutoFillBackground(True)
        name_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: 0px; margin: 0px;")
        name_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter layout name...")
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
        name_layout.addWidget(self.name_edit)
        
        layout.addLayout(name_layout)
        
        # Info label
        info_label = QLabel("Double-click a layout to load it, or use the buttons above.")
        info_label.setAutoFillBackground(True)
        info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.SMALL}px; margin: 0px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_layouts(self) -> None:
        """Load saved layouts into the list."""
        self.layouts_list.clear()
        layouts = self.layout_manager.list_layouts()
        
        for layout_name in sorted(layouts):
            item = QListWidgetItem(layout_name)
            item.setData(Qt.ItemDataRole.UserRole, layout_name)
            self.layouts_list.addItem(item)
    
    def _save_current_layout(self) -> None:
        """Save current window layout."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "No Name", "Please enter a layout name.")
            return
        
        # Get current layout from parent window (main window)
        parent_window = self.parent()
        # Navigate up to find MainWindow
        while parent_window:
            if hasattr(parent_window, '_main_splitter') and hasattr(parent_window, 'layout_manager'):
                break
            parent_window = parent_window.parent() if hasattr(parent_window, 'parent') else None
        
        if not parent_window or not hasattr(parent_window, '_main_splitter'):
            QMessageBox.warning(self, "Error", "Cannot access current layout. Please save from the main window.")
            return
        
        # Save layout
        try:
            if parent_window._main_splitter:
                layout_data = {
                    "sidebar_width": parent_window._main_splitter.sizes()[0] if parent_window._main_splitter.count() > 0 else 250,
                    "main_splitter": parent_window._main_splitter.sizes(),
                    "window_geometry": {
                        "width": parent_window.width(),
                        "height": parent_window.height(),
                        "x": parent_window.x(),
                        "y": parent_window.y(),
                    },
                }
                self.layout_manager.save_layout(name, layout_data)
                self._load_layouts()
                self.name_edit.clear()
                QMessageBox.information(self, "Saved", f"Layout '{name}' saved successfully.")
            else:
                QMessageBox.warning(self, "Error", "Cannot access window layout.")
        except Exception as e:
            logger.error("Error saving layout: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save layout: {str(e)}")
    
    def _load_selected_layout(self) -> None:
        """Load the selected layout."""
        current_item = self.layouts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a layout to load.")
            return
        
        layout_name = current_item.data(Qt.ItemDataRole.UserRole)
        if not layout_name:
            return
        
        # Find main window
        parent_window = self.parent()
        while parent_window:
            if hasattr(parent_window, '_main_splitter') and hasattr(parent_window, '_apply_layout'):
                break
            parent_window = parent_window.parent() if hasattr(parent_window, 'parent') else None
        
        if not parent_window:
            QMessageBox.warning(self, "Error", "Cannot access main window.")
            return
        
        try:
            layout = self.layout_manager.load_layout(layout_name)
            if not layout:
                QMessageBox.warning(self, "Not Found", f"Layout '{layout_name}' not found.")
                return
            
            # Apply layout to main window
            parent_window._apply_layout(layout)
            QMessageBox.information(self, "Loaded", f"Layout '{layout_name}' loaded successfully.")
        except Exception as e:
            logger.error("Error loading layout: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load layout: {str(e)}")
    
    def _delete_selected_layout(self) -> None:
        """Delete the selected layout."""
        current_item = self.layouts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a layout to delete.")
            return
        
        layout_name = current_item.data(Qt.ItemDataRole.UserRole)
        if not layout_name:
            return
        
        if layout_name == "default":
            QMessageBox.warning(self, "Cannot Delete", "The 'default' layout cannot be deleted.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete layout '{layout_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.layout_manager.delete_layout(layout_name):
                    self._load_layouts()
                    QMessageBox.information(self, "Deleted", f"Layout '{layout_name}' deleted successfully.")
                else:
                    QMessageBox.warning(self, "Not Found", f"Layout '{layout_name}' not found.")
            except Exception as e:
                logger.error("Error deleting layout: %s", e, exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to delete layout: {str(e)}")


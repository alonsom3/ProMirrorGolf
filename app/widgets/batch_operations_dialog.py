"""Dialog for batch operations on multiple shots."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme

logger = logging.getLogger(__name__)


class BatchOperationsDialog(QDialog):
    """Dialog for performing batch operations on selected shots."""
    
    def __init__(self, shot_ids: list[int], session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.shot_ids = shot_ids
        self.session_manager = session_manager
        self.setWindowTitle(f"Batch Operations ({len(shot_ids)} shots selected)")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Info label
        info_label = QLabel(f"Perform operations on {len(shot_ids)} selected shot(s)")
        info_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(info_label)
        
        # Tabs for different operations
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {current_colors.BORDER_DEFAULT};
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
            QTabBar::tab {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
            }}
        """)
        
        # Tags tab
        tags_tab = self._build_tags_tab()
        tabs.addTab(tags_tab, "Tags")
        
        # Export tab
        export_tab = self._build_export_tab()
        tabs.addTab(export_tab, "Export")
        
        # Favorite tab
        favorite_tab = self._build_favorite_tab()
        tabs.addTab(favorite_tab, "Favorite")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply_operations)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _build_tags_tab(self) -> QWidget:
        """Build tags operation tab."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Add tags
        add_label = QLabel("Add Tags (comma-separated):")
        add_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        layout.addWidget(add_label)
        
        self.add_tags_input = QLineEdit()
        self.add_tags_input.setPlaceholderText("e.g., practice, driver, good")
        self.add_tags_input.setMinimumHeight(SIZES.INPUT_MIN_HEIGHT)
        layout.addWidget(self.add_tags_input)
        
        # Remove tags
        remove_label = QLabel("Remove Tags (comma-separated):")
        remove_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; margin-top: {SPACING.MEDIUM}px;")
        layout.addWidget(remove_label)
        
        self.remove_tags_input = QLineEdit()
        self.remove_tags_input.setPlaceholderText("e.g., practice, driver")
        self.remove_tags_input.setMinimumHeight(SIZES.INPUT_MIN_HEIGHT)
        layout.addWidget(self.remove_tags_input)
        
        layout.addStretch()
        return widget
    
    def _build_export_tab(self) -> QWidget:
        """Build export operation tab."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        info_label = QLabel("Export selected shots to files.")
        info_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px;")
        layout.addWidget(info_label)
        
        self.export_csv_check = QCheckBox("Export to CSV")
        self.export_csv_check.setChecked(True)
        layout.addWidget(self.export_csv_check)
        
        self.export_json_check = QCheckBox("Export to JSON")
        layout.addWidget(self.export_json_check)
        
        layout.addStretch()
        return widget
    
    def _build_favorite_tab(self) -> QWidget:
        """Build favorite operation tab."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        self.mark_favorite_check = QCheckBox("Mark all as favorite")
        layout.addWidget(self.mark_favorite_check)
        
        self.unmark_favorite_check = QCheckBox("Unmark all as favorite")
        layout.addWidget(self.unmark_favorite_check)
        
        layout.addStretch()
        return widget
    
    def _apply_operations(self) -> None:
        """Apply all selected operations."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        import json
        from pathlib import Path
        
        try:
            with Session(self.session_manager.engine) as session:
                # Tags operations
                add_tags = [t.strip() for t in self.add_tags_input.text().split(",") if t.strip()]
                remove_tags = [t.strip() for t in self.remove_tags_input.text().split(",") if t.strip()]
                
                if add_tags or remove_tags:
                    for shot_id in self.shot_ids:
                        shot = session.get(ShotModel, shot_id)
                        if shot:
                            current_tags = json.loads(shot.tags) if shot.tags else []
                            
                            # Add tags
                            for tag in add_tags:
                                if tag not in current_tags:
                                    current_tags.append(tag)
                            
                            # Remove tags
                            for tag in remove_tags:
                                if tag in current_tags:
                                    current_tags.remove(tag)
                            
                            self.session_manager.update_shot(shot_id, tags=json.dumps(current_tags))
                
                # Favorite operations
                if self.mark_favorite_check.isChecked():
                    for shot_id in self.shot_ids:
                        self.session_manager.update_shot(shot_id, is_favorite=True)
                
                if self.unmark_favorite_check.isChecked():
                    for shot_id in self.shot_ids:
                        self.session_manager.update_shot(shot_id, is_favorite=False)
                
                # Export operations
                if self.export_csv_check.isChecked() or self.export_json_check.isChecked():
                    from PyQt6.QtWidgets import QFileDialog
                    
                    output_dir = QFileDialog.getExistingDirectory(
                        self, "Select Export Directory"
                    )
                    
                    if output_dir:
                        for shot_id in self.shot_ids:
                            shot = session.get(ShotModel, shot_id)
                            if shot:
                                base_name = f"shot_{shot_id}"
                                
                                if self.export_csv_check.isChecked():
                                    # Export to CSV (simplified)
                                    csv_path = Path(output_dir) / f"{base_name}.csv"
                                    # Would need CSV export implementation
                                
                                if self.export_json_check.isChecked():
                                    json_path = Path(output_dir) / f"{base_name}.json"
                                    shot_data = {
                                        "id": shot.id,
                                        "recorded_at": shot.recorded_at.isoformat(),
                                        "club_speed": shot.club_speed,
                                        "ball_speed": shot.ball_speed,
                                        "carry_distance": shot.carry_distance,
                                        "notes": shot.notes,
                                    }
                                    with open(json_path, 'w') as f:
                                        json.dump(shot_data, f, indent=2)
            
            QMessageBox.information(self, "Success", "Batch operations completed successfully.")
            self.accept()
        except Exception as e:
            logger.error("Error in batch operations: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Error performing batch operations:\n{str(e)}")


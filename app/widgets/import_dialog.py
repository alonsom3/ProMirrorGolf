"""Dialog for importing shot data from CSV and Excel files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.data_import import import_shots_from_csv, import_shots_from_excel

from app.design_constants import COLORS, SPACING, TYPOGRAPHY, SIZES
from app.style_helpers import style_button, style_input, style_label

logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Worker thread for importing data without blocking the UI."""
    
    finished = pyqtSignal(int, int)  # session_id, shots_imported
    error = pyqtSignal(str)
    
    def __init__(
        self,
        file_path: Path,
        session_manager,
        session_id: Optional[int],
        create_session: bool,
        session_name: Optional[str],
        sheet_name: Optional[str] = None,
    ):
        super().__init__()
        self.file_path = file_path
        self.session_manager = session_manager
        self.session_id = session_id
        self.create_session = create_session
        self.session_name = session_name
        self.sheet_name = sheet_name
    
    def run(self):
        """Run the import in a background thread."""
        try:
            if self.file_path.suffix.lower() == ".csv":
                session_id, shots_imported = import_shots_from_csv(
                    self.file_path,
                    self.session_manager,
                    self.session_id,
                    self.create_session,
                    self.session_name,
                )
            elif self.file_path.suffix.lower() in [".xlsx", ".xls"]:
                session_id, shots_imported = import_shots_from_excel(
                    self.file_path,
                    self.session_manager,
                    self.session_id,
                    self.create_session,
                    self.session_name,
                    self.sheet_name,
                )
            else:
                self.error.emit(f"Unsupported file format: {self.file_path.suffix}")
                return
            
            if session_id < 0:
                self.error.emit("Failed to import data. Check logs for details.")
            else:
                self.finished.emit(session_id, shots_imported)
        except Exception as e:
            logger.exception("Error in import worker")
            self.error.emit(str(e))


class ImportDialog(QDialog):
    """Dialog for importing shot data from CSV/Excel files."""
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.file_path: Optional[Path] = None
        self.import_worker: Optional[ImportWorker] = None
        
        self.setWindowTitle("Import Shot Data")
        self.setMinimumSize(500, 300)
        self._build_ui()
    
    def _build_ui(self):
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # File selection
        file_group = QWidget()
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(SPACING.SMALL)
        
        file_label = QLabel("File:")
        file_label.setAutoFillBackground(True)
        file_label.setStyleSheet(style_label(weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        file_layout.addWidget(file_label)
        
        file_row = QHBoxLayout()
        file_row.setSpacing(SPACING.SMALL)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a CSV or Excel file...")
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setStyleSheet(style_input())
        file_row.addWidget(self.file_path_edit, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(style_button(variant="success"))
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        
        file_layout.addLayout(file_row)
        layout.addWidget(file_group)
        
        # Session options
        session_group = QWidget()
        session_layout = QVBoxLayout(session_group)
        session_layout.setSpacing(SPACING.SMALL)
        
        session_label = QLabel("Import to:")
        session_label.setAutoFillBackground(True)
        session_label.setStyleSheet(style_label(weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        session_layout.addWidget(session_label)
        
        self.session_mode_combo = QComboBox()
        self.session_mode_combo.addItems(["New Session", "Existing Session"])
        self.session_mode_combo.currentIndexChanged.connect(self._on_session_mode_changed)
        self.session_mode_combo.setStyleSheet(style_input())
        session_layout.addWidget(self.session_mode_combo)
        
        # Session name (for new session)
        self.session_name_widget = QWidget()
        session_name_layout = QVBoxLayout(self.session_name_widget)
        session_name_layout.setContentsMargins(0, 0, 0, 0)
        session_name_layout.setSpacing(SPACING.SMALL)
        
        session_name_label = QLabel("Session Name:")
        session_name_label.setAutoFillBackground(True)
        session_name_label.setStyleSheet(style_label(secondary=True) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        session_name_layout.addWidget(session_name_label)
        
        self.session_name_edit = QLineEdit()
        self.session_name_edit.setPlaceholderText("Leave empty to use filename")
        self.session_name_edit.setStyleSheet(style_input())
        session_name_layout.addWidget(self.session_name_edit)
        
        session_layout.addWidget(self.session_name_widget)
        
        # Existing session selector (initially hidden)
        self.existing_session_widget = QWidget()
        existing_session_layout = QVBoxLayout(self.existing_session_widget)
        existing_session_layout.setContentsMargins(0, 0, 0, 0)
        existing_session_layout.setSpacing(SPACING.SMALL)
        
        existing_session_label = QLabel("Select Session:")
        existing_session_label.setAutoFillBackground(True)
        existing_session_label.setStyleSheet(style_label(secondary=True) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        existing_session_layout.addWidget(existing_session_label)
        
        self.existing_session_combo = QComboBox()
        self.existing_session_combo.setStyleSheet(style_input())
        self._load_existing_sessions()
        existing_session_layout.addWidget(self.existing_session_combo)
        
        session_layout.addWidget(self.existing_session_widget)
        self.existing_session_widget.hide()
        
        layout.addWidget(session_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setStyleSheet(f"""

            QProgressBar {{
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_CONTROL};
                text-align: center;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QProgressBar::chunk {{
                background-color: {current_colors.SUCCESS};
                border-radius: 5px;
            }}
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._start_import)
        self.button_box.rejected.connect(self.reject)
        
        # Style buttons
        ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("Import")
        ok_btn.setStyleSheet(style_button(variant="success"))
        ok_btn.setMinimumWidth(80)
        
        cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setStyleSheet(style_button(variant="secondary"))
        cancel_btn.setMinimumWidth(80)
        
        layout.addWidget(self.button_box)
        
        # Update OK button state
        self._update_ok_button()
        self.file_path_edit.textChanged.connect(self._update_ok_button)
    
    def _browse_file(self):
        """Open file dialog to select CSV/Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Import File",
            "",
            "Data Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        
        if file_path:
            self.file_path = Path(file_path)
            self.file_path_edit.setText(str(self.file_path))
            
            # Auto-fill session name if empty
            if not self.session_name_edit.text() and self.session_mode_combo.currentIndex() == 0:
                self.session_name_edit.setText(self.file_path.stem)
    
    def _on_session_mode_changed(self, index: int):
        """Handle session mode change."""
        if index == 0:  # New Session
            self.session_name_widget.show()
            self.existing_session_widget.hide()
        else:  # Existing Session
            self.session_name_widget.hide()
            self.existing_session_widget.show()
            self._load_existing_sessions()
    
    def _load_existing_sessions(self):
        """Load existing sessions into the combo box."""
        self.existing_session_combo.clear()
        
        try:
            if not hasattr(self.session_manager, 'engine') or self.session_manager.engine is None:
                logger.debug("Session manager has no engine, skipping session load")
                return
            
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            with Session(self.session_manager.engine) as db_session:
                sessions = db_session.query(SessionModel).order_by(SessionModel.started_at.desc()).all()
                
                for sess in sessions:
                    display_name = f"{sess.name} ({sess.started_at.strftime('%Y-%m-%d %H:%M')})"
                    self.existing_session_combo.addItem(display_name, sess.id)
        except Exception as e:
            logger.debug("Error loading sessions (expected in test mode): %s", e)
    
    def _update_ok_button(self):
        """Update OK button enabled state."""
        ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        has_file = bool(self.file_path and self.file_path.exists())
        ok_btn.setEnabled(has_file)
    
    def _start_import(self):
        """Start the import process."""
        if not self.file_path or not self.file_path.exists():
            QMessageBox.warning(self, "Invalid File", "Please select a valid file.")
            return
        
        # Get session options
        is_new_session = self.session_mode_combo.currentIndex() == 0
        
        if is_new_session:
            session_id = None
            session_name = self.session_name_edit.text().strip() or None
        else:
            session_id = self.existing_session_combo.currentData()
            if session_id is None:
                QMessageBox.warning(self, "No Session Selected", "Please select an existing session.")
                return
            session_name = None
        
        # Get sheet name for Excel files
        sheet_name = None
        if self.file_path.suffix.lower() in [".xlsx", ".xls"]:
            # For now, use first sheet. Could add UI for sheet selection later.
            sheet_name = None
        
        # Disable UI during import
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        ok_btn.setEnabled(False)
        cancel_btn.setEnabled(False)
        
        # Start import worker
        self.import_worker = ImportWorker(
            self.file_path,
            self.session_manager,
            session_id,
            is_new_session,
            session_name,
            sheet_name,
        )
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()
    
    def _on_import_finished(self, session_id: int, shots_imported: int):
        """Handle import completion."""
        self.progress_bar.hide()
        
        ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        ok_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {shots_imported} shot(s) to session #{session_id}.",
        )
        
        self.accept()
    
    def _on_import_error(self, error_msg: str):
        """Handle import error."""
        self.progress_bar.hide()
        
        ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        ok_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Import Error", f"Failed to import data:\n\n{error_msg}")
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.terminate()
            self.import_worker.wait()
        event.accept()


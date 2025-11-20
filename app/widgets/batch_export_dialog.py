"""Batch video export dialog with queue system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.video_export import export_dual_video_side_by_side, export_video_with_drawings

logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Worker thread for batch video export."""
    
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, export_jobs: list[dict], parent=None):
        super().__init__(parent)
        self.export_jobs = export_jobs
        self.cancelled = False
    
    def cancel(self):
        """Cancel export operation."""
        self.cancelled = True
    
    def run(self):
        """Execute export jobs."""
        total = len(self.export_jobs)
        success_count = 0
        
        for idx, job in enumerate(self.export_jobs):
            if self.cancelled:
                self.finished.emit(False, "Export cancelled by user.")
                return
            
            self.progress.emit(idx + 1, total, job.get('name', 'Unknown'))
            
            try:
                if job['format'] == 'side_by_side':
                    success = export_dual_video_side_by_side(
                        job.get('dtl_path'),
                        job.get('face_path'),
                        job['output_path'],
                        job.get('dtl_lines', []),
                        job.get('face_lines', []),
                        job.get('dtl_overlay', ''),
                        job.get('face_overlay', ''),
                        job.get('codec', 'mp4v'),
                        job.get('fps', 30.0),
                        job.get('start_frame'),
                        job.get('end_frame'),
                        job.get('scale_factor', 1.0),
                    )
                else:
                    success = export_video_with_drawings(
                        job['video_path'],
                        job['output_path'],
                        job.get('lines', []),
                        job.get('overlay_text', ''),
                        job.get('codec', 'mp4v'),
                        job.get('fps', 30.0),
                        job.get('start_frame'),
                        job.get('end_frame'),
                        job.get('quality'),
                        job.get('scale_factor', 1.0),
                    )
                
                if success:
                    success_count += 1
            except Exception as e:
                logger.error("Error exporting %s: %s", job.get('name', 'Unknown'), e, exc_info=True)
        
        if self.cancelled:
            self.finished.emit(False, "Export cancelled.")
        else:
            self.finished.emit(
                True,
                f"Export complete: {success_count}/{total} videos exported successfully."
            )


class BatchExportDialog(QDialog):
    """Dialog for batch video export with progress tracking."""
    
    def __init__(self, export_jobs: list[dict], parent: Optional[QWidget] = None):
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.export_jobs = export_jobs
        self.worker: Optional[ExportWorker] = None
        
        self.setWindowTitle(f"Batch Export ({len(export_jobs)} videos)")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Status label
        self.status_label = QLabel("Preparing export...")
        self.status_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(export_jobs))
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_CONTROL};
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {current_colors.ACCENT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Job list
        jobs_label = QLabel("Export Queue:")
        jobs_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(jobs_label)
        
        self.jobs_list = QListWidget()
        self.jobs_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
            QListWidgetItem {{
                color: {current_colors.TEXT_PRIMARY};
                padding: {SPACING.SMALL}px;
            }}
        """)
        for job in export_jobs:
            item = QListWidgetItem(job.get('name', 'Unknown'))
            self.jobs_list.addItem(item)
        layout.addWidget(self.jobs_list, 1)
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        self.cancel_btn.clicked.connect(self._cancel_export)
        buttons.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons)
        
        # Start export
        self._start_export()
    
    def _start_export(self):
        """Start the export process."""
        self.worker = ExportWorker(self.export_jobs, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, current: int, total: int, filename: str):
        """Update progress."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Exporting {filename}... ({current}/{total})")
        
        # Update list item
        if current > 0 and current <= self.jobs_list.count():
            item = self.jobs_list.item(current - 1)
            if item:
                item.setText(f"✓ {item.text()}")
    
    def _on_finished(self, success: bool, message: str):
        """Handle export completion."""
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(message)
        self.cancel_btn.setText("Close")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)
        
        if not success:
            QMessageBox.warning(self, "Export Warning", message)
    
    def _cancel_export(self):
        """Cancel the export."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Export",
                "Are you sure you want to cancel the export?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait()
                self.reject()
        else:
            self.reject()
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        event.accept()


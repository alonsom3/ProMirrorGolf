"""Report builder dialog for creating custom reports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
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
from core.report_builder import ReportBuilder, ReportFormat, ReportSection, ReportTemplate

logger = logging.getLogger(__name__)


class ReportBuilderDialog(QDialog):
    """Dialog for building custom reports."""
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.session_manager = session_manager
        self.report_builder = ReportBuilder(session_manager)
        self.selected_template: Optional[ReportTemplate] = None
        
        self.setWindowTitle("Report Builder")
        self.setMinimumSize(700, 600)
        self.resize(900, 700)
        self.setStyleSheet(get_current_theme())
        
        self._build_ui()
        self._load_templates()
    
    def _build_ui(self) -> None:
        """Build the UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Template selection
        template_label = QLabel("Select Template:")
        template_label.setAutoFillBackground(True)
        template_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.setStyleSheet(f"""

            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)
        
        # Template description
        self.template_desc = QLabel("")
        self.template_desc.setAutoFillBackground(True)
        self.template_desc.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.SMALL}px; margin: 0px;")
        self.template_desc.setWordWrap(True)
        layout.addWidget(self.template_desc)
        
        # Sections list
        sections_label = QLabel("Report Sections:")
        sections_label.setAutoFillBackground(True)
        sections_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(sections_label)
        
        self.sections_list = QListWidget()
        self.sections_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QListWidget::item {{
                padding: {SPACING.SMALL}px;
                border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        layout.addWidget(self.sections_list, 1)
        
        # Filters section
        filters_label = QLabel("Filters:")
        filters_label.setAutoFillBackground(True)
        filters_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(filters_label)
        
        filters_layout = QHBoxLayout()
        
        # Date range
        date_label = QLabel("Date Range:")
        date_label.setAutoFillBackground(True)
        date_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        filters_layout.addWidget(date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
        """)
        filters_layout.addWidget(self.start_date)
        
        end_label = QLabel("to")
        end_label.setAutoFillBackground(True)
        end_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        filters_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(self.start_date.styleSheet())
        filters_layout.addWidget(self.end_date)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Club filter
        club_layout = QHBoxLayout()
        club_label = QLabel("Club:")
        club_label.setAutoFillBackground(True)
        club_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        club_layout.addWidget(club_label)
        
        self.club_combo = QComboBox()
        self.club_combo.addItem("All Clubs", None)
        self.club_combo.setStyleSheet(self.template_combo.styleSheet())
        self._load_clubs()
        club_layout.addWidget(self.club_combo)
        club_layout.addStretch()
        layout.addLayout(club_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Export Format:")
        format_label.setAutoFillBackground(True)
        format_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "HTML", "DOCX", "CSV", "Excel"])
        self.format_combo.setStyleSheet(self.template_combo.styleSheet())
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # Options section
        options_label = QLabel("Report Options:")
        options_label.setAutoFillBackground(True)
        options_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(options_label)
        
        options_layout = QHBoxLayout()
        
        self.include_charts_check = QCheckBox("Include Charts")
        self.include_charts_check.setChecked(True)
        self.include_charts_check.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px;")
        options_layout.addWidget(self.include_charts_check)
        
        self.include_stats_check = QCheckBox("Include Statistics")
        self.include_stats_check.setChecked(True)
        self.include_stats_check.setStyleSheet(self.include_charts_check.styleSheet())
        options_layout.addWidget(self.include_stats_check)
        
        self.include_tables_check = QCheckBox("Include Tables")
        self.include_tables_check.setChecked(True)
        self.include_tables_check.setStyleSheet(self.include_charts_check.styleSheet())
        options_layout.addWidget(self.include_tables_check)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._generate_report)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_templates(self) -> None:
        """Load available templates."""
        templates = self.report_builder.get_available_templates()
        
        self.template_combo.clear()
        for template in templates:
            self.template_combo.addItem(template.name, template)
        
        if templates:
            self._on_template_changed(0)
    
    def _on_template_changed(self, index: int) -> None:
        """Handle template selection change."""
        template = self.template_combo.itemData(index)
        if not template:
            return
        
        self.selected_template = template
        self.template_desc.setText(template.description)
        
        # Update sections list
        self.sections_list.clear()
        for section in sorted(template.sections, key=lambda s: s.order):
            item = QListWidgetItem(f"{section.title} ({section.content_type})")
            item.setData(Qt.ItemDataRole.UserRole, section)
            self.sections_list.addItem(item)
    
    def _generate_report(self) -> None:
        """Generate the report."""
        if not self.selected_template:
            QMessageBox.warning(self, "No Template", "Please select a template.")
            return
        
        # Get format
        format_text = self.format_combo.currentText()
        format_map = {
            "PDF": ReportFormat.PDF,
            "HTML": ReportFormat.HTML,
            "DOCX": ReportFormat.DOCX,
            "CSV": ReportFormat.CSV,
            "Excel": ReportFormat.EXCEL,
        }
        report_format = format_map.get(format_text, ReportFormat.PDF)
        
        # Get file path
        ext_map = {"PDF": "pdf", "HTML": "html", "DOCX": "docx", "CSV": "csv", "Excel": "xlsx"}
        ext = ext_map.get(format_text, "pdf")
        default_name = f"report_{self.selected_template.name.lower().replace(' ', '_')}.{ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / default_name),
            f"{format_text} Files (*.{ext});;All Files (*)"
        )
        
        if not file_path:
            return
        
        output_path = Path(file_path)
        
        # Get filters
        date_range = None
        if self.start_date.date().isValid() and self.end_date.date().isValid():
            from datetime import datetime
            from PyQt6.QtCore import QDate
            
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            
            date_range = (
                datetime(start_qdate.year(), start_qdate.month(), start_qdate.day(), 0, 0, 0),
                datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            )
        
        club_filter = self.club_combo.currentData()
        
        # Show progress
        progress = QMessageBox(self)
        progress.setWindowTitle("Generating Report")
        progress.setText("Generating report... This may take a moment.")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        
        try:
            success = self.report_builder.generate_report(
                template=self.selected_template,
                output_path=output_path,
                format=report_format,
                date_range=date_range,
                club_filter=club_filter,
                include_charts=self.include_charts_check.isChecked(),
                include_stats=self.include_stats_check.isChecked(),
                include_tables=self.include_tables_check.isChecked(),
            )
            
            progress.close()
            
            if success:
                QMessageBox.information(
                    self,
                    "Report Generated",
                    f"Report successfully generated:\n{output_path}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Generation Failed",
                    "Failed to generate report. Check logs for details."
                )
        except Exception as e:
            progress.close()
            logger.error("Error generating report: %s", e, exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred:\n{str(e)}"
            )
    
    def _load_clubs(self) -> None:
        """Load available clubs into combo box."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            with Session(self.session_manager.engine) as session:
                clubs = session.query(SessionModel.club).distinct().filter(SessionModel.club.isnot(None)).all()
                
                current_club = self.club_combo.currentData()
                self.club_combo.clear()
                self.club_combo.addItem("All Clubs", None)
                
                for (club,) in clubs:
                    if club:
                        self.club_combo.addItem(club, club)
                
                if current_club:
                    idx = self.club_combo.findData(current_club)
                    if idx >= 0:
                        self.club_combo.setCurrentIndex(idx)
        except Exception as e:
            logger.error("Error loading clubs: %s", e, exc_info=True)


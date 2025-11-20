"""Recent shots dialog."""

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
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.recent_shots import RecentShotsTracker

logger = logging.getLogger(__name__)


class RecentShotsDialog(QDialog):
    """Dialog for viewing recently reviewed shots."""
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.session_manager = session_manager
        self.setWindowTitle("Recent Shots")
        self.setMinimumSize(700, 450)  # More flexible for smaller screens
        self.resize(900, 550)  # Smaller default size
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme())
        
        # Initialize tracker
        cache_file = Path("data/recent_shots.json")
        self.tracker = RecentShotsTracker(cache_file)
        
        self._build_ui()
        self._load_recent_shots()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Recently Viewed Shots")
        title.setAutoFillBackground(True)
        title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        header.addWidget(title)
        
        header.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(32)
        clear_btn.setMaximumHeight(40)
        clear_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        clear_btn.setStyleSheet(f"""

            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 4px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        clear_btn.clicked.connect(self._clear_recent)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Table with enhanced features
        from app.widgets.enhanced_table import FilterableTableWidget
        
        self.shots_table_widget = FilterableTableWidget(
            columns=["Shot ID", "Session", "Club Speed", "Ball Speed", "Viewed"],
            filterable_columns=list(range(5)),
            table_id="recent_shots_table",
        )
        self.shots_table = self.shots_table_widget.table
        
        # Enable sorting
        self.shots_table.setSortingEnabled(True)
        
        # Enable scroll wheel
        self.shots_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.shots_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Make headers visible and clickable
        header = self.shots_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        
        # Set column widths
        self.shots_table_widget.set_column_widths([100, 200, 120, 120, 180])
        
        self.shots_table.itemDoubleClicked.connect(self._review_shot)
        layout.addWidget(self.shots_table_widget, 1)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
    
    def _load_recent_shots(self) -> None:
        """Load and display recent shots."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel, SessionModel
        
        try:
            recent = self.tracker.get_recent_shots(limit=50)
            
            self.shots_table_widget.clear()
            
            with Session(self.session_manager.engine) as db_session:
                for entry in recent:
                    shot_id = entry.get("shot_id")
                    session_id = entry.get("session_id")
                    
                    shot = db_session.get(ShotModel, shot_id)
                    if not shot:
                        continue
                    
                    session = db_session.get(SessionModel, session_id)
                    session_name = session.name if session else f"Session {session_id}"
                    
                    viewed_at = entry.get("viewed_at", "")
                    if viewed_at:
                        from datetime import datetime
                        try:
                            dt = datetime.fromisoformat(viewed_at)
                            viewed_text = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            viewed_text = viewed_at
                    else:
                        viewed_text = "--"
                    
                    shot_id_item = QTableWidgetItem(str(shot_id))
                    shot_id_item.setData(Qt.ItemDataRole.UserRole, shot_id)
                    
                    self.shots_table_widget.add_row([
                        shot_id_item,
                        session_name,
                        f"{shot.club_speed:.1f}" if shot.club_speed else "--",
                        f"{shot.ball_speed:.1f}" if shot.ball_speed else "--",
                        viewed_text,
                    ])
        except Exception as e:
            logger.error("Error loading recent shots: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load recent shots: {str(e)}")
    
    def _review_shot(self, item: QTableWidgetItem) -> None:
        """Review selected shot."""
        shot_id = item.data(Qt.ItemDataRole.UserRole)
        if shot_id:
            self._review_shot_by_id(shot_id)
    
    def _review_shot_by_id(self, shot_id: int) -> None:
        """Review shot by ID."""
        from app.widgets.shot_review_window import ShotReviewWindow
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        
        try:
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, shot_id)
                if not shot:
                    QMessageBox.warning(self, "Not Found", f"Shot {shot_id} not found.")
                    return
                
                shot_data = {
                    "ClubSpeed": shot.club_speed,
                    "BallSpeed": shot.ball_speed,
                    "TotalSpin": shot.spin_rate,
                    "LaunchAngle": shot.launch_angle,
                }
                
                dtl_path = Path(shot.dtl_video_path) if shot.dtl_video_path else None
                face_path = Path(shot.face_video_path) if shot.face_video_path else None
                
                if not dtl_path and not face_path:
                    QMessageBox.information(self, "No Video", f"Shot {shot_id} has no video files.")
                    return
                
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Shot Review - #{shot_id}")
                dialog.setMinimumSize(1200, 700)
                dialog.resize(1400, 800)
                dialog.setSizeGripEnabled(True)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
                dialog.setStyleSheet(get_current_theme())
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
                
                review = ShotReviewWindow(
                    dtl_path,
                    face_path,
                    shot_data,
                    dialog,
                    shot_id=shot_id,
                    session_manager=self.session_manager,
                )
                layout.addWidget(review)
                
                # Track this view
                self.tracker.add_shot(shot_id, shot.session_id, shot_data)
                
                dialog.exec()
        except Exception as e:
            logger.error("Error reviewing shot: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open shot review: {str(e)}")
    
    def _clear_recent(self) -> None:
        """Clear recent shots list."""
        reply = QMessageBox.question(
            self,
            "Clear Recent Shots",
            "Are you sure you want to clear the recent shots list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tracker.clear()
            self._load_recent_shots()
            QMessageBox.information(self, "Cleared", "Recent shots list cleared.")


"""Thumbnail grid view for browsing shots."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.session_manager import SessionManager

logger = logging.getLogger(__name__)


class ThumbnailWidget(QWidget):
    """Widget displaying a single shot thumbnail."""
    
    clicked = pyqtSignal(int)  # shot_id
    
    def __init__(self, shot_id: int, thumbnail_path: Optional[Path], shot_info: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.shot_id = shot_id
        self.thumbnail_path = thumbnail_path
        self.shot_info = shot_info
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the thumbnail widget UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XS, SPACING.XS, SPACING.XS, SPACING.XS)
        layout.setSpacing(SPACING.XS)
        
        # Thumbnail image
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setMinimumSize(150, 100)
        self.thumbnail_label.setMaximumSize(200, 150)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setAutoFillBackground(True)
        from app.design_constants import COLORS, SIZES
        self.thumbnail_label.setStyleSheet(f"""

            QLabel {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 2px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        if self.thumbnail_path and self.thumbnail_path.exists():
            pixmap = QPixmap(str(self.thumbnail_path))
            if not pixmap.isNull():
                self.thumbnail_label.setPixmap(pixmap)
            else:
                self.thumbnail_label.setText("No Image")
                from app.design_constants import COLORS, SIZES
                self.thumbnail_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {current_colors.BACKGROUND_CONTROL};
                        border: 2px solid {current_colors.BORDER_DEFAULT};
                        border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                        color: {current_colors.TEXT_SECONDARY};
                        padding: 0px;
                        margin: 0px;
                    }}
                """)
        else:
            self.thumbnail_label.setText("No Thumbnail")
            from app.design_constants import COLORS, SIZES
            self.thumbnail_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 2px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    color: {current_colors.TEXT_SECONDARY};
                    padding: 0px;
                    margin: 0px;
                }}
            """)
        
        layout.addWidget(self.thumbnail_label)
        
        # Shot info
        info_text = f"Shot #{self.shot_id}"
        if self.shot_info.get('ClubSpeed'):
            info_text += f"\n{self.shot_info['ClubSpeed']:.1f} mph"
        if self.shot_info.get('CarryDistance'):
            info_text += f"\n{self.shot_info['CarryDistance']:.0f} yds"
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setAutoFillBackground(True)
        from app.design_constants import COLORS, TYPOGRAPHY, SPACING
        info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                padding: {SPACING.XS}px;
                margin: 0px;
            }}
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        from app.design_constants import COLORS, SIZES, SPACING
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 2px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.XS}px;
            }}
            QWidget:hover {{
                border-color: {current_colors.ACCENT};
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.shot_id)
        super().mousePressEvent(event)


class ThumbnailGridDialog(QDialog):
    """Dialog showing shots in a thumbnail grid."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.session_manager = session_manager
        self.selected_shot_id: Optional[int] = None
        
        self.setWindowTitle("Browse Shots - Thumbnail View")
        self.setMinimumSize(1000, 700)
        self.resize(1400, 900)
        self.setStyleSheet(get_current_theme())
        
        self._build_ui()
        self._load_shots()
    
    def _build_ui(self) -> None:
        """Build the UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Header with controls
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Shot Thumbnails")
        from app.design_constants import COLORS, TYPOGRAPHY
        title.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setMaximumHeight(40)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
        refresh_btn.setStyleSheet(f"""

            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        refresh_btn.clicked.connect(self._load_shots)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        from app.design_constants import COLORS, SIZES
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
            QScrollBar:vertical {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(SPACING.MEDIUM)
        self.grid_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll, 1)
        
        # Status label
        self.status_label = QLabel("Loading shots...")
        from app.design_constants import COLORS, SPACING, TYPOGRAPHY
        self.status_label.setAutoFillBackground(True)
        self.status_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.XS}px; margin: 0px;")
        layout.addWidget(self.status_label)
    
    def _load_shots(self) -> None:
        """Load shots and display as thumbnails."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel, SessionModel
        from core.thumbnails import get_thumbnail_path
        
        # Clear existing thumbnails
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            with Session(self.session_manager.engine) as session:
                # Get all shots
                shots = session.query(ShotModel).order_by(ShotModel.recorded_at.desc()).all()
                
                if not shots:
                    self.status_label.setText("No shots found")
                    return
                
                # Load thumbnails
                row = 0
                col = 0
                max_cols = 5
                
                for shot in shots:
                    # Determine video path for thumbnail (video paths are on ShotModel, not SessionModel)
                    video_path = None
                    if shot.dtl_video_path:
                        video_path = Path(shot.dtl_video_path)
                    elif shot.face_video_path:
                        video_path = Path(shot.face_video_path)
                    
                    thumbnail_path = None
                    if video_path and video_path.exists():
                        thumbnail_path = get_thumbnail_path(video_path)
                    
                    # Build shot info
                    shot_info = {
                        'ClubSpeed': shot.club_speed,
                        'BallSpeed': shot.ball_speed,
                        'CarryDistance': shot.carry_distance,
                    }
                    
                    # Create thumbnail widget
                    thumb_widget = ThumbnailWidget(shot.id, thumbnail_path, shot_info, self)
                    thumb_widget.clicked.connect(self._on_thumbnail_clicked)
                    
                    self.grid_layout.addWidget(thumb_widget, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                
                self.status_label.setText(f"Showing {len(shots)} shot(s)")
                
        except Exception as e:
            logger.error("Error loading shots for thumbnail grid: %s", e, exc_info=True)
            self.status_label.setText(f"Error loading shots: {str(e)}")
    
    def _on_thumbnail_clicked(self, shot_id: int) -> None:
        """Handle thumbnail click - open shot review."""
        self.selected_shot_id = shot_id
        self.accept()


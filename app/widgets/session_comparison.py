"""Multi-session comparison view."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.session_manager import SessionManager, SessionModel

logger = logging.getLogger(__name__)


class SessionComparison(QDialog):
    """Compare statistics across multiple sessions."""

    def __init__(self, session_manager: SessionManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.session_manager = session_manager
        self.setWindowTitle("Session Comparison")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)
        self.setSizeGripEnabled(True)
        # Ensure window can be maximized
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self.selected_sessions: list[int] = []
        self._build_ui()
        self._load_sessions()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)

        # Session selection
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(SPACING.MEDIUM)
        
        label = QLabel("Select sessions to compare (up to 5):")
        label.setAutoFillBackground(True)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        selection_layout.addWidget(label)
        
        self.session_combo = QComboBox()
        self.session_combo.setMinimumWidth(300)
        self.session_combo.currentIndexChanged.connect(self._on_session_selected)
        self.session_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """)
        selection_layout.addWidget(self.session_combo)
        
        button_style = f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """
        
        add_btn = QPushButton("Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(button_style)
        add_btn.clicked.connect(self._add_session)
        selection_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(button_style)
        clear_btn.clicked.connect(self._clear_sessions)
        selection_layout.addWidget(clear_btn)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Selected sessions list
        selected_label = QLabel("Selected Sessions:")
        selected_label.setAutoFillBackground(True)
        selected_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        layout.addWidget(selected_label)
        
        self.selected_list = QLabel("None")
        self.selected_list.setAutoFillBackground(True)
        self.selected_list.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.SMALL}px; border: 1px solid {current_colors.BORDER_DEFAULT}; border-radius: {SIZES.BORDER_RADIUS_SMALL}px; margin: 0px;")
        layout.addWidget(self.selected_list)

        # Comparison table - wrapped in scroll area
        comparison_scroll = QScrollArea()
        comparison_scroll.setWidgetResizable(True)
        comparison_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        comparison_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        comparison_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        comparison_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {current_colors.BACKGROUND_BASE};
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
            QScrollBar:horizontal {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        
        comparison_container = QWidget()
        comparison_container.setMinimumSize(1000, 300)  # Ensure minimum size for content
        comparison_layout = QVBoxLayout(comparison_container)
        comparison_layout.setContentsMargins(0, 0, 0, 0)
        comparison_layout.setSpacing(0)
        
        self.comparison_table = QTableWidget(0, 0)
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.verticalHeader().setVisible(False)
        self.comparison_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.comparison_table.horizontalHeader().setStretchLastSection(False)
        
        # Enable sorting
        self.comparison_table.setSortingEnabled(True)
        
        # Enable scroll wheel
        self.comparison_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.comparison_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Make headers visible and clickable
        header = self.comparison_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        
        self.comparison_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                gridline-color: transparent;
                color: {current_colors.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                border: none;
                border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
            }}
            QTableWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QTableWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
            QHeaderView::section {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                border: none;
                border-bottom: 2px solid {current_colors.BORDER_DEFAULT};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.BOLD};
            }}
            QHeaderView::section:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QHeaderView::section:pressed {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        comparison_layout.addWidget(self.comparison_table)
        comparison_container.setLayout(comparison_layout)
        comparison_scroll.setWidget(comparison_container)
        layout.addWidget(comparison_scroll, 1)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        button_style = f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.BODY}px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """
        
        compare_btn = QPushButton("Compare Statistics")
        compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        compare_btn.setStyleSheet(button_style)
        compare_btn.clicked.connect(self._compare_sessions)
        buttons_layout.addWidget(compare_btn)
        
        side_by_side_btn = QPushButton("Side-by-Side Review")
        side_by_side_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        side_by_side_btn.setStyleSheet(button_style)
        side_by_side_btn.clicked.connect(self._side_by_side_review)
        buttons_layout.addWidget(side_by_side_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(button_style)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)

    def _load_sessions(self) -> None:
        """Load available sessions."""
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        
        try:
            with Session(self.session_manager.engine) as session:
                sessions = session.query(SessionModel).order_by(desc(SessionModel.started_at)).all()
                
                self.session_combo.clear()
                self.session_combo.addItem("Select a session...", None)
                
                for sess in sessions:
                    display = f"{sess.name} ({sess.started_at.strftime('%Y-%m-%d')})"
                    self.session_combo.addItem(display, sess.id)
        except Exception as e:
            logger.error("Error loading sessions: %s", e, exc_info=True)

    def _on_session_selected(self) -> None:
        """Handle session selection."""
        pass  # Handled by Add button

    def _add_session(self) -> None:
        """Add selected session to comparison."""
        session_id = self.session_combo.currentData()
        if not session_id:
            return
        
        if session_id in self.selected_sessions:
            return
        
        if len(self.selected_sessions) >= 5:
            return
        
        self.selected_sessions.append(session_id)
        self._update_selected_list()
        self.session_combo.setCurrentIndex(0)

    def _clear_sessions(self) -> None:
        """Clear all selected sessions."""
        self.selected_sessions.clear()
        self._update_selected_list()
        self.comparison_table.setRowCount(0)
        self.comparison_table.setColumnCount(0)

    def _update_selected_list(self) -> None:
        """Update the selected sessions display."""
        if not self.selected_sessions:
            self.selected_list.setText("None")
            return
        
        from sqlalchemy.orm import Session
        
        names = []
        with Session(self.session_manager.engine) as session:
            for sid in self.selected_sessions:
                sess = session.get(SessionModel, sid)
                if sess:
                    names.append(sess.name)
        
        self.selected_list.setText(", ".join(names))

    def _compare_sessions(self) -> None:
        """Compare selected sessions."""
        if not self.selected_sessions:
            return
        
        from sqlalchemy.orm import Session
        
        try:
            with Session(self.session_manager.engine) as session:
                sessions_data = []
                for sid in self.selected_sessions:
                    sess = session.get(SessionModel, sid)
                    if not sess:
                        continue
                    
                    shots = list(sess.shots) if sess.shots else []
                    club_speeds = [s.club_speed for s in shots if s.club_speed]
                    ball_speeds = [s.ball_speed for s in shots if s.ball_speed]
                    spins = [s.spin_rate for s in shots if s.spin_rate]
                    carries = [s.carry_distance for s in shots if s.carry_distance]
                    
                    sessions_data.append({
                        "name": sess.name,
                        "date": sess.started_at.strftime("%Y-%m-%d"),
                        "shots": len(shots),
                        "avg_club_speed": sum(club_speeds) / len(club_speeds) if club_speeds else None,
                        "avg_ball_speed": sum(ball_speeds) / len(ball_speeds) if ball_speeds else None,
                        "avg_spin": sum(spins) / len(spins) if spins else None,
                        "avg_carry": sum(carries) / len(carries) if carries else None,
                        "max_carry": max(carries) if carries else None,
                        "min_carry": min(carries) if carries else None,
                    })
            
            # Build comparison table
            headers = ["Metric"] + [d["name"] for d in sessions_data]
            metrics = [
                ("Date", [d["date"] for d in sessions_data]),
                ("Total Shots", [str(d["shots"]) for d in sessions_data]),
                ("Avg Club Speed", [f"{d['avg_club_speed']:.1f}" if d['avg_club_speed'] else "--" for d in sessions_data]),
                ("Avg Ball Speed", [f"{d['avg_ball_speed']:.1f}" if d['avg_ball_speed'] else "--" for d in sessions_data]),
                ("Avg Spin", [f"{d['avg_spin']:.0f}" if d['avg_spin'] else "--" for d in sessions_data]),
                ("Avg Carry", [f"{d['avg_carry']:.1f}" if d['avg_carry'] else "--" for d in sessions_data]),
                ("Max Carry", [f"{d['max_carry']:.1f}" if d['max_carry'] else "--" for d in sessions_data]),
                ("Min Carry", [f"{d['min_carry']:.1f}" if d['min_carry'] else "--" for d in sessions_data]),
            ]
            
            self.comparison_table.setColumnCount(len(headers))
            self.comparison_table.setHorizontalHeaderLabels(headers)
            self.comparison_table.setRowCount(len(metrics))
            
            for row, (metric_name, values) in enumerate(metrics):
                self.comparison_table.setItem(row, 0, QTableWidgetItem(metric_name))
                for col, value in enumerate(values, 1):
                    self.comparison_table.setItem(row, col, QTableWidgetItem(value))
            
            self.comparison_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error("Error comparing sessions: %s", e, exc_info=True)
    
    def _side_by_side_review(self) -> None:
        """Open enhanced side-by-side shot review with synchronized playback."""
        if len(self.selected_sessions) < 2:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Selection Required", "Please select at least 2 sessions for side-by-side comparison.")
            return
        
        from sqlalchemy.orm import Session
        from app.widgets.video_comparison_window import VideoComparisonWindow
        from pathlib import Path
        
        try:
            with Session(self.session_manager.engine) as session:
                sessions_data = []
                for sid in self.selected_sessions[:2]:  # Limit to 2 sessions
                    sess = session.get(SessionModel, sid)
                    if not sess or not sess.shots:
                        continue
                    
                    # Get first shot with video
                    for shot in sess.shots:
                        if shot.dtl_video_path or shot.face_video_path:
                            dtl_path = Path(shot.dtl_video_path) if shot.dtl_video_path else None
                            face_path = Path(shot.face_video_path) if shot.face_video_path else None
                            
                            shot_data = {
                                "ClubSpeed": shot.club_speed,
                                "BallSpeed": shot.ball_speed,
                                "TotalSpin": shot.spin_rate,
                                "LaunchAngle": shot.launch_angle,
                            }
                            
                            sessions_data.append({
                                "session_name": sess.name,
                                "shot_id": shot.id,
                                "dtl_path": dtl_path,
                                "face_path": face_path,
                                "shot_data": shot_data,
                            })
                            break
                
                if len(sessions_data) < 2:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "No Video", "Selected sessions don't have shots with video clips.")
                    return
                
                # Create enhanced comparison window with synchronized playback
                comp_window = VideoComparisonWindow(
                    left_video_data=sessions_data[0],
                    right_video_data=sessions_data[1],
                    parent=self,
                )
                comp_window.exec()
                
        except Exception as e:
            logger.error("Error opening side-by-side review: %s", e, exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open side-by-side review: {str(e)}")


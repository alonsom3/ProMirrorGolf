"""Session comparison visualization widget."""

from __future__ import annotations

import logging
from typing import Optional

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.session_manager import SessionModel, ShotModel

logger = logging.getLogger(__name__)


class SessionComparisonCanvas(FigureCanvas):
    """Canvas for session comparison charts."""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=current_colors.BACKGROUND_BASE)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(current_colors.BACKGROUND_SURFACE)


class SessionComparisonWidget(QWidget):
    """Widget for visualizing session comparisons."""
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session_manager = session_manager
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        layout.setSpacing(SPACING.MEDIUM)
        
        self.canvas = SessionComparisonCanvas(self, width=10, height=6)
        layout.addWidget(self.canvas)
    
    def compare_sessions(self, session_ids: list[int]) -> None:
        """Compare multiple sessions visually.
        
        Args:
            session_ids: List of session IDs to compare
        """
        from sqlalchemy.orm import Session
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.canvas.ax.clear()
        
        try:
            with Session(self.session_manager.engine) as session:
                sessions_data = []
                for sess_id in session_ids:
                    sess = session.get(SessionModel, sess_id)
                    if sess and sess.shots:
                        sessions_data.append({
                            'name': sess.name,
                            'club': sess.club or "Unknown",
                            'shots': list(sess.shots),
                        })
                
                if not sessions_data:
                    self.canvas.ax.text(0.5, 0.5, 'No session data available', 
                                     ha='center', va='center', transform=self.canvas.ax.transAxes,
                                     color=current_colors.TEXT_SECONDARY, fontsize=14)
                    self.canvas.draw()
                    return
                
                # Compare average carry distance
                session_names = [d['name'] for d in sessions_data]
                avg_carries = []
                avg_speeds = []
                
                for data in sessions_data:
                    carries = [s.carry_distance for s in data['shots'] if s.carry_distance]
                    speeds = [s.club_speed for s in data['shots'] if s.club_speed]
                    avg_carries.append(np.mean(carries) if carries else 0)
                    avg_speeds.append(np.mean(speeds) if speeds else 0)
                
                x = np.arange(len(session_names))
                width = 0.35
                
                colors = {
                    'primary': current_colors.ACCENT,
                    'secondary': current_colors.SUCCESS,
                    'text': current_colors.TEXT_PRIMARY,
                }
                
                bars1 = self.canvas.ax.bar(x - width/2, avg_carries, width, label='Avg Carry (yds)', 
                                          color=colors['primary'], alpha=0.8)
                bars2 = self.canvas.ax.bar(x + width/2, avg_speeds, width, label='Avg Speed (mph)', 
                                          color=colors['secondary'], alpha=0.8)
                
                self.canvas.ax.set_xlabel('Session', color=colors['text'])
                self.canvas.ax.set_ylabel('Value', color=colors['text'])
                self.canvas.ax.set_title('Session Comparison', color=colors['text'], fontsize=14, fontweight='bold')
                self.canvas.ax.set_xticks(x)
                self.canvas.ax.set_xticklabels(session_names, rotation=45, ha='right', color=colors['text'])
                self.canvas.ax.legend(facecolor=current_colors.BACKGROUND_SURFACE, 
                                    edgecolor=current_colors.BORDER_DEFAULT, 
                                    labelcolor=colors['text'])
                self.canvas.ax.grid(True, alpha=0.2, color=current_colors.BORDER_DEFAULT)
                
        except Exception as e:
            logger.error("Error comparing sessions: %s", e, exc_info=True)
            self.canvas.ax.text(0.5, 0.5, f'Error: {str(e)}', 
                             ha='center', va='center', transform=self.canvas.ax.transAxes,
                             color=current_colors.DANGER, fontsize=12)
        
        self.canvas.draw()


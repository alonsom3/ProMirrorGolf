"""Swing tempo visualization widget."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.analytics import calculate_tempo_ratio

logger = logging.getLogger(__name__)


class SwingTempoWidget(QWidget):
    """Widget for visualizing swing tempo with phase markers."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(get_current_theme())
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.SMALL)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.SMALL, SPACING.MEDIUM, SPACING.SMALL)
        
        # Title
        title_label = QLabel("Swing Tempo")
        title_label.setStyleSheet(f"""
            color: {current_colors.TEXT_PRIMARY};
            font-size: {TYPOGRAPHY.BODY}px;
            font-weight: {TYPOGRAPHY.BOLD};
        """)
        layout.addWidget(title_label)
        
        # Tempo display
        self.tempo_label = QLabel("Tempo: --")
        self.tempo_label.setStyleSheet(f"""
            color: {current_colors.TEXT_SECONDARY};
            font-size: {TYPOGRAPHY.SMALL}px;
        """)
        layout.addWidget(self.tempo_label)
        
        # Phase markers will be drawn in paintEvent
        self.phases = {
            "address": 0.0,
            "top": 0.0,
            "impact": 0.0,
            "finish": 0.0,
        }
        self.tempo_ratio = None
        self.total_frames = 0
        self.current_frame = 0
    
    def set_phases(self, address: float, top: float, impact: float, finish: float) -> None:
        """Set swing phase positions (as frame numbers or percentages).
        
        Args:
            address: Address phase position
            top: Top of backswing position
            impact: Impact position
            finish: Finish position
        """
        self.phases = {
            "address": address,
            "top": top,
            "impact": impact,
            "finish": finish,
        }
        self.update()
    
    def set_tempo_ratio(self, ratio: Optional[float]) -> None:
        """Set tempo ratio.
        
        Args:
            ratio: Tempo ratio (backswing/downswing)
        """
        self.tempo_ratio = ratio
        if ratio is not None:
            self.tempo_label.setText(f"Tempo Ratio: {ratio:.2f}:1")
        else:
            self.tempo_label.setText("Tempo: --")
        self.update()
    
    def set_frame_info(self, current_frame: int, total_frames: int) -> None:
        """Set current frame information.
        
        Args:
            current_frame: Current frame number
            total_frames: Total frames in video
        """
        self.current_frame = current_frame
        self.total_frames = total_frames
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw tempo timeline with phase markers."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw timeline
        margin = SPACING.MEDIUM
        timeline_y = self.height() - margin - 20
        timeline_x = margin
        timeline_width = self.width() - 2 * margin
        timeline_height = 8
        
        # Timeline background
        timeline_rect = QRectF(timeline_x, timeline_y, timeline_width, timeline_height)
        painter.fillRect(timeline_rect, QColor(current_colors.BACKGROUND_CONTROL))
        painter.setPen(QPen(QColor(current_colors.BORDER_DEFAULT), 1))
        painter.drawRect(timeline_rect)
        
        if self.total_frames == 0:
            return
        
        # Draw phase markers
        phase_colors = {
            "address": QColor(current_colors.SUCCESS),
            "top": QColor(current_colors.ACCENT),
            "impact": QColor(current_colors.DANGER),
            "finish": QColor(current_colors.SUCCESS),
        }
        
        for phase_name, phase_pos in self.phases.items():
            if phase_pos > 0:
                # Convert to percentage
                if phase_pos <= 1.0:
                    # Already a percentage
                    x_pos = timeline_x + (phase_pos * timeline_width)
                else:
                    # Frame number
                    x_pos = timeline_x + ((phase_pos / self.total_frames) * timeline_width)
                
                color = phase_colors.get(phase_name, QColor(current_colors.TEXT_SECONDARY))
                painter.setPen(QPen(color, 2))
                painter.drawLine(int(x_pos), int(timeline_y - 5), int(x_pos), int(timeline_y + timeline_height + 5))
                
                # Label
                painter.setPen(QPen(color, 1))
                painter.drawText(
                    int(x_pos - 20),
                    int(timeline_y - 10),
                    40,
                    20,
                    Qt.AlignmentFlag.AlignCenter,
                    phase_name.capitalize()
                )
        
        # Draw current frame indicator
        if self.current_frame > 0:
            current_x = timeline_x + ((self.current_frame / self.total_frames) * timeline_width)
            painter.setPen(QPen(QColor(current_colors.TEXT_PRIMARY), 3))
            painter.drawLine(int(current_x), int(timeline_y - 8), int(current_x), int(timeline_y + timeline_height + 8))


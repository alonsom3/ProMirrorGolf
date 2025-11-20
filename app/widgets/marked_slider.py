"""Custom slider with visual markers for timeline scrubber.

This module provides a QSlider subclass that can display visual markers at specific
positions along the slider track, useful for indicating key moments in video playback.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class MarkedSlider(QSlider):
    """QSlider with visual markers for key moments.
    
    Extends QSlider to display vertical line markers at specified frame positions.
    Used in the shot review window to indicate key positions (0%, 25%, 50%, 75%, 100%)
    on the video timeline.
    
    Attributes:
        markers: List of frame positions where markers should be displayed
    """
    
    def __init__(self, orientation: Qt.Orientation, parent=None):
        """Initialize the marked slider.
        
        Args:
            orientation: Slider orientation (Horizontal or Vertical)
            parent: Parent widget
        """
        super().__init__(orientation, parent)
        self.markers: list[int] = []  # Frame positions for markers
    
    def set_markers(self, frame_positions: list[int]) -> None:
        """Set marker positions (frame numbers).
        
        Args:
            frame_positions: List of frame numbers where markers should appear
        """
        self.markers = frame_positions
        self.update()  # Trigger repaint
    
    def paintEvent(self, event) -> None:
        """Override paint event to draw markers.
        
        Draws vertical line markers at the specified positions along the slider groove.
        """
        super().paintEvent(event)
        
        if not self.markers or self.maximum() == 0:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        
        groove_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self
        )
        
        handle_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self
        )
        
        # Draw markers
        from PyQt6.QtGui import QColor
        pen = QPen(QColor(255, 255, 255))  # White color
        pen.setWidth(2)
        painter.setPen(pen)
        
        for frame_pos in self.markers:
            if frame_pos < self.minimum() or frame_pos > self.maximum():
                continue
            
            # Calculate position
            ratio = (frame_pos - self.minimum()) / (self.maximum() - self.minimum()) if self.maximum() > self.minimum() else 0
            x = groove_rect.left() + int(ratio * groove_rect.width())
            y_top = groove_rect.top()
            y_bottom = groove_rect.bottom()
            
            # Draw vertical line marker
            painter.drawLine(x, y_top - 2, x, y_bottom + 2)


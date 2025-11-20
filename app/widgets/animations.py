"""Animation utilities for smooth UI transitions."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QWidget


class FadeAnimation(QPropertyAnimation):
    """Fade in/out animation for widgets."""
    
    def __init__(self, widget: QWidget, duration: int = 300, parent=None):
        super().__init__(widget, b"windowOpacity", parent)
        self.setDuration(duration)
        self.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def fade_in(self) -> None:
        """Fade widget in."""
        self.setStartValue(0.0)
        self.setEndValue(1.0)
        self.start()
    
    def fade_out(self) -> None:
        """Fade widget out."""
        self.setStartValue(1.0)
        self.setEndValue(0.0)
        self.start()


class SlideAnimation(QPropertyAnimation):
    """Slide animation for widgets."""
    
    def __init__(self, widget: QWidget, duration: int = 300, parent=None):
        super().__init__(widget, b"pos", parent)
        self.setDuration(duration)
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.widget = widget
    
    def slide_in_from_left(self, target_pos: QPoint) -> None:
        """Slide widget in from left."""
        start_pos = QPoint(target_pos.x() - self.widget.width(), target_pos.y())
        self.setStartValue(start_pos)
        self.setEndValue(target_pos)
        self.start()
    
    def slide_in_from_right(self, target_pos: QPoint) -> None:
        """Slide widget in from right."""
        start_pos = QPoint(target_pos.x() + self.widget.width(), target_pos.y())
        self.setStartValue(start_pos)
        self.setEndValue(target_pos)
        self.start()
    
    def slide_out_to_left(self) -> None:
        """Slide widget out to left."""
        current_pos = self.widget.pos()
        end_pos = QPoint(current_pos.x() - self.widget.width(), current_pos.y())
        self.setStartValue(current_pos)
        self.setEndValue(end_pos)
        self.start()
    
    def slide_out_to_right(self) -> None:
        """Slide widget out to right."""
        current_pos = self.widget.pos()
        end_pos = QPoint(current_pos.x() + self.widget.width(), current_pos.y())
        self.setStartValue(current_pos)
        self.setEndValue(end_pos)
        self.start()


class SizeAnimation(QPropertyAnimation):
    """Size animation for widgets."""
    
    def __init__(self, widget: QWidget, duration: int = 200, parent=None):
        super().__init__(widget, b"size", parent)
        self.setDuration(duration)
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.widget = widget
    
    def expand(self, target_size: QSize) -> None:
        """Expand widget to target size."""
        self.setStartValue(self.widget.size())
        self.setEndValue(target_size)
        self.start()
    
    def collapse(self, target_size: QSize) -> None:
        """Collapse widget to target size."""
        self.setStartValue(self.widget.size())
        self.setEndValue(target_size)
        self.start()


def animate_widget_fade(widget: QWidget, fade_in: bool = True, duration: int = 300) -> None:
    """Quick helper to fade a widget in or out.
    
    Args:
        widget: Widget to animate
        fade_in: True to fade in, False to fade out
        duration: Animation duration in milliseconds
    """
    animation = FadeAnimation(widget, duration)
    if fade_in:
        animation.fade_in()
    else:
        animation.fade_out()


"""Swing path tracing and visualization."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


@dataclass
class PathPoint:
    """A point on the swing path."""
    frame: int
    x: float
    y: float
    timestamp: float = 0.0


class SwingPathTracer:
    """Tracks and visualizes club head path through swing."""
    
    def __init__(self):
        """Initialize swing path tracer."""
        self.path_points: list[PathPoint] = []
        self.is_tracing = False
        self.path_color = QColor(255, 77, 77)  # Accent color
        self.path_width = 3
        self.show_path = True
    
    def start_tracing(self) -> None:
        """Start tracing swing path."""
        self.path_points.clear()
        self.is_tracing = True
    
    def stop_tracing(self) -> None:
        """Stop tracing swing path."""
        self.is_tracing = False
    
    def add_point(self, frame: int, x: float, y: float, timestamp: float = 0.0) -> None:
        """Add a point to the swing path.
        
        Args:
            frame: Frame number
            x: X coordinate
            y: Y coordinate
            timestamp: Timestamp in seconds
        """
        if self.is_tracing:
            self.path_points.append(PathPoint(frame, x, y, timestamp))
    
    def clear_path(self) -> None:
        """Clear all path points."""
        self.path_points.clear()
    
    def get_path_for_frame_range(self, start_frame: int, end_frame: int) -> list[PathPoint]:
        """Get path points within a frame range.
        
        Args:
            start_frame: Start frame
            end_frame: End frame
            
        Returns:
            List of path points in range
        """
        return [p for p in self.path_points if start_frame <= p.frame <= end_frame]
    
    def get_path_up_to_frame(self, frame: int) -> list[PathPoint]:
        """Get all path points up to a specific frame.
        
        Args:
            frame: Frame number
            
        Returns:
            List of path points up to frame
        """
        return [p for p in self.path_points if p.frame <= frame]
    
    def calculate_path_metrics(self) -> dict:
        """Calculate metrics about the swing path.
        
        Returns:
            Dictionary with path metrics
        """
        if len(self.path_points) < 2:
            return {}
        
        # Calculate total path length
        total_length = 0.0
        for i in range(1, len(self.path_points)):
            p1 = self.path_points[i - 1]
            p2 = self.path_points[i]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            total_length += (dx ** 2 + dy ** 2) ** 0.5
        
        # Calculate path straightness (deviation from straight line)
        if len(self.path_points) >= 2:
            start = self.path_points[0]
            end = self.path_points[-1]
            straight_distance = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
            straightness_ratio = straight_distance / total_length if total_length > 0 else 0
        else:
            straightness_ratio = 0
        
        return {
            "total_length": total_length,
            "point_count": len(self.path_points),
            "straightness_ratio": straightness_ratio,
            "start_frame": self.path_points[0].frame if self.path_points else 0,
            "end_frame": self.path_points[-1].frame if self.path_points else 0,
        }


"""Measurement tools for distance and angle measurement on video."""

from __future__ import annotations

import math
import logging
from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from app.design_constants import SPACING, SIZES, TYPOGRAPHY

logger = logging.getLogger(__name__)


class Measurement:
    """Represents a measurement on the video."""
    
    def __init__(self, measurement_type: str, points: list[Tuple[float, float]], 
                 value: Optional[float] = None, unit: str = "px"):
        self.measurement_type = measurement_type  # "distance" or "angle"
        self.points = points
        self.value = value
        self.unit = unit
        self.color = QColor(255, 77, 77)  # Accent color
        self.width = 2
    
    def calculate_value(self) -> Optional[float]:
        """Calculate measurement value from points."""
        if self.measurement_type == "distance":
            if len(self.points) >= 2:
                x1, y1 = self.points[0]
                x2, y2 = self.points[1]
                distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                return distance
        elif self.measurement_type == "angle":
            if len(self.points) >= 3:
                # Calculate angle at middle point
                p1 = self.points[0]
                p2 = self.points[1]  # Vertex
                p3 = self.points[2]
                
                # Vectors from vertex
                v1 = (p1[0] - p2[0], p1[1] - p2[1])
                v2 = (p3[0] - p2[0], p3[1] - p2[1])
                
                # Calculate angle
                dot = v1[0] * v2[0] + v1[1] * v2[1]
                mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
                mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
                
                if mag1 > 0 and mag2 > 0:
                    cos_angle = dot / (mag1 * mag2)
                    cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
                    angle_rad = math.acos(cos_angle)
                    angle_deg = math.degrees(angle_rad)
                    return angle_deg
        return None
    
    def draw(self, painter: QPainter, scale_factor: float = 1.0) -> None:
        """Draw the measurement on the canvas."""
        if not self.points:
            return
        
        pen = QPen(self.color, self.width)
        painter.setPen(pen)
        
        if self.measurement_type == "distance":
            if len(self.points) >= 2:
                p1 = QPointF(self.points[0][0] * scale_factor, self.points[0][1] * scale_factor)
                p2 = QPointF(self.points[1][0] * scale_factor, self.points[1][1] * scale_factor)
                
                # Draw line
                painter.drawLine(p1, p2)
                
                # Draw endpoints
                radius = 4 * scale_factor
                painter.drawEllipse(p1, radius, radius)
                painter.drawEllipse(p2, radius, radius)
                
                # Draw label with larger font
                if self.value is not None:
                    mid_x = (p1.x() + p2.x()) / 2
                    mid_y = (p1.y() + p2.y()) / 2
                    label = f"{self.value:.1f} {self.unit}"
                    # Set font for readable text
                    from PyQt6.QtGui import QFont
                    font = QFont()
                    font.setPointSize(14)
                    font.setBold(True)
                    painter.setFont(font)
                    # Draw background for better visibility
                    from PyQt6.QtGui import QFontMetrics
                    metrics = QFontMetrics(font)
                    text_rect = metrics.boundingRect(label)
                    bg_rect = text_rect.translated(int(mid_x + 5), int(mid_y - 5))
                    bg_rect.adjust(-4, -2, 4, 2)
                    painter.fillRect(bg_rect, QColor(0, 0, 0, 180))  # Semi-transparent black
                    painter.setPen(QColor(255, 255, 255))  # White text
                    painter.drawText(QPointF(mid_x + 5, mid_y - 5), label)
        
        elif self.measurement_type == "angle":
            if len(self.points) >= 3:
                p1 = QPointF(self.points[0][0] * scale_factor, self.points[0][1] * scale_factor)
                p2 = QPointF(self.points[1][0] * scale_factor, self.points[1][1] * scale_factor)
                p3 = QPointF(self.points[2][0] * scale_factor, self.points[2][1] * scale_factor)
                
                # Draw lines
                painter.drawLine(p1, p2)
                painter.drawLine(p2, p3)
                
                # Draw vertex
                radius = 5 * scale_factor
                painter.drawEllipse(p2, radius, radius)
                
                # Draw arc
                # Calculate arc bounds
                rect_size = 30 * scale_factor
                rect = QPointF(p2.x() - rect_size, p2.y() - rect_size)
                # Simple arc approximation
                painter.drawArc(int(rect.x()), int(rect.y()), 
                              int(rect_size * 2), int(rect_size * 2), 0, 5760)  # 90 degrees
                
                # Draw label with larger font
                if self.value is not None:
                    label = f"{self.value:.1f}°"
                    # Set font for readable text
                    from PyQt6.QtGui import QFont
                    font = QFont()
                    font.setPointSize(14)
                    font.setBold(True)
                    painter.setFont(font)
                    # Draw background for better visibility
                    from PyQt6.QtGui import QFontMetrics
                    metrics = QFontMetrics(font)
                    text_rect = metrics.boundingRect(label)
                    bg_rect = text_rect.translated(int(p2.x() + 10), int(p2.y() - 10))
                    bg_rect.adjust(-4, -2, 4, 2)
                    painter.fillRect(bg_rect, QColor(0, 0, 0, 180))  # Semi-transparent black
                    painter.setPen(QColor(255, 255, 255))  # White text
                    painter.drawText(QPointF(p2.x() + 10, p2.y() - 10), label)


class MeasurementTool:
    """Tool for creating measurements on video."""
    
    def __init__(self):
        self.measurements: list[Measurement] = []
        self.current_measurement: Optional[Measurement] = None
        self.measurement_type: Optional[str] = None
        self.current_points: list[Tuple[float, float]] = []
        self.measurement_history: list[Measurement] = []  # For undo/redo
    
    def start_measurement(self, measurement_type: str) -> None:
        """Start a new measurement.
        
        Args:
            measurement_type: "distance" or "angle"
        """
        self.measurement_type = measurement_type
        self.current_points = []
        self.current_measurement = None
    
    def add_point(self, x: float, y: float) -> bool:
        """Add a point to current measurement.
        
        Returns:
            True if measurement is complete
        """
        self.current_points.append((x, y))
        
        if self.measurement_type == "distance":
            if len(self.current_points) >= 2:
                self.current_measurement = Measurement("distance", self.current_points.copy())
                self.current_measurement.value = self.current_measurement.calculate_value()
                return True
        elif self.measurement_type == "angle":
            if len(self.current_points) >= 3:
                self.current_measurement = Measurement("angle", self.current_points.copy())
                self.current_measurement.value = self.current_measurement.calculate_value()
                return True
        
        return False
    
    def complete_measurement(self) -> Optional[Measurement]:
        """Complete current measurement and add to list.
        
        Returns:
            Completed measurement or None
        """
        if self.current_measurement:
            self.measurements.append(self.current_measurement)
            self.measurement_history.append(self.current_measurement)
            measurement = self.current_measurement
            self.current_measurement = None
            self.current_points = []
            self.measurement_type = None
            return measurement
        return None
    
    def save_measurements(self, shot_id: int, session_manager) -> bool:
        """Save measurements to database.
        
        Args:
            shot_id: Shot ID to associate measurements with
            session_manager: SessionManager instance
            
        Returns:
            True if saved successfully
        """
        try:
            import json
            from sqlalchemy.orm import Session
            
            # Convert measurements to JSON
            measurements_data = []
            for m in self.measurements:
                measurements_data.append({
                    "type": m.measurement_type,
                    "points": m.points,
                    "value": m.value,
                    "unit": m.unit,
                    "color": [m.color.red(), m.color.green(), m.color.blue()],
                    "width": m.width,
                })
            
            with Session(session_manager.engine) as session:
                from core.session_manager import ShotModel
                shot = session.get(ShotModel, shot_id)
                if shot:
                    # Store in custom_fields as JSON
                    custom_fields = {}
                    if shot.custom_fields:
                        try:
                            custom_fields = json.loads(shot.custom_fields)
                        except:
                            custom_fields = {}
                    
                    custom_fields["measurements"] = measurements_data
                    shot.custom_fields = json.dumps(custom_fields)
                    session.commit()
                    return True
            return False
        except Exception as e:
            logger.error("Error saving measurements: %s", e, exc_info=True)
            return False
    
    def load_measurements(self, shot_id: int, session_manager) -> bool:
        """Load measurements from database.
        
        Args:
            shot_id: Shot ID to load measurements for
            session_manager: SessionManager instance
            
        Returns:
            True if loaded successfully
        """
        try:
            import json
            from sqlalchemy.orm import Session
            
            with Session(session_manager.engine) as session:
                from core.session_manager import ShotModel
                shot = session.get(ShotModel, shot_id)
                if shot and shot.custom_fields:
                    try:
                        custom_fields = json.loads(shot.custom_fields)
                        if "measurements" in custom_fields:
                            self.measurements.clear()
                            for m_data in custom_fields["measurements"]:
                                m = Measurement(
                                    m_data["type"],
                                    m_data["points"],
                                    m_data.get("value"),
                                    m_data.get("unit", "px")
                                )
                                if "color" in m_data:
                                    m.color = QColor(*m_data["color"])
                                if "width" in m_data:
                                    m.width = m_data["width"]
                                self.measurements.append(m)
                            return True
                    except Exception as e:
                        logger.error("Error loading measurements: %s", e)
            return False
        except Exception as e:
            logger.error("Error loading measurements: %s", e, exc_info=True)
            return False
    
    def undo_last_measurement(self) -> bool:
        """Undo last measurement.
        
        Returns:
            True if measurement was undone
        """
        if self.measurements and self.measurement_history:
            last = self.measurement_history[-1]
            if last in self.measurements:
                self.measurements.remove(last)
            self.measurement_history.pop()
            return True
        return False
    
    def cancel_measurement(self) -> None:
        """Cancel current measurement."""
        self.current_measurement = None
        self.current_points = []
        self.measurement_type = None
    
    def clear_all(self) -> None:
        """Clear all measurements."""
        self.measurements.clear()
        self.current_measurement = None
        self.current_points = []
        self.measurement_type = None
    
    def get_current_preview(self) -> Optional[Measurement]:
        """Get preview of current measurement."""
        if self.current_points and self.measurement_type:
            if self.measurement_type == "distance" and len(self.current_points) >= 1:
                # Create preview with current point
                preview = Measurement("distance", self.current_points.copy())
                return preview
            elif self.measurement_type == "angle" and len(self.current_points) >= 1:
                preview = Measurement("angle", self.current_points.copy())
                return preview
        return None


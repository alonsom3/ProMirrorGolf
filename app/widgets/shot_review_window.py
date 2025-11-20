"""Side-by-side synchronized video player for reviewing shots with drawing tools."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPen, QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.theme import get_current_theme
from app.design_constants import  SPACING, TYPOGRAPHY, SIZES
from app.style_helpers import style_button, style_input, style_label

logger = logging.getLogger(__name__)


class VideoCanvas(QLabel):
    """Canvas for displaying video with drawing overlay."""
    
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title = title
        self.current_frame: Optional[np.ndarray] = None
        self.original_frame: Optional[np.ndarray] = None
        self.drawing_mode = None  # "draw", "swing_plane", "reference", "select", None
        # Lines: [(x1, y1, x2, y2, color, width), ...]
        self.lines = []
        self.current_line_start = None  # For drawing new lines
        self.selected_line_index = None  # Index of selected line for color change
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.drawing_color = QColor(current_colors.ACCENT)  # Use accent color
        self.drawing_width = 3
        # Remove fixed minimum size - let it scale responsively
        self.setMinimumSize(200, 150)  # Small minimum for very small screens
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAutoFillBackground(True)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {current_colors.BACKGROUND_BASE};
                border: 2px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                color: {current_colors.TEXT_SECONDARY};
                font-size: {TYPOGRAPHY.H3}px;
                padding: 0px;
                margin: 0px;
            }}
        """)
        self.setText(f"{title}\nWaiting for frames...")
        self.setScaledContents(False)
        self.overlay_text: str = ""
        self._original_pixmap: Optional[QPixmap] = None
        
        self.show_shot_data_overlay = True
        self.overlay_position = "top-left"
        self.overlay_metrics = ["club_speed", "ball_speed", "carry_distance"]
        self.overlay_style = {
            "background_color": QColor(0, 0, 0, 200),
            "text_color": QColor(255, 255, 255),
            "font_size": 14,
            "padding": 8,
        }
        self.shot_data_dict: dict = {}  # Shot data to display in overlay
        
        # Canvas-specific measurement tools and path tracing
        from app.widgets.measurement_tools import MeasurementTool
        from core.swing_path_tracer import SwingPathTracer
        self.measurement_tool = MeasurementTool()
        self.path_tracer = SwingPathTracer()
        
        # Undo/redo system for drawing operations
        from core.drawing_undo_redo import DrawingUndoRedoManager
        self.undo_redo_manager = DrawingUndoRedoManager(max_stack_size=100)

    def set_frame(self, frame: np.ndarray) -> None:
        """Update displayed frame."""
        self.original_frame = frame.copy()
        self.current_frame = self.original_frame.copy()
        self._update_display()

    def _get_image_coords(self, mouse_x: float, mouse_y: float) -> tuple[int, int] | None:
        """Convert mouse to image coordinates."""
        if self.original_frame is None:
            return None
        
        pixmap = self.pixmap()
        if not pixmap or pixmap.isNull():
            return None
        
        pixmap_size = pixmap.size()
        label_size = self.size()
        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2
        
        pixmap_x = mouse_x - offset_x
        pixmap_y = mouse_y - offset_y
        
        if pixmap_size.width() > 0 and pixmap_size.height() > 0:
            scale_x = self.original_frame.shape[1] / pixmap_size.width()
            scale_y = self.original_frame.shape[0] / pixmap_size.height()
            
            img_x = int(pixmap_x * scale_x)
            img_y = int(pixmap_y * scale_y)
            
            img_x = max(0, min(img_x, self.original_frame.shape[1] - 1))
            img_y = max(0, min(img_y, self.original_frame.shape[0] - 1))
            
            return (img_x, img_y)
        return None

    def _find_line_at_point(self, x: int, y: int, threshold: int = 10) -> int | None:
        """Find line index near point."""
        threshold_sq = threshold * threshold
        for i, line in enumerate(self.lines):
            x1, y1, x2, y2, _, _ = line
            
            A = x - x1
            B = y - y1
            C = x2 - x1
            D = y2 - y1
            
            dot = A * C + B * D
            len_sq = C * C + D * D
            
            if len_sq == 0:
                dist_sq = A * A + B * B
            else:
                param = dot / len_sq
                if param < 0:
                    xx, yy = x1, y1
                elif param > 1:
                    xx, yy = x2, y2
                else:
                    xx, yy = x1 + param * C, y1 + param * D
                
                dx = x - xx
                dy = y - yy
                dist_sq = dx * dx + dy * dy
            
            if dist_sq <= threshold_sq:
                return i
        return None

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if self.original_frame is None:
            return
        
        coords = self._get_image_coords(event.position().x(), event.position().y())
        if not coords:
            return
        
        img_x, img_y = coords
        
        # Right-click always selects line (even if not in select mode)
        if event.button() == Qt.MouseButton.RightButton:
            line_idx = self._find_line_at_point(img_x, img_y)
            if line_idx is not None:
                self.selected_line_index = line_idx
                # Show color picker
                if hasattr(self, 'parent_window'):
                    self.parent_window._change_line_color(self, line_idx)
            return
        
        if self.drawing_mode == "select":
            # Left-click in select mode: find and select line
            line_idx = self._find_line_at_point(img_x, img_y)
            if line_idx is not None:
                self.selected_line_index = line_idx
                # Show color picker
                if hasattr(self, 'parent_window'):
                    self.parent_window._change_line_color(self, line_idx)
        elif self.drawing_mode in ["measure_distance", "measure_angle"]:
            # Handle measurement tools - use canvas-specific tool
            if not self.measurement_tool.current_points:
                self.measurement_tool.add_point(img_x, img_y)
                self._update_display()
        elif self.drawing_mode == "path_trace":
            # Handle path tracing - use canvas-specific tracer
            if hasattr(self, 'parent_window') and self.parent_window:
                current_frame = getattr(self.parent_window, 'current_frame', 0)
                self.path_tracer.add_point(current_frame, img_x, img_y)
                self._update_display()
        elif self.drawing_mode:
            # Start drawing
            self.current_line_start = (img_x, img_y)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move - update current line preview."""
        if self.drawing_mode and self.original_frame is not None:
            coords = self._get_image_coords(event.position().x(), event.position().y())
            if not coords:
                return
            
            img_x, img_y = coords
            
            # Handle measurement tools - just update preview
            if self.drawing_mode in ["measure_distance", "measure_angle"]:
                # Preview will be drawn in _update_display
                self._update_display()
                return
            
            # Handle path tracing - use canvas-specific tracer
            if self.drawing_mode == "path_trace":
                if hasattr(self, 'parent_window') and self.parent_window:
                    current_frame = getattr(self.parent_window, 'current_frame', 0)
                    self.path_tracer.add_point(current_frame, img_x, img_y)
                    self._update_display()
                return
            
            # Handle regular drawing
            if self.current_line_start:
                # For reference lines, snap to vertical or horizontal in preview
                if self.drawing_mode == "reference":
                    x1, y1 = self.current_line_start
                    dx = abs(img_x - x1)
                    dy = abs(img_y - y1)
                    if dx > dy:
                        img_y = y1
                    else:
                        img_x = x1
                
                self._current_line_end = (img_x, img_y)
                self._update_display()

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release - complete the line."""
        if self.drawing_mode and self.original_frame is not None:
            coords = self._get_image_coords(event.position().x(), event.position().y())
            if not coords:
                return
            
            img_x, img_y = coords
            
            # Handle measurement tools - use canvas-specific tool
            if self.drawing_mode in ["measure_distance", "measure_angle"]:
                complete = self.measurement_tool.add_point(img_x, img_y)
                if complete:
                    measurement = self.measurement_tool.complete_measurement()
                    if measurement:
                        logger.debug("Measurement completed: %s = %s", 
                                   measurement.measurement_type, measurement.value)
                self._update_display()
                return
            
            # Handle path tracing - use canvas-specific tracer
            if self.drawing_mode == "path_trace":
                if hasattr(self, 'parent_window') and self.parent_window:
                    current_frame = getattr(self.parent_window, 'current_frame', 0)
                    self.path_tracer.add_point(current_frame, img_x, img_y)
                    self._update_display()
                return
            
            # Handle regular drawing
            if self.current_line_start:
                x1, y1 = self.current_line_start
                
                # For reference lines, snap to vertical or horizontal
                if self.drawing_mode == "reference":
                    dx = abs(img_x - x1)
                    dy = abs(img_y - y1)
                    if dx > dy:
                        img_y = y1
                    else:
                        img_x = x1
                
                # Add line with color and width
                new_line = (x1, y1, img_x, img_y, self.drawing_color, self.drawing_width)
                self.lines.append(new_line)
                
                # Record undo/redo action
                if hasattr(self, 'undo_redo_manager'):
                    line_index = len(self.lines) - 1
                    old_lines = self.lines.copy()
                    
                    def undo_func():
                        if line_index < len(self.lines):
                            self.lines.pop(line_index)
                            self._update_display()
                    
                    def redo_func():
                        if line_index <= len(self.lines):
                            self.lines.insert(line_index, new_line)
                            self._update_display()
                    
                    from core.drawing_undo_redo import DrawingAction
                    action = DrawingAction(
                        action_type="add_line",
                        canvas_id=self.title.lower().replace(" ", "_"),
                        data={"line_index": line_index, "line": new_line},
                        undo_func=undo_func,
                        redo_func=redo_func
                    )
                    self.undo_redo_manager.push_action(action)
                
                self.current_line_start = None
                self._current_line_end = None
                self._update_display()

    def _update_display(self) -> None:
        """Update displayed image."""
        if self.current_frame is None:
            return
        
        # Convert to RGB
        rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb.shape
        bytes_per_line = 3 * width
        qimage = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Draw overlay on original size image
        pixmap = QPixmap.fromImage(qimage)
        pixmap_size = pixmap.size()
        
        # Check if we need to draw anything
        has_lines = bool(self.lines or self.current_line_start)
        has_measurements = (bool(self.measurement_tool.measurements) or
                          bool(self.measurement_tool.current_points))
        has_path = (self.path_tracer.show_path and
                  bool(self.path_tracer.path_points))
        
        if has_lines or has_measurements or has_path:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw all completed lines with their own colors
            for i, line in enumerate(self.lines):
                x1, y1, x2, y2, color, width = line
                pen = QPen(color, width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
                # Highlight selected line
                if i == self.selected_line_index:
                    # Draw selection indicator
                    pen = QPen(QColor(255, 255, 0), width + 2)
                    painter.setPen(pen)
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw current line being drawn (preview)
            if self.current_line_start and hasattr(self, '_current_line_end') and self._current_line_end:
                x1, y1 = self.current_line_start
                x2, y2 = self._current_line_end
                pen = QPen(self.drawing_color, self.drawing_width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw measurements if available - use canvas-specific tool
            for measurement in self.measurement_tool.measurements:
                measurement.draw(painter)
            # Draw preview
            preview = self.measurement_tool.get_current_preview()
            if preview:
                preview.draw(painter)
            
            # Draw swing path if available - use canvas-specific tracer
            if self.path_tracer.show_path:
                if hasattr(self, 'parent_window') and self.parent_window:
                    current_frame = getattr(self.parent_window, 'current_frame', 0)
                    path_points = self.path_tracer.get_path_up_to_frame(current_frame)
                else:
                    path_points = self.path_tracer.get_path_up_to_frame(0)
                if len(path_points) > 1:
                    pen = QPen(self.path_tracer.path_color, 
                             self.path_tracer.path_width)
                    painter.setPen(pen)
                    for i in range(1, len(path_points)):
                        p1 = path_points[i - 1]
                        p2 = path_points[i]
                        painter.drawLine(int(p1.x), int(p1.y), int(p2.x), int(p2.y))
            
            painter.end()
        
        # Draw overlay text (playback info)
        if self.overlay_text:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            fm = QFontMetrics(painter.font())
            padding = 8
            text_width = fm.horizontalAdvance(self.overlay_text)
            text_height = fm.height()
            rect = QRectF(
                12,
                12,
                text_width + padding * 2,
                text_height + padding * 2,
            )
            painter.setBrush(QColor(0, 0, 0, 190))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor(240, 244, 250))
            painter.drawText(
                rect.adjusted(padding, padding, -padding, -padding),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self.overlay_text,
            )
            painter.end()
        
        # Draw shot data overlay (if enabled)
        if self.show_shot_data_overlay and self.shot_data_dict:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Build overlay text from selected metrics
            overlay_lines = []
            metric_labels = {
                "club_speed": "Club Speed",
                "ball_speed": "Ball Speed",
                "carry_distance": "Carry",
                "total_distance": "Total",
                "spin_rate": "Spin",
                "launch_angle": "Launch",
                "smash_factor": "Smash",
            }
            
            for metric in self.overlay_metrics:
                if metric in self.shot_data_dict:
                    value = self.shot_data_dict[metric]
                    label = metric_labels.get(metric, metric.replace("_", " ").title())
                    if isinstance(value, (int, float)):
                        if "speed" in metric:
                            overlay_lines.append(f"{label}: {value:.1f} mph")
                        elif "distance" in metric:
                            overlay_lines.append(f"{label}: {value:.1f} yds")
                        elif "spin" in metric:
                            overlay_lines.append(f"{label}: {value:.0f} rpm")
                        elif "angle" in metric:
                            overlay_lines.append(f"{label}: {value:.1f}°")
                        else:
                            overlay_lines.append(f"{label}: {value:.2f}")
                    else:
                        overlay_lines.append(f"{label}: {value}")
            
            if overlay_lines:
                # Calculate position based on overlay_position setting
                font = painter.font()
                font.setPointSize(self.overlay_style["font_size"])
                painter.setFont(font)
                fm = QFontMetrics(font)
                padding = self.overlay_style["padding"]
                line_height = fm.height()
                total_height = len(overlay_lines) * line_height + padding * 2
                max_width = max(fm.horizontalAdvance(line) for line in overlay_lines) + padding * 2
                
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                
                if self.overlay_position == "top-left":
                    x, y = 12, 12
                elif self.overlay_position == "top-right":
                    x, y = pixmap_width - max_width - 12, 12
                elif self.overlay_position == "bottom-left":
                    x, y = 12, pixmap_height - total_height - 12
                else:  # bottom-right
                    x, y = pixmap_width - max_width - 12, pixmap_height - total_height - 12
                
                rect = QRectF(x, y, max_width, total_height)
                
                # Draw background
                painter.setBrush(self.overlay_style["background_color"])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect, 6, 6)
                
                # Draw text
                painter.setPen(self.overlay_style["text_color"])
                
                y_offset = y + padding
                for line in overlay_lines:
                    painter.drawText(x + padding, y_offset, line)
                    y_offset += line_height
            
            painter.end()
        
        # Store original pixmap for scaling
        self._original_pixmap = pixmap
        
        # Scale pixmap to fit current label size while maintaining aspect ratio
        self._scale_pixmap_to_fit()
    
    def resizeEvent(self, event) -> None:
        """Handle resize events to rescale video."""
        super().resizeEvent(event)
        if self._original_pixmap and not self._original_pixmap.isNull():
            self._scale_pixmap_to_fit()
    
    def _scale_pixmap_to_fit(self) -> None:
        """Scale the pixmap to fit the label size while maintaining aspect ratio."""
        if not self._original_pixmap or self._original_pixmap.isNull():
            return
        
        label_size = self.size()
        pixmap_size = self._original_pixmap.size()
        
        if label_size.width() <= 0 or label_size.height() <= 0:
            return
        
        if pixmap_size.width() <= 0 or pixmap_size.height() <= 0:
            return
        
        # Scale the pixmap to fit label size while maintaining aspect ratio
        scaled_pixmap = self._original_pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)

    def clear_drawing(self) -> None:
        """Clear all drawings."""
        # Record undo action
        if hasattr(self, 'undo_redo_manager') and self.lines:
            old_lines = self.lines.copy()
            
            def undo_func():
                self.lines = old_lines.copy()
                self._update_display()
            
            def redo_func():
                self.lines = []
                self._update_display()
            
            from core.drawing_undo_redo import DrawingAction
            action = DrawingAction(
                action_type="clear_all",
                canvas_id=self.title.lower().replace(" ", "_"),
                data={"old_lines": old_lines},
                undo_func=undo_func,
                redo_func=redo_func
            )
            self.undo_redo_manager.push_action(action)
        
        self.lines = []
        self.current_line_start = None
        self._current_line_end = None
        self.selected_line_index = None
        self._update_display()

    def set_drawing_color(self, color: QColor) -> None:
        """Set drawing color for new lines."""
        self.drawing_color = color
        self._update_display()

    def set_drawing_width(self, width: int) -> None:
        """Set drawing line width for new lines."""
        self.drawing_width = width
        self._update_display()

    def set_overlay_text(self, text: str | None) -> None:
        """Set overlay text rendered on top of the canvas."""
        self.overlay_text = text or ""
        self._update_display()
    
    def set_shot_data_overlay(self, enabled: bool, shot_data: dict | None = None) -> None:
        """Enable/disable shot data overlay and set data."""
        self.show_shot_data_overlay = enabled
        if shot_data:
            self.shot_data_dict = shot_data
        self._update_display()
    
    def set_overlay_position(self, position: str) -> None:
        """Set overlay position: 'top-left', 'top-right', 'bottom-left', 'bottom-right'."""
        if position in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            self.overlay_position = position
            self._update_display()
    
    def set_overlay_metrics(self, metrics: list[str]) -> None:
        """Set which metrics to display in overlay."""
        self.overlay_metrics = metrics
        self._update_display()
    
    def set_overlay_style(self, style: dict) -> None:
        """Set overlay style (colors, font size, padding)."""
        if "background_color" in style:
            self.overlay_style["background_color"] = style["background_color"]
        if "text_color" in style:
            self.overlay_style["text_color"] = style["text_color"]
        if "font_size" in style:
            self.overlay_style["font_size"] = style["font_size"]
        if "padding" in style:
            self.overlay_style["padding"] = style["padding"]
        self._update_display()

    def change_line_color(self, line_index: int, color: QColor) -> None:
        """Change color of an existing line."""
        if 0 <= line_index < len(self.lines):
            x1, y1, x2, y2, _, width = self.lines[line_index]
            self.lines[line_index] = (x1, y1, x2, y2, color, width)
            self._update_display()


class PlaybackWorker(QThread):
    """Background worker for playback timing."""

    tick = pyqtSignal()
    diagnostics = pyqtSignal(float, float)

    def __init__(self, fps: float, playback_speed: float) -> None:
        super().__init__()
        self.fps = max(fps, 0.1)
        self.playback_speed = max(playback_speed, 0.01)
        self._play_event = threading.Event()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._interval_ms = self._calculate_interval()
        self._play_event.clear()  # Start paused

    def _calculate_interval(self) -> float:
        fps = max(self.fps, 0.1)
        speed = max(self.playback_speed, 0.01)
        return max(1.0, (1000.0 / fps) / speed)

    def set_speed(self, playback_speed: float) -> None:
        with self._lock:
            self.playback_speed = max(playback_speed, 0.01)
            self._interval_ms = self._calculate_interval()

    def start_playback(self) -> None:
        self._play_event.set()

    def pause_playback(self) -> None:
        self._play_event.clear()

    def stop_worker(self) -> None:
        self._stop_event.set()
        self._play_event.set()
        self.wait()

    def run(self) -> None:
        next_tick = time.perf_counter() * 1000.0
        last_tick = next_tick
        while not self._stop_event.is_set():
            if not self._play_event.is_set():
                time.sleep(0.005)
                baseline = time.perf_counter() * 1000.0
                next_tick = baseline
                last_tick = baseline
                continue

            with self._lock:
                interval = self._interval_ms

            now = time.perf_counter() * 1000.0
            if now >= next_tick:
                if self._play_event.is_set():
                    self.tick.emit()
                    actual_interval = now - last_tick
                    self.diagnostics.emit(interval, actual_interval)
                    last_tick = now
                    next_tick += interval

                    if now - next_tick > interval:
                        next_tick = now + interval
            else:
                sleep_seconds = max(0.001, (next_tick - now) / 1000.0)
                time.sleep(sleep_seconds)


class ShotReviewWindow(QWidget):
    """Side-by-side video player for shot review."""

    def __init__(
        self,
        dtl_video_path: Optional[Path],
        face_video_path: Optional[Path],
        shot_data: dict,
        parent: QWidget | None = None,
        shot_id: Optional[int] = None,
        session_manager=None,
    ) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.dtl_path = dtl_video_path
        self.face_path = face_video_path
        self.shot_data = shot_data
        self.shot_id = shot_id
        self.session_manager = session_manager
        self.current_tags: list[str] = []
        self.is_favorite = False
        self.shot_notes: str = ""
        self.dtl_cap: Optional[cv2.VideoCapture] = None
        self.face_cap: Optional[cv2.VideoCapture] = None
        self.current_frame = 0
        self.dtl_total_frames = 0
        self.face_total_frames = 0
        self.fps = 30
        self.playback_speed = 0.1  # Speed multiplier (default to super slow motion)
        self.playing = False
        self.playback_worker = PlaybackWorker(self.fps, self.playback_speed)
        self.playback_worker.tick.connect(self._on_worker_tick)
        self.playback_worker.diagnostics.connect(self._log_playback_diagnostics)
        self.playing = False
        self.playback_worker.pause_playback()
        self.playback_worker.start()
        
        # Impact zone auto-slowdown
        self.impact_zone_enabled = True
        self.impact_frame = None  # Will be calculated
        self.impact_zone_frames = 60  # 2 seconds at 30fps
        self.auto_slow_speed = 0.25  # Speed when in impact zone
        self.original_speed_before_zone = None
        
        # Note: Measurement tools and path tracers are now canvas-specific
        # Each VideoCanvas has its own instances to prevent cross-contamination
        
        # Video trimming
        self.trim_start_frame = 0
        self.trim_end_frame = None  # Will be set to max_frames
        self.trim_mode = False
        
        if isinstance(parent, QWidget) and not isinstance(parent, QDialog):
            self.setWindowTitle("Shot Review")
            self.setMinimumSize(1200, 700)
            self.resize(1400, 800)
        self.setStyleSheet(get_current_theme() + f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        self._load_shot_metadata()
        self._load_videos()
        self._build_ui()
        # Load saved measurements
        if self.shot_id and self.session_manager:
            if hasattr(self.dtl_canvas, 'measurement_tool'):
                self.dtl_canvas.measurement_tool.load_measurements(self.shot_id, self.session_manager)
            if hasattr(self.face_canvas, 'measurement_tool'):
                self.face_canvas.measurement_tool.load_measurements(self.shot_id, self.session_manager)
        self._setup_shortcuts()
        self._apply_multi_monitor_layout()
        # Initial playback diagnostics
        base_time_per_frame_ms = (1000.0 / self.fps) if self.fps > 0 else 33.0
        time_per_frame_ms = base_time_per_frame_ms / self.playback_speed
        logger.info(
            "Playback initialized: %.2f ms per frame (fps: %.1f, speed: %.2fx)",
            time_per_frame_ms,
            self.fps,
            self.playback_speed,
        )

    def _load_videos(self) -> None:
        """Load video files."""
        if self.dtl_path and self.dtl_path.exists():
            self.dtl_cap = cv2.VideoCapture(str(self.dtl_path))
            if self.dtl_cap.isOpened():
                self.dtl_total_frames = int(self.dtl_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.dtl_cap.get(cv2.CAP_PROP_FPS) or 30
                logger.debug("Loaded DTL video: %d frames, %.1f fps", self.dtl_total_frames, self.fps)
        
        if self.face_path and self.face_path.exists():
            self.face_cap = cv2.VideoCapture(str(self.face_path))
            if self.face_cap.isOpened():
                self.face_total_frames = int(self.face_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                logger.debug("Loaded face video: %d frames", self.face_total_frames)
        
        # Calculate impact frame (assume impact is at 75% of swing for now)
        # In a real implementation, this could be detected from video or shot data
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        if max_frames > 0:
            self.impact_frame = int(max_frames * 0.75)  # Approximate impact at 75%
            self.trim_end_frame = max_frames - 1
        
        # Update timeline markers after loading videos
        self._update_timeline_markers()

    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        # Main horizontal splitter: Sidebar | Video Area (resizable)
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(SPACING.XS)
        main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        # VERTICAL SIDEBAR - Tools (left edge) - expandable
        sidebar = QWidget()
        sidebar.setMinimumWidth(200)  # Increased to prevent label cutoff
        sidebar.setMaximumWidth(250)  # Match main sidebar maximum width
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable area for sidebar tools to prevent overflow
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sidebar_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        
        # Use QListWidget like main sidebar for better text handling
        self.tool_list = QListWidget()
        self.tool_list.setSpacing(SPACING.XS)
        self.tool_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                margin: {SPACING.XS}px {SPACING.XS}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
                min-height: 28px;
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
            }}
        """)
        
        icon_font = QFont()
        icon_font.setPointSize(12)
        
        # Slightly larger font for drawing tools (but not too big)
        drawing_tool_font = QFont()
        drawing_tool_font.setPointSize(13)
        drawing_tool_font.setWeight(QFont.Weight.Medium)
        
        # Tool items organized by category with separators
        # Drawing tools
        drawing_tools = [
            ("✎", "Freehand Draw", "Draw freehand lines (D)", "freehand"),
            ("╱", "Swing Plane", "Draw swing plane line (P)", "swing_plane"),
            ("┃", "Reference Line", "Draw reference line (R)", "reference"),
            ("☑", "Select Line", "Select and edit lines (E)", "select"),
        ]
        
        # Measurement tools
        measurement_tools = [
            ("📏", "Measure Distance", "Measure distance between points (M)", "distance"),
            ("∠", "Measure Angle", "Measure angle between lines", "angle"),
            ("⌇", "Trace Path", "Trace swing path", "path"),
        ]
        
        # Editing tools
        editing_tools = [
            ("✕", "Clear All", "Clear all drawings and measurements (C)", "clear"),
        ]
        
        # Video controls
        video_tools = [
            ("📊", "Toggle Overlay", "Show/hide data overlay", "overlay"),
            ("⚙", "Overlay Settings", "Configure overlay display", "settings"),
            ("⏱", "Auto-Slowdown", "Auto-slow at impact zone", "autoslow"),
            ("✂", "Trim Video", "Trim video start/end", "trim"),
        ]
        
        self.tool_items_map = {}
        
        def add_tool_group(tools, add_separator_after=False, use_drawing_font=False):
            """Add a group of tools to the list."""
            for icon, label, tooltip, tool_id in tools:
                item = QListWidgetItem(f"{icon} {label}")
                # Use larger font for drawing tools
                if use_drawing_font:
                    item.setFont(drawing_tool_font)
                else:
                    item.setFont(icon_font)
                item.setToolTip(tooltip)
                item.setData(Qt.ItemDataRole.UserRole, tool_id)
                self.tool_list.addItem(item)
                self.tool_items_map[tool_id] = item
            if add_separator_after:
                # Add a visual separator using a custom widget
                separator_widget = QWidget()
                separator_widget.setFixedHeight(1)
                separator_widget.setStyleSheet(f"background-color: {current_colors.BORDER_DEFAULT};")
                separator_item = QListWidgetItem()
                separator_item.setSizeHint(QSize(0, SPACING.SMALL))
                separator_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
                self.tool_list.addItem(separator_item)
                self.tool_list.setItemWidget(separator_item, separator_widget)
        
        # Add tool groups with separators
        add_tool_group(drawing_tools, add_separator_after=True, use_drawing_font=True)
        add_tool_group(measurement_tools, add_separator_after=True)
        add_tool_group(editing_tools, add_separator_after=True)
        add_tool_group(video_tools, add_separator_after=False)
        
        # Use accent color as default drawing color
        accent_color_hex = current_colors.ACCENT.lstrip('#')
        self.current_color = QColor(int(accent_color_hex[0:2], 16), 
                                    int(accent_color_hex[2:4], 16), 
                                    int(accent_color_hex[4:6], 16))
        self._update_color_item()
        # Update color preview if panel exists
        if hasattr(self, "color_preview_btn"):
            self._update_color_preview()
        
        def on_tool_clicked(item: QListWidgetItem) -> None:
            tool_id = item.data(Qt.ItemDataRole.UserRole)
            if not tool_id:  # Skip items without tool_id (separators, labels, widgets)
                return
            
            # Don't update selection for action tools (they don't stay selected)
            action_tools = ["color", "clear", "overlay", "settings", "autoslow", "trim", "path"]
            
            if tool_id == "freehand":
                self._select_tool("freehand")
            elif tool_id == "swing_plane":
                self._select_tool("swing_plane")
            elif tool_id == "reference":
                self._select_tool("reference")
            elif tool_id == "select":
                self._select_tool("select")
            elif tool_id == "distance":
                self._select_measurement_tool("distance")
            elif tool_id == "angle":
                self._select_measurement_tool("angle")
            elif tool_id == "path":
                self._toggle_path_tracing()
            elif tool_id == "color":
                self._pick_color()
            elif tool_id == "clear":
                self._clear_drawings()
            elif tool_id == "overlay":
                self._toggle_overlay()
            elif tool_id == "settings":
                self._open_overlay_settings()
            elif tool_id == "autoslow":
                self._toggle_impact_zone()
            elif tool_id == "trim":
                self._open_trim_dialog()
            
            # Update selection only for tools that should stay selected
            if tool_id not in action_tools:
                self.tool_list.setCurrentItem(item)
        
        self.tool_list.itemClicked.connect(on_tool_clicked)
        
        # Tool properties panel - only visible when drawing tool is selected
        self.tool_properties_panel = QWidget()
        self.tool_properties_panel.setVisible(False)  # Hidden by default
        tool_props_layout = QVBoxLayout(self.tool_properties_panel)
        tool_props_layout.setSpacing(SPACING.SMALL)
        tool_props_layout.setContentsMargins(SPACING.SMALL, SPACING.SMALL, SPACING.SMALL, SPACING.SMALL)
        
        # Width control - moved here to avoid cutting off buttons
        width_label = QLabel("Line Width")
        width_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: {TYPOGRAPHY.BOLD};")
        tool_props_layout.addWidget(width_label)
        
        self.width_combo = QComboBox()
        self.width_combo.addItems(["1", "2", "3", "4", "5"])
        self.width_combo.setCurrentText("3")
        self.width_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
                min-height: 32px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_HOVER};
            }}
        """)
        self.width_combo.currentTextChanged.connect(self._change_line_width)
        tool_props_layout.addWidget(self.width_combo)
        
        # Color control
        color_label = QLabel("Drawing Color")
        color_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: {TYPOGRAPHY.BOLD};")
        tool_props_layout.addWidget(color_label)
        
        self.color_preview_btn = QPushButton()
        self.color_preview_btn.setFixedSize(40, 32)
        # Will be updated after color is set
        self.color_preview_btn.clicked.connect(self._pick_color)
        self.color_preview_btn.setToolTip("Click to change drawing color")
        tool_props_layout.addWidget(self.color_preview_btn)
        
        sidebar_layout.addWidget(self.tool_list, 1)
        sidebar_layout.addWidget(self.tool_properties_panel, 0)
        
        # Add sidebar to splitter
        main_splitter.addWidget(sidebar)
        
        # RIGHT SIDE: Video area with top bar and controls
        right_side = QWidget()
        right_side_layout = QVBoxLayout(right_side)
        right_side_layout.setSpacing(0)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar - minimal header
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; border-bottom: 1px solid {current_colors.BORDER_DEFAULT};")
        top_bar.setFixedHeight(32)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(SPACING.SMALL, SPACING.XS, SPACING.SMALL, SPACING.XS)
        top_layout.setSpacing(SPACING.SMALL)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Shot info - formatted with bold numbers and smaller gray labels
        club_speed = self.shot_data.get('ClubSpeed', '--')
        ball_speed = self.shot_data.get('BallSpeed', '--')
        total_spin = self.shot_data.get('TotalSpin', '--')
        
        shot_info_html = f"""
            <span style="color: {current_colors.TEXT_PRIMARY}; font-weight: {TYPOGRAPHY.BOLD}; font-size: {TYPOGRAPHY.SMALL}px;">{club_speed}</span>
            <span style="color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px;"> mph</span>
            <span style="color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px;"> | </span>
            <span style="color: {current_colors.TEXT_PRIMARY}; font-weight: {TYPOGRAPHY.BOLD}; font-size: {TYPOGRAPHY.SMALL}px;">{ball_speed}</span>
            <span style="color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px;"> mph</span>
            <span style="color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px;"> | </span>
            <span style="color: {current_colors.TEXT_PRIMARY}; font-weight: {TYPOGRAPHY.BOLD}; font-size: {TYPOGRAPHY.SMALL}px;">{total_spin}</span>
            <span style="color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px;"> rpm</span>
        """
        shot_info = QLabel()
        shot_info.setTextFormat(Qt.TextFormat.RichText)
        shot_info.setText(shot_info_html)
        top_layout.addWidget(shot_info)
        
        top_layout.addStretch()
        
        # Action buttons - icon-only to match top bar height (30-35px)
        if self.shot_id and self.session_manager:
            # Icon-only button style for top bar
            # Monochrome icon buttons (gray by default, colored on hover)
            icon_btn_style = f"""
                QPushButton {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    border: 1px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    color: {current_colors.TEXT_SECONDARY};
                    font-size: {TYPOGRAPHY.SMALL}px;
                    min-width: 28px;
                    min-height: 28px;
                    max-width: 28px;
                    max-height: 28px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                    border-color: {current_colors.BORDER_HOVER};
                    color: {current_colors.TEXT_PRIMARY};
                }}
            """
            
            # Export button - keep colored as primary action
            primary_icon_btn_style = f"""
                QPushButton {{
                    background-color: {current_colors.ACCENT};
                    border: 1px solid {current_colors.ACCENT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    color: {current_colors.WHITE_TEXT};
                    font-size: {TYPOGRAPHY.SMALL}px;
                    min-width: 28px;
                    min-height: 28px;
                    max-width: 28px;
                    max-height: 28px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {current_colors.ACCENT_HOVER};
                    border-color: {current_colors.ACCENT_HOVER};
                }}
            """
            
            self.favorite_btn = QPushButton("★")
            self.favorite_btn.setCheckable(True)
            self.favorite_btn.setChecked(self.is_favorite)
            self.favorite_btn.setToolTip("Favorite (F)")
            self.favorite_btn.setFixedSize(28, 28)
            self.favorite_btn.setStyleSheet(icon_btn_style + f"""
                QPushButton:checked {{
                    background-color: {current_colors.ACCENT};
                    border-color: {current_colors.ACCENT};
                    color: {current_colors.WHITE_TEXT};
                }}
            """)
            self._update_favorite_button()
            self.favorite_btn.clicked.connect(self._toggle_favorite)
            top_layout.addWidget(self.favorite_btn)
            
            edit_tags_btn = QPushButton("🏷")
            edit_tags_btn.setToolTip("Edit Tags (T)")
            edit_tags_btn.setStyleSheet(icon_btn_style)
            edit_tags_btn.clicked.connect(self._edit_tags)
            top_layout.addWidget(edit_tags_btn)
            
            edit_notes_btn = QPushButton("📝")
            edit_notes_btn.setToolTip("Edit Notes (N)")
            edit_notes_btn.setStyleSheet(icon_btn_style)
            edit_notes_btn.clicked.connect(self._edit_notes)
            top_layout.addWidget(edit_notes_btn)
            
            export_btn = QPushButton("⬇")
            export_btn.setToolTip("Export Video")
            export_btn.setStyleSheet(primary_icon_btn_style)
            export_btn.clicked.connect(self._export_video)
            top_layout.addWidget(export_btn)
            
            # Save measurements button
            save_measurements_btn = QPushButton("💾")
            save_measurements_btn.setToolTip("Save Measurements (Ctrl+S)")
            save_measurements_btn.setStyleSheet(icon_btn_style)
            save_measurements_btn.clicked.connect(self._save_measurements)
            top_layout.addWidget(save_measurements_btn)
        
        right_side_layout.addWidget(top_bar)

        # Video area - maximized

        # Video panels side-by-side with resizable splitter and scroll areas
        video_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        video_splitter.setChildrenCollapsible(False)  # Prevent panels from being completely hidden
        video_splitter.setHandleWidth(4)
        video_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)

        self.dtl_canvas = VideoCanvas("Down the Line")
        self.face_canvas = VideoCanvas("Face On")
        self.dtl_canvas.parent_window = self
        self.face_canvas.parent_window = self
        self._set_overlay_text("Ready")
        
        dtl_scroll = QScrollArea()
        dtl_scroll.setWidget(self.dtl_canvas)
        dtl_scroll.setWidgetResizable(True)
        dtl_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        dtl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dtl_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dtl_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {current_colors.BACKGROUND_BASE};
                border: none;
                padding: {SPACING.XS}px;
            }}
            QScrollBar:vertical, QScrollBar:horizontal {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                width: 12px;
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-height: {SPACING.MEDIUM + SPACING.XS}px;
                min-width: {SPACING.MEDIUM + SPACING.XS}px;
            }}
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        dtl_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        face_scroll = QScrollArea()
        face_scroll.setWidget(self.face_canvas)
        face_scroll.setWidgetResizable(True)
        face_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        face_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        face_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        face_scroll.setStyleSheet(dtl_scroll.styleSheet())
        face_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.dtl_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.face_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        video_splitter.addWidget(dtl_scroll)
        video_splitter.addWidget(face_scroll)
        video_splitter.setStretchFactor(0, 1)
        video_splitter.setStretchFactor(1, 1)
        
        video_splitter.setSizes([500, 500])
        
        right_side_layout.addWidget(video_splitter, 1)

        # Bottom playback controls - centered and ergonomic
        controls = QWidget()
        controls.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; border-top: 1px solid {current_colors.BORDER_DEFAULT};")
        controls.setFixedHeight(48)  # More space for larger buttons
        controls.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(SPACING.SMALL)
        controls_layout.setContentsMargins(SPACING.SMALL, SPACING.XS, SPACING.SMALL, SPACING.XS)

        # Timeline scrubber with preview
        from app.widgets.marked_slider import MarkedSlider
        self.progress_slider = MarkedSlider(Qt.Orientation.Horizontal)
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(max(0, max_frames - 1))
        self.progress_slider.valueChanged.connect(self._seek_to_frame)
        self._slider_updating = False
        self._update_timeline_markers()
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {current_colors.BORDER_DEFAULT};
                height: 3px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {current_colors.ACCENT};
                border-radius: 2px;
                height: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {current_colors.ACCENT};
                width: 10px;
                height: 10px;
                margin: -3.5px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {current_colors.ACCENT_HOVER};
            }}
        """)
        self.progress_slider.setPageStep(1)
        
        # Enable tooltip for frame preview on hover
        self.progress_slider.setToolTip("Frame: 0")
        self.progress_slider.installEventFilter(self)
        
        # Frame info - minimal, on the left
        self.frame_label = QLabel("0/0")
        self.frame_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px {SPACING.SMALL}px;")
        self.frame_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        controls_layout.addWidget(self.frame_label)
        
        controls_layout.addWidget(self.progress_slider, 1)  # Stretch slider in center
        
        # Centered transport controls
        transport_container = QWidget()
        transport_layout = QHBoxLayout(transport_container)
        transport_layout.setSpacing(SPACING.XS)
        transport_layout.setContentsMargins(SPACING.SMALL, 0, SPACING.SMALL, 0)
        
        # Larger, more prominent play/pause button - starts in paused state
        self.play_btn = QPushButton("▶")
        self.play_btn.setToolTip("Play/Pause (Space)")
        self.play_btn.clicked.connect(self._toggle_play)
        # Ensure button shows play icon (not paused) initially
        self.play_btn.setText("▶")
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.ACCENT};
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                color: {current_colors.WHITE_TEXT};
                font-size: {TYPOGRAPHY.H3}px;
                min-width: 40px;
                min-height: 40px;
                max-width: 40px;
                max-height: 40px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        transport_layout.addWidget(self.play_btn)
        
        # Speed dropdown - next to play button
        speed_combo = QComboBox()
        speed_combo.addItems(["0.1x", "0.25x", "0.5x", "1x", "2x", "4x"])
        speed_combo.setCurrentText("0.1x")
        speed_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                min-height: 32px;
                max-width: 60px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_HOVER};
            }}
        """)
        speed_combo.currentTextChanged.connect(self._change_speed)
        transport_layout.addWidget(speed_combo)
        
        controls_layout.addWidget(transport_container, 0)  # Center the transport controls
        
        right_side_layout.addWidget(controls, 0)
        
        # Add right side to splitter
        main_splitter.addWidget(right_side)
        main_splitter.setStretchFactor(0, 0)  # Sidebar doesn't stretch
        main_splitter.setStretchFactor(1, 1)  # Video area stretches
        main_splitter.setSizes([64, 800])  # Initial sizes: compact sidebar, larger video area
        
        # Set splitter as the main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_splitter)

        self._update_frames()
        self._update_playback_status(state="ready")
    
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for playback and actions."""
        # Playback controls
        QShortcut(QKeySequence("Space"), self, self._toggle_play)
        QShortcut(QKeySequence("S"), self, self._stop)
        QShortcut(QKeySequence("Left"), self, self._rewind)
        QShortcut(QKeySequence("Right"), self, self._fast_forward)
        QShortcut(QKeySequence("Ctrl+Left"), self, lambda: self._seek_frame(-30))
        QShortcut(QKeySequence("Ctrl+Right"), self, lambda: self._seek_frame(30))
        # Frame-by-frame navigation
        QShortcut(QKeySequence("Shift+Left"), self, lambda: self._step_frame(-1))
        QShortcut(QKeySequence("Shift+Right"), self, lambda: self._step_frame(1))
        QShortcut(QKeySequence("Up"), self, lambda: self._step_frame(-1))
        QShortcut(QKeySequence("Down"), self, lambda: self._step_frame(1))
        
        # Speed controls
        QShortcut(QKeySequence("1"), self, lambda: self._change_speed("0.1x"))
        QShortcut(QKeySequence("2"), self, lambda: self._change_speed("0.25x"))
        QShortcut(QKeySequence("3"), self, lambda: self._change_speed("0.5x"))
        QShortcut(QKeySequence("4"), self, lambda: self._change_speed("1x"))
        QShortcut(QKeySequence("5"), self, lambda: self._change_speed("2x"))
        QShortcut(QKeySequence("6"), self, lambda: self._change_speed("4x"))
        
        # Shot metadata (if available)
        if self.shot_id and self.session_manager:
            QShortcut(QKeySequence("F"), self, self._toggle_favorite)
            QShortcut(QKeySequence("T"), self, self._edit_tags)
            QShortcut(QKeySequence("N"), self, self._edit_notes)
            QShortcut(QKeySequence("Ctrl+S"), self, self._save_measurements)
        
        # Undo/Redo shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_drawing)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._redo_drawing)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo_drawing)
        
        # Drawing tools
        QShortcut(QKeySequence("D"), self, lambda: self._select_tool("freehand"))
        QShortcut(QKeySequence("P"), self, lambda: self._select_tool("swing_plane"))
        QShortcut(QKeySequence("R"), self, lambda: self._select_tool("reference"))
        QShortcut(QKeySequence("E"), self, lambda: self._select_tool("select"))
        QShortcut(QKeySequence("C"), self, self._clear_drawings)
        QShortcut(QKeySequence("Ctrl+C"), self, self._pick_color)
        
        # Measurement tools
        QShortcut(QKeySequence("M"), self, lambda: self._select_measurement_tool("distance"))
        QShortcut(QKeySequence("G"), self, self._goto_frame_dialog)
        
        # Frame navigation
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        QShortcut(QKeySequence("Home"), self, lambda: self._seek_to_frame(0))
        QShortcut(QKeySequence("End"), self, lambda: self._seek_to_frame(max_frames - 1) if max_frames > 0 else None)
    
    def _apply_multi_monitor_layout(self) -> None:
        """Apply optimal multi-monitor layout."""
        try:
            from core.multi_monitor import get_optimal_window_rect, detect_monitors
            
            # Only apply if parent is not a QDialog (dialogs handle their own sizing)
            if isinstance(self.parent(), QWidget) and not isinstance(self.parent(), QDialog):
                layouts = detect_monitors()
                if layouts and layouts[0].has_secondary():
                    # Use secondary monitor for review window if available
                    rect = get_optimal_window_rect(self, "review", 1)
                    self.setGeometry(rect)
                else:
                    # Use primary monitor
                    rect = get_optimal_window_rect(self, "review", 0)
                    self.setGeometry(rect)
        except Exception as e:
            logger.debug("Error applying multi-monitor layout: %s", e)
    
    def _seek_frame(self, offset: int) -> None:
        """Seek forward or backward by specified number of frames."""
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        self.current_frame = max(0, min(max_frames - 1, self.current_frame + offset))
        self._update_frames()
    
    def _step_frame(self, direction: int) -> None:
        """Step forward or backward by one frame (for precise navigation)."""
        # Pause playback if playing
        was_playing = self.playing
        if was_playing:
            self.playback_worker.pause_playback()
            self.playing = False
            self.play_btn.setText("▶")
        
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        self.current_frame = max(0, min(max_frames - 1, self.current_frame + direction))
        self._update_frames()
        self._update_playback_status(state="scrub")

    def _select_tool(self, tool: str) -> None:
        """Select drawing tool."""
        # Update list selection if using QListWidget
        if hasattr(self, "tool_items_map") and hasattr(self, "tool_list"):
            # Clear previous selection for drawing tools
            drawing_tool_ids = ["freehand", "swing_plane", "reference", "select"]
            for tool_id in drawing_tool_ids:
                if tool_id in self.tool_items_map:
                    item = self.tool_items_map[tool_id]
                    if item.listWidget():
                        item.listWidget().setCurrentItem(None)
            
            # Set new selection
            if tool in self.tool_items_map:
                item = self.tool_items_map[tool]
                if item.listWidget():
                    item.listWidget().setCurrentItem(item)
        
        # Set drawing mode
        drawing_tools = ["freehand", "swing_plane", "reference", "select"]
        if tool in drawing_tools:
            if tool == "freehand":
                self.dtl_canvas.drawing_mode = "freehand"
                self.face_canvas.drawing_mode = "freehand"
            elif tool == "swing_plane":
                self.dtl_canvas.drawing_mode = "swing_plane"
                self.face_canvas.drawing_mode = "swing_plane"
            elif tool == "reference":
                self.dtl_canvas.drawing_mode = "reference"
                self.face_canvas.drawing_mode = "reference"
            elif tool == "select":
                self.dtl_canvas.drawing_mode = "select"
                self.face_canvas.drawing_mode = "select"
            # Show tool properties panel when drawing tool is selected
            if hasattr(self, "tool_properties_panel"):
                self.tool_properties_panel.setVisible(True)
        else:
            self.dtl_canvas.drawing_mode = None
            self.face_canvas.drawing_mode = None
            # Hide tool properties panel when no drawing tool is selected
            if hasattr(self, "tool_properties_panel"):
                self.tool_properties_panel.setVisible(False)
        
        self.dtl_canvas.set_drawing_color(self.current_color)
        self.face_canvas.set_drawing_color(self.current_color)

    def _change_line_color(self, canvas: VideoCanvas, line_index: int) -> None:
        """Change selected line color."""
        if line_index is None or line_index >= len(canvas.lines):
            return
        
        _, _, _, _, current_color, _ = canvas.lines[line_index]
        color = QColorDialog.getColor(current_color, self, "Select Line Color")
        if color.isValid():
            canvas.change_line_color(line_index, color)
            self._set_current_color(color)

    def _pick_color(self) -> None:
        """Open color picker."""
        color = QColorDialog.getColor(self.current_color, self, "Select Drawing Color")
        if color.isValid():
            self._set_current_color(color)

    def _set_current_color(self, color: QColor) -> None:
        """Set current color."""
        self.current_color = color
        self._update_color_button()
        self.dtl_canvas.set_drawing_color(color)
        self.face_canvas.set_drawing_color(color)

    def _update_color_item(self) -> None:
        """Update color item display to show current color."""
        if hasattr(self, "tool_items_map") and "color" in self.tool_items_map:
            color = self.current_color
            color_item = self.tool_items_map["color"]
            # Update icon color by setting text color
            color_item.setForeground(QColor(color))
    
    def _update_color_preview(self) -> None:
        """Update color preview button in tool properties panel."""
        if not hasattr(self, "color_preview_btn"):
            return
        from app.design_constants import get_current_colors, SIZES
        current_colors = get_current_colors()
        color = self.current_color
        self.color_preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QPushButton:hover {{
                border-color: {current_colors.BORDER_HOVER};
            }}
        """)
    
    def _update_color_button(self) -> None:
        """Legacy method - redirects to _update_color_item."""
        self._update_color_item()
        self._update_color_preview()

    def _set_overlay_text(self, text: str) -> None:
        """Set overlay text on both canvases."""
        self.dtl_canvas.set_overlay_text(text)
        self.face_canvas.set_overlay_text(text)

    def _change_line_width(self, width_text: str) -> None:
        """Change line width."""
        width = int(width_text)
        self.dtl_canvas.set_drawing_width(width)
        self.face_canvas.set_drawing_width(width)

    def _clear_drawings(self) -> None:
        """Clear all drawings, measurements, and path traces from both canvases."""
        # Clear DTL canvas
        self.dtl_canvas.clear_drawing()
        self.dtl_canvas.measurement_tool.clear_all()
        self.dtl_canvas.path_tracer.clear_path()
        self.dtl_canvas._update_display()
        
        # Clear Face On canvas
        self.face_canvas.clear_drawing()
        self.face_canvas.measurement_tool.clear_all()
        self.face_canvas.path_tracer.clear_path()
        self.face_canvas._update_display()
    
    def _undo_drawing(self) -> None:
        """Undo last drawing operation."""
        # Try DTL canvas first
        if hasattr(self.dtl_canvas, 'undo_redo_manager'):
            action = self.dtl_canvas.undo_redo_manager.undo()
            if action:
                return
        
        # Try Face canvas
        if hasattr(self.face_canvas, 'undo_redo_manager'):
            action = self.face_canvas.undo_redo_manager.undo()
            if action:
                return
    
    def _redo_drawing(self) -> None:
        """Redo last undone drawing operation."""
        # Try DTL canvas first
        if hasattr(self.dtl_canvas, 'undo_redo_manager'):
            action = self.dtl_canvas.undo_redo_manager.redo()
            if action:
                return
        
        # Try Face canvas
        if hasattr(self.face_canvas, 'undo_redo_manager'):
            action = self.face_canvas.undo_redo_manager.redo()
            if action:
                return

    def _change_speed(self, speed_text: str) -> None:
        """Change playback speed."""
        speed_map = {"0.1x": 0.1, "0.25x": 0.25, "0.5x": 0.5, "1x": 1.0, "2x": 2.0, "4x": 4.0}
        new_speed = speed_map.get(speed_text, 1.0)
        
        if new_speed == self.playback_speed:
            return
        
        was_playing = self.playing
        self.playback_speed = new_speed
        
        if was_playing:
            self.playback_worker.pause_playback()
            self.playback_worker.set_speed(self.playback_speed)
            self.playback_worker.start_playback()
        else:
            self.playback_worker.set_speed(self.playback_speed)
        
        base_time_per_frame_ms = (1000.0 / self.fps) if self.fps > 0 else 33.0
        time_per_frame_ms = base_time_per_frame_ms / self.playback_speed
        logger.debug("Speed changed to %.2fx (%.2f ms per frame)", self.playback_speed, time_per_frame_ms)


    def _rewind(self) -> None:
        """Rewind 10 frames."""
        self.current_frame = max(0, self.current_frame - 10)
        self._update_frames()

    def _fast_forward(self) -> None:
        """Forward 10 frames."""
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        self.current_frame = min(max_frames - 1, self.current_frame + 10)
        self._update_frames()

    def _toggle_play(self) -> None:
        """Toggle play/pause."""
        if not self.dtl_cap and not self.face_cap:
            logger.warning("Cannot play: no video loaded")
            return
        
        self.playing = not self.playing
        if self.playing:
            self.play_btn.setText("⏸")
            self.playback_worker.set_speed(self.playback_speed)
            self.playback_worker.start_playback()
            self._update_playback_status(state="playing")
        else:
            self.play_btn.setText("▶")
            self.playback_worker.pause_playback()
            self._update_playback_status(state="paused")

    def _stop(self) -> None:
        """Stop playback and reset."""
        self.playing = False
        self.play_btn.setText("▶")  # Play icon
        self.playback_worker.pause_playback()
        self.current_frame = 0
        self._update_frames()
        self._update_playback_status(state="stopped")

    def _on_worker_tick(self) -> None:
        """Handle playback tick."""
        if not self.playing:
            if hasattr(self.playback_worker, '_play_event') and self.playback_worker._play_event.is_set():
                self.playback_worker.pause_playback()
            return
        self._next_frame()

    def _log_playback_diagnostics(self, target_interval_ms: float, actual_interval_ms: float) -> None:
        """Log playback timing."""
        if not self.playing:
            return
        self._update_playback_status(target_interval_ms, actual_interval_ms)
        if self.current_frame % 30 == 0:
            logger.debug(
                "Playback timing: target=%.2f ms, actual=%.2f ms, frame=%d",
                target_interval_ms,
                actual_interval_ms,
                self.current_frame,
            )

    def _next_frame(self) -> None:
        """Advance to next frame."""
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        if self.current_frame >= max_frames - 1:
            self._stop()
            return
        
        # Impact zone auto-slowdown
        if self.impact_zone_enabled and self.impact_frame is not None:
            frames_before_impact = self.impact_frame - self.current_frame
            if 0 <= frames_before_impact <= self.impact_zone_frames:
                # In impact zone - use slower speed
                if self.playback_speed > self.auto_slow_speed:
                    if self.original_speed_before_zone is None:
                        self.original_speed_before_zone = self.playback_speed
                    self.playback_worker.set_speed(self.auto_slow_speed)
                    # Update UI to show we're in impact zone
                    if hasattr(self, 'impact_zone_btn'):
                        self.impact_zone_btn.setStyleSheet(
                            self.impact_zone_btn.styleSheet() + 
                            f"background-color: {self.impact_zone_btn.palette().color(self.impact_zone_btn.backgroundRole()).name()};"
                        )
            elif frames_before_impact > self.impact_zone_frames:
                # Before impact zone - restore original speed
                if self.original_speed_before_zone is not None:
                    self.playback_worker.set_speed(self.original_speed_before_zone)
                    self.original_speed_before_zone = None
            else:
                # Past impact zone - restore original speed
                if self.original_speed_before_zone is not None:
                    self.playback_worker.set_speed(self.original_speed_before_zone)
                    self.original_speed_before_zone = None
        
        self.current_frame += 1
        self._update_frames()

    def _seek_to_frame(self, frame: int) -> None:
        """Seek to frame."""
        if self._slider_updating:
            return
        was_playing = self.playing
        if was_playing:
            self.playback_worker.pause_playback()
        self.current_frame = frame
        self._update_frames()
        if was_playing:
            self.playback_worker.start_playback()
        else:
            self._update_playback_status(state="scrub")

    def _update_playback_status(
        self,
        target_interval_ms: float | None = None,
        actual_interval_ms: float | None = None,
        state: str | None = None,
    ) -> None:
        """Update playback status label."""
        from app.design_constants import get_current_colors, TYPOGRAPHY, SPACING
        current_colors = get_current_colors()
        
        if not hasattr(self, "playback_status") or self.playback_status is None:
            return

        if state is not None:
            mapping = {
                "ready": "Timing: ready",
                "playing": "Timing: syncing…",
                "paused": "Timing: paused",
                "stopped": "Timing: stopped",
                "scrub": "Timing: scrubbing",
            }
            self.playback_status.setStyleSheet(f"color: {current_colors.BORDER_ICON}; font-size: {TYPOGRAPHY.BODY}px; padding-left: {SPACING.XS}px;")
            self.playback_status.setText(mapping.get(state, f"Timing: {state}"))
            overlay_map = {
                "ready": "Ready",
                "paused": "Paused",
                "stopped": "Stopped",
                "scrub": "Scrubbing",
            }
            if state in overlay_map:
                self._set_overlay_text(overlay_map[state])
            elif state == "playing":
                # keep overlay driven by diagnostics
                self._set_overlay_text("Syncing…")
            return

        if target_interval_ms is None or actual_interval_ms is None:
            return

        delta = abs(actual_interval_ms - target_interval_ms)
        within_tolerance = delta <= max(1.0, target_interval_ms * 0.1)
        from app.design_constants import TYPOGRAPHY, SPACING, get_current_colors
        current_colors = get_current_colors()
        color = current_colors.SUCCESS if within_tolerance else current_colors.DANGER_TEXT
        self.playback_status.setStyleSheet(f"color: {color}; font-size: {TYPOGRAPHY.BODY}px; padding-left: {SPACING.XS}px;")
        self.playback_status.setText(
            f"Timing: target {target_interval_ms:.2f} ms • actual {actual_interval_ms:.2f} ms"
        )
        if target_interval_ms > 0 and actual_interval_ms > 0:
            target_fps = 1000.0 / target_interval_ms
            actual_fps = 1000.0 / actual_interval_ms
            self._set_overlay_text(f"{actual_fps:.1f} fps • target {target_fps:.1f}")

    def _update_frames(self) -> None:
        """Update displayed frames for both videos."""
        if self.dtl_cap and self.dtl_cap.isOpened() and self.dtl_total_frames > 0:
            frame_num = min(self.current_frame, self.dtl_total_frames - 1)
            self.dtl_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.dtl_cap.read()
            if ret:
                self.dtl_canvas.set_frame(frame)
            else:
                logger.debug("Failed to read DTL frame %d", frame_num)
        
        if self.face_cap and self.face_cap.isOpened() and self.face_total_frames > 0:
            frame_num = min(self.current_frame, self.face_total_frames - 1)
            self.face_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.face_cap.read()
            if ret:
                self.face_canvas.set_frame(frame)
            else:
                logger.debug("Failed to read face frame %d", frame_num)
        
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        self._slider_updating = True
        self.progress_slider.setValue(self.current_frame)
        self._slider_updating = False
        # Get current speed text from playback_speed
        speed_map = {0.1: "0.1x", 0.25: "0.25x", 0.5: "0.5x", 1.0: "1x", 2.0: "2x", 4.0: "4x"}
        speed_text = speed_map.get(self.playback_speed, f"{self.playback_speed:.2f}x")
        
        # Show impact zone indicator if in impact zone
        impact_indicator = ""
        if self.impact_zone_enabled and self.impact_frame is not None:
            frames_before_impact = self.impact_frame - self.current_frame
            if 0 <= frames_before_impact <= self.impact_zone_frames:
                impact_indicator = " • Impact Zone"
        
        self.frame_label.setText(f"Frame: {self.current_frame + 1} / {max_frames} • {speed_text}{impact_indicator}")
    
    def _update_timeline_markers(self) -> None:
        """Update timeline markers for key moments."""
        from app.widgets.marked_slider import MarkedSlider
        if not hasattr(self, "progress_slider") or not isinstance(self.progress_slider, MarkedSlider):
            return
        
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        if max_frames == 0:
            self.progress_slider.set_markers([])
            return
        
        # Add markers at key positions: start, 25%, 50%, 75%, end
        markers = [
            0,
            max_frames // 4,
            max_frames // 2,
            (max_frames * 3) // 4,
            max_frames - 1,
        ]
        # Remove duplicates and ensure they're within range
        markers = sorted(set([m for m in markers if 0 <= m < max_frames]))
        self.progress_slider.set_markers(markers)

    def _load_shot_metadata(self) -> None:
        """Load shot tags and favorite status from database."""
        if not self.shot_id or not self.session_manager:
            return
        
        try:
            import json
            from sqlalchemy.orm import Session
            from core.session_manager import ShotModel
            
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, self.shot_id)
                if shot:
                    if shot.tags:
                        self.current_tags = json.loads(shot.tags)
                    else:
                        self.current_tags = []
                    self.is_favorite = shot.is_favorite
                    self.shot_notes = shot.notes or ""
        except Exception as e:
            logger.error("Error loading shot metadata: %s", e, exc_info=True)
    
    def _toggle_favorite(self) -> None:
        """Toggle favorite status."""
        if not self.shot_id or not self.session_manager:
            return
        
        self.is_favorite = self.favorite_btn.isChecked()
        if self.session_manager.update_shot(self.shot_id, is_favorite=self.is_favorite):
            self._update_favorite_button()
            logger.debug("Updated favorite status for shot %d: %s", self.shot_id, self.is_favorite)
    
    def _update_favorite_button(self) -> None:
        """Update favorite button appearance."""
        if not hasattr(self, "favorite_btn"):
            return
        # Button styling is handled by the stylesheet based on checked state
        # Just ensure the button reflects the current favorite state
        self.favorite_btn.setChecked(self.is_favorite)
    
    def _edit_tags(self) -> None:
        """Open dialog to edit tags."""
        if not self.shot_id or not self.session_manager:
            return
        
        from core.tag_manager import TagManager
        from pathlib import Path
        from app.widgets.tag_edit_dialog import TagEditDialog
        
        # Create tag manager
        tags_file = Path("data/tags.json")
        tag_manager = TagManager(tags_file, self.session_manager)
        
        # Show tag edit dialog
        dialog = TagEditDialog(tag_manager, self.current_tags, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_tags = dialog.get_tags()
            if self.session_manager.update_shot(self.shot_id, tags=new_tags):
                self.current_tags = new_tags
                self.tags_display.setText(", ".join(self.current_tags) if self.current_tags else "None")
                logger.debug("Updated tags for shot %d: %s", self.shot_id, new_tags)
    
    def _edit_notes(self) -> None:
        """Open dialog to edit shot notes."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        if not self.shot_id or not self.session_manager:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Shot Notes")
        dialog.setMinimumSize(500, 300)
        dialog.resize(600, 400)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        label = QLabel("Notes:")
        label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(label)
        
        notes_edit = QPlainTextEdit()
        notes_edit.setPlainText(self.shot_notes)
        notes_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
            }}
        """)
        layout.addWidget(notes_edit, 1)
        
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
                border-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        save_btn.clicked.connect(dialog.accept)
        buttons.addWidget(save_btn)
        
        # Custom fields
        from core.custom_fields import CustomFieldManager
        from pathlib import Path
        from app.widgets.custom_fields_form import CustomFieldsForm
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        
        fields_file = Path("data/custom_fields.json")
        field_manager = CustomFieldManager(fields_file)
        custom_fields_form = CustomFieldsForm(field_manager, "shots", dialog)
        layout.addWidget(custom_fields_form)
        
        # Load existing custom fields
        with Session(self.session_manager.engine) as session:
            shot = session.get(ShotModel, self.shot_id)
            if shot and shot.custom_fields:
                custom_fields_form.set_values(shot.custom_fields)
        
        layout.addLayout(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_notes = notes_edit.toPlainText().strip() or None
            # Get custom fields
            from core.custom_fields import set_custom_fields_to_json
            custom_fields_values = custom_fields_form.get_values()
            custom_fields_json = set_custom_fields_to_json(custom_fields_values)
            
            if self.session_manager.update_shot(self.shot_id, notes=new_notes, custom_fields=custom_fields_json):
                self.shot_notes = new_notes or ""
                logger.debug("Updated notes for shot %d", self.shot_id)
    
    def _export_video(self) -> None:
        """Export video with drawings and quality presets.
        
        Features:
        - Quality presets: High (95%), Medium (85%), Low (70%)
        - Automatic codec and scale selection
        - Format options: Side-by-Side, DTL Only, Face Only
        - Trimming support with frame range selection
        """
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        if not self.dtl_path and not self.face_path:
            QMessageBox.warning(self, "No Video", "No video files available to export.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Video")
        dialog.setMinimumSize(600, 550)
        dialog.resize(650, 600)
        dialog.setStyleSheet(get_current_theme())
        
        # Main layout with scroll area for better space management
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Format selection
        format_label = QLabel("Export Format:")
        format_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(format_label)
        
        format_combo = QComboBox()
        format_combo.addItems(["Side-by-Side (Both Cameras)", "DTL Only", "Face Only"])
        format_combo.setStyleSheet(f"""
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
        layout.addWidget(format_combo)
        
        # Codec selection
        codec_label = QLabel("Video Codec:")
        codec_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(codec_label)
        
        codec_combo = QComboBox()
        codec_combo.addItems(["mp4v", "H264", "X264", "XVID"])
        codec_combo.setCurrentText("mp4v")
        codec_combo.setStyleSheet(format_combo.styleSheet())
        layout.addWidget(codec_combo)
        
        # Quality preset
        quality_label = QLabel("Quality Preset:")
        quality_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(quality_label)
        
        quality_combo = QComboBox()
        quality_combo.addItems(["High (Best Quality)", "Medium (Balanced)", "Low (Small File)"])
        quality_combo.setCurrentText("High (Best Quality)")
        quality_combo.setStyleSheet(format_combo.styleSheet())
        layout.addWidget(quality_combo)
        
        def update_quality_settings():
            """Update scale and codec based on quality preset."""
            quality_text = quality_combo.currentText()
            if "High" in quality_text:
                scale_combo.setCurrentText("100% (Original)")
                codec_combo.setCurrentText("H264")
            elif "Medium" in quality_text:
                scale_combo.setCurrentText("75%")
                codec_combo.setCurrentText("H264")
            elif "Low" in quality_text:
                scale_combo.setCurrentText("50%")
                codec_combo.setCurrentText("mp4v")
        
        quality_combo.currentTextChanged.connect(update_quality_settings)
        
        # Compression options
        compression_label = QLabel("Compression:")
        compression_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(compression_label)
        
        compression_widget = QWidget()
        compression_layout = QHBoxLayout(compression_widget)
        compression_layout.setContentsMargins(0, 0, 0, 0)
        
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.BODY}px;")
        scale_label.setMinimumWidth(50)
        compression_layout.addWidget(scale_label)
        
        scale_combo = QComboBox()
        scale_combo.addItems(["100% (Original)", "75%", "50%", "25%"])
        scale_combo.setCurrentText("100% (Original)")
        scale_combo.setStyleSheet(format_combo.styleSheet())
        compression_layout.addWidget(scale_combo)
        
        compression_layout.addStretch()
        layout.addWidget(compression_widget)
        
        # Trimming options
        trim_check = QCheckBox("Trim Video")
        trim_check.setStyleSheet(f"""
            QCheckBox {{
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
            QCheckBox::indicator:checked {{
                background-color: {current_colors.ACCENT};
                border-color: {current_colors.ACCENT};
            }}
        """)
        layout.addWidget(trim_check)
        
        trim_widget = QWidget()
        trim_layout = QHBoxLayout(trim_widget)
        trim_layout.setContentsMargins(SPACING.MEDIUM, 0, 0, 0)
        trim_layout.setSpacing(SPACING.MEDIUM)
        
        start_label = QLabel("Start Frame:")
        start_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.BODY}px;")
        start_label.setMinimumWidth(80)
        trim_layout.addWidget(start_label)
        
        start_spin = QSpinBox()
        start_spin.setMinimum(0)
        start_spin.setMaximum(max(self.dtl_total_frames, self.face_total_frames) - 1)
        start_spin.setValue(0)
        start_spin.setMinimumWidth(100)
        start_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                min-width: 100px;
            }}
            QSpinBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        trim_layout.addWidget(start_spin)
        
        trim_layout.addSpacing(SPACING.LARGE)
        
        end_label = QLabel("End Frame:")
        end_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.BODY}px;")
        end_label.setMinimumWidth(80)
        trim_layout.addWidget(end_label)
        
        end_spin = QSpinBox()
        end_spin.setMinimum(1)
        end_spin.setMaximum(max(self.dtl_total_frames, self.face_total_frames))
        end_spin.setValue(max(self.dtl_total_frames, self.face_total_frames))
        end_spin.setMinimumWidth(100)
        end_spin.setStyleSheet(start_spin.styleSheet())
        trim_layout.addWidget(end_spin)
        
        trim_layout.addStretch()
        layout.addWidget(trim_widget)
        trim_widget.setEnabled(False)
        trim_check.toggled.connect(trim_widget.setEnabled)
        
        # Add stretch to push content up
        layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons (outside scroll area, always visible)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(SPACING.LARGE, SPACING.MEDIUM, SPACING.LARGE, SPACING.LARGE)
        buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
                border-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        buttons.addWidget(export_btn)
        
        main_layout.addLayout(buttons)
        
        def do_export() -> None:
            format_type = format_combo.currentText()
            codec = codec_combo.currentText()
            trim = trim_check.isChecked()
            start_frame = start_spin.value() if trim else None
            end_frame = end_spin.value() if trim else None
            
            # Parse quality preset
            quality_text = quality_combo.currentText()
            quality_presets = {
                "High (Best Quality)": {"scale": 1.0, "codec": "H264"},
                "Medium (Balanced)": {"scale": 0.75, "codec": "H264"},
                "Low (Small File)": {"scale": 0.5, "codec": "mp4v"},
            }
            preset = quality_presets.get(quality_text, {"scale": 1.0, "codec": "H264"})
            
            # Use preset or manual settings
            if quality_text != "High (Best Quality)":
                scale_factor = preset["scale"]
                codec = preset["codec"]
                scale_combo.setCurrentText(f"{int(preset['scale'] * 100)}%")
                codec_combo.setCurrentText(preset["codec"])
            else:
                # Parse scale factor from manual selection
                scale_text = scale_combo.currentText()
                scale_map = {"100% (Original)": 1.0, "75%": 0.75, "50%": 0.5, "25%": 0.25}
                scale_factor = scale_map.get(scale_text, 1.0)
            
            # Get output path
            default_name = f"shot_{self.shot_id}_export.mp4" if self.shot_id else "export.mp4"
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Video",
                default_name,
                "Video Files (*.mp4 *.avi);;All Files (*)",
            )
            
            if not output_path:
                return
            
            output_path = Path(output_path)
            
            # Show progress dialog with cancel button
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Exporting video...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Exporting Video")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            cancelled = [False]  # Use list to allow modification in nested function
            
            def progress_callback(current: int, total: int) -> None:
                if total > 0:
                    percent = int((current / total) * 100)
                    progress.setValue(percent)
                    progress.setLabelText(f"Exporting video... {current}/{total} frames")
                if progress.wasCanceled():
                    cancelled[0] = True
            
            try:
                from core.video_export import export_dual_video_side_by_side, export_video_with_drawings
                
                dtl_lines = self.dtl_canvas.lines if hasattr(self.dtl_canvas, 'lines') else []
                face_lines = self.face_canvas.lines if hasattr(self.face_canvas, 'lines') else []
                dtl_overlay = self.dtl_canvas.overlay_text if hasattr(self.dtl_canvas, 'overlay_text') else ""
                face_overlay = self.face_canvas.overlay_text if hasattr(self.face_canvas, 'overlay_text') else ""
                
                success = False
                
                if format_type == "Side-by-Side (Both Cameras)":
                    success = export_dual_video_side_by_side(
                        self.dtl_path,
                        self.face_path,
                        output_path,
                        dtl_lines,
                        face_lines,
                        dtl_overlay,
                        face_overlay,
                        codec,
                        self.fps,
                        start_frame,
                        end_frame,
                        scale_factor,
                        progress_callback=progress_callback,
                    )
                elif format_type == "DTL Only" and self.dtl_path:
                    # Determine quality based on preset
                    quality_value = 95 if "High" in quality_text else (85 if "Medium" in quality_text else 70)
                    success = export_video_with_drawings(
                        self.dtl_path,
                        output_path,
                        dtl_lines,
                        dtl_overlay,
                        codec,
                        self.fps,
                        start_frame,
                        end_frame,
                        quality=quality_value,
                        scale_factor=scale_factor,
                        progress_callback=progress_callback,
                    )
                elif format_type == "Face Only" and self.face_path:
                    # Determine quality based on preset
                    quality_value = 95 if "High" in quality_text else (85 if "Medium" in quality_text else 70)
                    success = export_video_with_drawings(
                        self.face_path,
                        output_path,
                        face_lines,
                        face_overlay,
                        codec,
                        self.fps,
                        start_frame,
                        end_frame,
                        quality=quality_value,
                        scale_factor=scale_factor,
                        progress_callback=progress_callback,
                    )
                
                progress.close()
                
                if cancelled[0]:
                    QMessageBox.information(self, "Export Cancelled", "Video export was cancelled.")
                    return
                
                if success:
                    QMessageBox.information(
                        self,
                        "Export Complete",
                        f"Video exported successfully to:\n{output_path}",
                    )
                    dialog.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Export Failed",
                        "Failed to export video. Check logs for details.",
                    )
            except Exception as e:
                progress.close()
                logger.error("Error exporting video: %s", e, exc_info=True)
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"An error occurred during export:\n{str(e)}",
                )
        
        export_btn.clicked.connect(do_export)
        
        dialog.exec()
    
    def _set_thumbnail_from_frame(self) -> None:
        """Set thumbnail from current frame."""
        if not self.shot_id or not self.session_manager:
            QMessageBox.warning(self, "No Shot", "Cannot set thumbnail: no shot selected.")
            return
        
        # Determine which video to use for thumbnail
        video_path = None
        if self.dtl_path and self.dtl_path.exists():
            video_path = self.dtl_path
        elif self.face_path and self.face_path.exists():
            video_path = self.face_path
        
        if not video_path:
            QMessageBox.warning(self, "No Video", "No video available for thumbnail generation.")
            return
        
        try:
            from core.thumbnails import generate_thumbnail
            
            # Generate thumbnail from current frame
            result = generate_thumbnail(video_path, frame_number=self.current_frame)
            
            if result:
                QMessageBox.information(
                    self,
                    "Thumbnail Set",
                    f"Thumbnail generated from frame {self.current_frame + 1}:\n{result}",
                )
                logger.info("Set thumbnail for shot %d from frame %d", self.shot_id, self.current_frame)
            else:
                QMessageBox.warning(self, "Failed", "Failed to generate thumbnail.")
        except Exception as e:
            logger.error("Error setting thumbnail: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Error setting thumbnail:\n{str(e)}")
    
    def _toggle_overlay(self) -> None:
        """Toggle shot data overlay on/off."""
        if not hasattr(self, "overlay_enabled"):
            self.overlay_enabled = True
        self.overlay_enabled = not self.overlay_enabled
        
        # Update list item to show state
        if hasattr(self, "tool_items_map") and "overlay" in self.tool_items_map:
            item = self.tool_items_map["overlay"]
            if self.overlay_enabled:
                item.setText("📊 Toggle Overlay (On)")
            else:
                item.setText("📊 Toggle Overlay (Off)")
        
        self.dtl_canvas.set_shot_data_overlay(self.overlay_enabled)
        self.face_canvas.set_shot_data_overlay(self.overlay_enabled)
    
    def _open_overlay_settings(self) -> None:
        """Open overlay settings dialog."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QColorDialog, QCheckBox, QGroupBox
        from PyQt6.QtGui import QColor
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Overlay Settings")
        dialog.setMinimumSize(500, 600)
        dialog.resize(600, 700)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Position selection
        position_group = QGroupBox("Position")
        position_group.setStyleSheet(f"""
            QGroupBox {{
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: {TYPOGRAPHY.BOLD};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                margin-top: {SPACING.MEDIUM}px;
                padding-top: {SPACING.MEDIUM}px;
            }}
        """)
        position_layout = QVBoxLayout(position_group)
        
        position_combo = QComboBox()
        position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        current_pos = self.dtl_canvas.overlay_position
        position_map = {"top-left": 0, "top-right": 1, "bottom-left": 2, "bottom-right": 3}
        position_combo.setCurrentIndex(position_map.get(current_pos, 0))
        position_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        position_layout.addWidget(position_combo)
        layout.addWidget(position_group)
        
        # Metrics selection
        metrics_group = QGroupBox("Metrics to Display")
        metrics_group.setStyleSheet(position_group.styleSheet())
        metrics_layout = QVBoxLayout(metrics_group)
        
        available_metrics = {
            "club_speed": "Club Speed",
            "ball_speed": "Ball Speed",
            "carry_distance": "Carry Distance",
            "total_distance": "Total Distance",
            "spin_rate": "Spin Rate",
            "launch_angle": "Launch Angle",
            "smash_factor": "Smash Factor",
        }
        
        metric_checkboxes = {}
        for metric_key, metric_label in available_metrics.items():
            checkbox = QCheckBox(metric_label)
            checkbox.setChecked(metric_key in self.dtl_canvas.overlay_metrics)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.BODY}px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    background-color: {current_colors.BACKGROUND_CONTROL};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {current_colors.ACCENT};
                    border-color: {current_colors.ACCENT};
                }}
            """)
            metric_checkboxes[metric_key] = checkbox
            metrics_layout.addWidget(checkbox)
        
        layout.addWidget(metrics_group)
        
        # Style settings
        style_group = QGroupBox("Style")
        style_group.setStyleSheet(position_group.styleSheet())
        style_layout = QVBoxLayout(style_group)
        
        # Font size
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        font_size_layout.addWidget(font_size_label)
        font_size_spin = QSpinBox()
        font_size_spin.setMinimum(8)
        font_size_spin.setMaximum(32)
        font_size_spin.setValue(self.dtl_canvas.overlay_style["font_size"])
        font_size_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
        """)
        font_size_layout.addWidget(font_size_spin)
        font_size_layout.addStretch()
        style_layout.addLayout(font_size_layout)
        
        # Colors
        color_layout = QHBoxLayout()
        bg_color_label = QLabel("Background:")
        bg_color_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        color_layout.addWidget(bg_color_label)
        
        bg_color_btn = QPushButton()
        bg_color_btn.setFixedSize(60, 30)
        bg_color = self.dtl_canvas.overlay_style["background_color"]
        bg_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color.name()};
                border: 2px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
        """)
        
        bg_color_var = [bg_color]  # Use list to allow modification in nested function
        
        def pick_bg_color():
            from app.design_constants import get_current_colors, SIZES, TYPOGRAPHY
            current_colors = get_current_colors()

            color = QColorDialog.getColor(bg_color_var[0], dialog, "Select Background Color")
            if color.isValid():
                bg_color_var[0] = color
                bg_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        border: 2px solid {current_colors.BORDER_HOVER};
                        border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    }}
                """)
        
        bg_color_btn.clicked.connect(pick_bg_color)
        color_layout.addWidget(bg_color_btn)
        color_layout.addStretch()
        
        text_color_label = QLabel("Text:")
        text_color_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        color_layout.addWidget(text_color_label)
        
        text_color_btn = QPushButton()
        text_color_btn.setFixedSize(60, 30)
        text_color = self.dtl_canvas.overlay_style["text_color"]
        text_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {text_color.name()};
                border: 2px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
        """)
        
        text_color_var = [text_color]  # Use list to allow modification in nested function
        
        def pick_text_color():
            from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
            current_colors = get_current_colors()

            color = QColorDialog.getColor(text_color_var[0], dialog, "Select Text Color")
            if color.isValid():
                text_color_var[0] = color
                text_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        border: 2px solid {current_colors.BORDER_HOVER};
                        border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    }}
                """)
        
        text_color_btn.clicked.connect(pick_text_color)
        color_layout.addWidget(text_color_btn)
        style_layout.addLayout(color_layout)
        
        layout.addWidget(style_group)
        
        layout.addStretch()
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
                border-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        
        def save_settings():
            # Position
            pos_map = {0: "top-left", 1: "top-right", 2: "bottom-left", 3: "bottom-right"}
            new_position = pos_map[position_combo.currentIndex()]
            self.dtl_canvas.set_overlay_position(new_position)
            self.face_canvas.set_overlay_position(new_position)
            
            # Metrics
            selected_metrics = [key for key, cb in metric_checkboxes.items() if cb.isChecked()]
            self.dtl_canvas.set_overlay_metrics(selected_metrics)
            self.face_canvas.set_overlay_metrics(selected_metrics)
            
            # Style
            new_style = {
                "font_size": font_size_spin.value(),
                "background_color": bg_color_var[0],
                "text_color": text_color_var[0],
            }
            self.dtl_canvas.set_overlay_style(new_style)
            self.face_canvas.set_overlay_style(new_style)
            
            dialog.accept()
        
        save_btn.clicked.connect(save_settings)
        buttons.addWidget(save_btn)
        
        layout.addLayout(buttons)
        
        dialog.exec()
    
    def _update_shot_data_overlays(self) -> None:
        """Update shot data overlays on both canvases."""
        # Map shot_data keys to overlay metric keys
        shot_data_dict = {}
        metric_map = {
            "ClubSpeed": "club_speed",
            "BallSpeed": "ball_speed",
            "CarryDistance": "carry_distance",
            "TotalDistance": "total_distance",
            "TotalSpin": "spin_rate",
            "LaunchAngle": "launch_angle",
            "SmashFactor": "smash_factor",
        }
        
        for key, value in self.shot_data.items():
            metric_key = metric_map.get(key)
            if metric_key and value is not None:
                shot_data_dict[metric_key] = value
        
        enabled = self.overlay_toggle_btn.isChecked() if hasattr(self, 'overlay_toggle_btn') else True
        self.dtl_canvas.set_shot_data_overlay(enabled, shot_data_dict)
        self.face_canvas.set_shot_data_overlay(enabled, shot_data_dict)
    
    def _goto_frame_dialog(self) -> None:
        """Open dialog to jump to specific frame."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        if max_frames == 0:
            QMessageBox.warning(self, "No Video", "No video loaded.")
            return
        
        frame_num, ok = QInputDialog.getInt(
            self,
            "Go to Frame",
            f"Enter frame number (1-{max_frames}):",
            self.current_frame + 1,
            1,
            max_frames,
            1
        )
        
        if ok:
            self._seek_to_frame(frame_num - 1)
    
    def _toggle_impact_zone(self) -> None:
        """Toggle impact zone auto-slowdown."""
        if not hasattr(self, "impact_zone_enabled"):
            self.impact_zone_enabled = True
        self.impact_zone_enabled = not self.impact_zone_enabled
        
        # Update list item to show state
        if hasattr(self, "tool_items_map") and "autoslow" in self.tool_items_map:
            item = self.tool_items_map["autoslow"]
            if self.impact_zone_enabled:
                item.setText("⏱ Auto-Slowdown (On)")
            else:
                item.setText("⏱ Auto-Slowdown (Off)")
        
        if not self.impact_zone_enabled and self.original_speed_before_zone is not None:
            self.playback_worker.set_speed(self.original_speed_before_zone)
            self.original_speed_before_zone = None
    
    def _select_measurement_tool(self, tool_type: str) -> None:
        """Select measurement tool (distance or angle)."""
        # Update list selection if using QListWidget
        if hasattr(self, "tool_items_map") and hasattr(self, "tool_list"):
            # Clear previous selection for measurement tools
            measurement_tool_ids = ["distance", "angle", "path"]
            for tool_id in measurement_tool_ids:
                if tool_id in self.tool_items_map:
                    item = self.tool_items_map[tool_id]
                    if item.listWidget():
                        item.listWidget().setCurrentItem(None)
            
            # Set new selection
            if tool_type in self.tool_items_map:
                item = self.tool_items_map[tool_type]
                if item.listWidget():
                    item.listWidget().setCurrentItem(item)
        
        # Clear drawing modes
        self.dtl_canvas.drawing_mode = None
        self.face_canvas.drawing_mode = None
        
        # Start measurement - each canvas has its own measurement tool
        if tool_type == "distance":
            self.dtl_canvas.measurement_tool.start_measurement("distance")
            self.face_canvas.measurement_tool.start_measurement("distance")
            self.dtl_canvas.drawing_mode = "measure_distance"
            self.face_canvas.drawing_mode = "measure_distance"
        elif tool_type == "angle":
            self.dtl_canvas.measurement_tool.start_measurement("angle")
            self.face_canvas.measurement_tool.start_measurement("angle")
            self.dtl_canvas.drawing_mode = "measure_angle"
            self.face_canvas.drawing_mode = "measure_angle"
    
    def _toggle_path_tracing(self) -> None:
        """Toggle swing path tracing - each canvas has its own tracer."""
        # Toggle state
        if hasattr(self, "path_tracing_enabled"):
            self.path_tracing_enabled = not self.path_tracing_enabled
        else:
            self.path_tracing_enabled = True
        
        # Update list item to show state
        if hasattr(self, "tool_items_map") and "path" in self.tool_items_map:
            item = self.tool_items_map["path"]
            if self.path_tracing_enabled:
                item.setText("⌇ Trace Path (On)")
            else:
                item.setText("⌇ Trace Path (Off)")
        
        if self.path_tracing_enabled:
            self.dtl_canvas.path_tracer.start_tracing()
            self.face_canvas.path_tracer.start_tracing()
            self.dtl_canvas.drawing_mode = "path_trace"
            self.face_canvas.drawing_mode = "path_trace"
        else:
            self.dtl_canvas.path_tracer.stop_tracing()
            self.face_canvas.path_tracer.stop_tracing()
            self.dtl_canvas.drawing_mode = None
            self.face_canvas.drawing_mode = None
    
    def _open_trim_dialog(self) -> None:
        """Open video trimming dialog."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        max_frames = max(self.dtl_total_frames, self.face_total_frames)
        if max_frames == 0:
            QMessageBox.warning(self, "No Video", "No video loaded.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Trim Video")
        dialog.setMinimumSize(500, 300)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        info_label = QLabel(f"Select start and end frames for trimming (Total: {max_frames} frames)")
        info_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        layout.addWidget(info_label)
        
        # Start frame
        start_layout = QHBoxLayout()
        start_label = QLabel("Start Frame:")
        start_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        start_layout.addWidget(start_label)
        
        start_spin = QSpinBox()
        start_spin.setMinimum(0)
        start_spin.setMaximum(max_frames - 1)
        start_spin.setValue(self.trim_start_frame)
        start_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        start_layout.addWidget(start_spin)
        layout.addLayout(start_layout)
        
        # End frame
        end_layout = QHBoxLayout()
        end_label = QLabel("End Frame:")
        end_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px;")
        end_layout.addWidget(end_label)
        
        end_spin = QSpinBox()
        end_spin.setMinimum(0)
        end_spin.setMaximum(max_frames - 1)
        end_spin.setValue(self.trim_end_frame if self.trim_end_frame else max_frames - 1)
        end_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
        """)
        end_layout.addWidget(end_spin)
        layout.addLayout(end_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.trim_start_frame = start_spin.value()
            self.trim_end_frame = end_spin.value()
            if self.trim_start_frame >= self.trim_end_frame:
                QMessageBox.warning(self, "Invalid Range", "Start frame must be less than end frame.")
                return
            
            # Apply trim (this would need video export functionality)
            QMessageBox.information(
                self,
                "Trim Set",
                f"Trim range set: frames {self.trim_start_frame} to {self.trim_end_frame}.\n"
                f"Use Export Video to save trimmed version."
            )
    
    def _save_measurements(self) -> None:
        """Save measurements to database.
        
        Saves measurements from both DTL and Face canvases.
        Can be triggered via save button or Ctrl+S shortcut.
        """
        if not hasattr(self, 'shot_id') or not self.shot_id or not hasattr(self, 'session_manager'):
            return
        
        saved = False
        if hasattr(self.dtl_canvas, 'measurement_tool'):
            if self.dtl_canvas.measurement_tool.save_measurements(self.shot_id, self.session_manager):
                saved = True
        if hasattr(self.face_canvas, 'measurement_tool'):
            if self.face_canvas.measurement_tool.save_measurements(self.shot_id, self.session_manager):
                saved = True
        
        if saved:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Saved", "Measurements saved successfully.")
    
    def eventFilter(self, obj, event) -> bool:
        """Event filter for timeline slider preview."""
        if obj == self.progress_slider:
            from PyQt6.QtCore import QEvent
            if event.type() == QEvent.Type.MouseMove:
                # Update tooltip with frame number
                pos = event.position().x() if hasattr(event, 'position') else event.x()
                slider_width = self.progress_slider.width()
                max_frames = max(self.dtl_total_frames, self.face_total_frames)
                if slider_width > 0 and max_frames > 0:
                    frame = int((pos / slider_width) * max_frames)
                    frame = max(0, min(frame, max_frames - 1))
                    self.progress_slider.setToolTip(f"Frame: {frame + 1} / {max_frames}")
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        # Save measurements before closing
        self._save_measurements()
        
        if hasattr(self, "playback_worker"):
            self.playback_worker.pause_playback()
            self.playback_worker.stop_worker()
        if self.dtl_cap:
            self.dtl_cap.release()
        if self.face_cap:
            self.face_cap.release()
        event.accept()

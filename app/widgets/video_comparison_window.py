"""Enhanced video comparison window with synchronized playback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from app.theme import get_current_theme
from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
from app.widgets.shot_review_window import VideoCanvas
from app.style_helpers import style_button, style_label, style_input

logger = logging.getLogger(__name__)


class SynchronizedPlaybackWorker(QThread):
    """Worker thread for synchronized playback of multiple videos."""
    
    tick = pyqtSignal()
    diagnostics = pyqtSignal(str)
    
    def __init__(self, fps: float, playback_speed: float):
        super().__init__()
        self.fps = fps
        self.playback_speed = playback_speed
        self._paused = False
        self._stopped = False
    
    def pause_playback(self) -> None:
        """Pause playback."""
        self._paused = True
    
    def resume_playback(self) -> None:
        """Resume playback."""
        self._paused = False
    
    def stop_playback(self) -> None:
        """Stop playback."""
        self._stopped = True
    
    def run(self) -> None:
        """Run playback loop."""
        import time
        
        while not self._stopped:
            if not self._paused:
                self.tick.emit()
            
            base_time_per_frame_ms = (1000.0 / self.fps) if self.fps > 0 else 33.0
            time_per_frame_ms = base_time_per_frame_ms / self.playback_speed
            sleep_seconds = time_per_frame_ms / 1000.0
            
            time.sleep(sleep_seconds)


class VideoComparisonWindow(QDialog):
    """Enhanced side-by-side video comparison with synchronized playback."""
    
    def __init__(
        self,
        left_video_data: dict,
        right_video_data: dict,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Video Comparison - Synchronized Playback")
        self.setMinimumSize(1600, 800)
        self.resize(1800, 900)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self.left_data = left_video_data
        self.right_data = right_video_data
        
        # Video capture objects
        self.left_dtl_cap: Optional[cv2.VideoCapture] = None
        self.left_face_cap: Optional[cv2.VideoCapture] = None
        self.right_dtl_cap: Optional[cv2.VideoCapture] = None
        self.right_face_cap: Optional[cv2.VideoCapture] = None
        
        # Frame tracking
        self.current_frame = 0
        self.left_dtl_frames = 0
        self.left_face_frames = 0
        self.right_dtl_frames = 0
        self.right_face_frames = 0
        self.fps = 30
        
        # Playback state
        self.playback_speed = 0.1
        self.playing = False
        self.playback_worker = SynchronizedPlaybackWorker(self.fps, self.playback_speed)
        self.playback_worker.tick.connect(self._on_playback_tick)
        self.playback_worker.start()
        
        self._load_videos()
        self._build_ui()
        self._setup_shortcuts()
        self._update_frames()
    
    def _load_videos(self) -> None:
        """Load video files for both sides."""
        # Left side videos
        if self.left_data.get("dtl_path") and self.left_data["dtl_path"].exists():
            self.left_dtl_cap = cv2.VideoCapture(str(self.left_data["dtl_path"]))
            if self.left_dtl_cap.isOpened():
                self.left_dtl_frames = int(self.left_dtl_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.left_dtl_cap.get(cv2.CAP_PROP_FPS) or 30
        
        if self.left_data.get("face_path") and self.left_data["face_path"].exists():
            self.left_face_cap = cv2.VideoCapture(str(self.left_data["face_path"]))
            if self.left_face_cap.isOpened():
                self.left_face_frames = int(self.left_face_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Right side videos
        if self.right_data.get("dtl_path") and self.right_data["dtl_path"].exists():
            self.right_dtl_cap = cv2.VideoCapture(str(self.right_data["dtl_path"]))
            if self.right_dtl_cap.isOpened():
                self.right_dtl_frames = int(self.right_dtl_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if self.right_data.get("face_path") and self.right_data["face_path"].exists():
            self.right_face_cap = cv2.VideoCapture(str(self.right_data["face_path"]))
            if self.right_face_cap.isOpened():
                self.right_face_frames = int(self.right_face_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Update max frames (ensure at least 1 to avoid division by zero)
        max_frames = max(
            self.left_dtl_frames,
            self.left_face_frames,
            self.right_dtl_frames,
            self.right_face_frames,
            1,  # Minimum of 1 frame
        )
        self.max_frames = max_frames
    
    def _build_ui(self) -> None:
        """Build the comparison UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar with session names and shot data
        top_bar = QWidget()
        top_bar.setStyleSheet(f"""
            background-color: {current_colors.BACKGROUND_SURFACE};
            border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
            padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
        """)
        top_bar.setMinimumHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(SPACING.MEDIUM, SPACING.SMALL, SPACING.MEDIUM, SPACING.SMALL)
        top_layout.setSpacing(SPACING.MEDIUM)
        
        # Left side info
        left_info = QLabel(
            f"<b>{self.left_data.get('session_name', 'Left')}</b><br>"
            f"Club: {self.left_data.get('shot_data', {}).get('ClubSpeed', '--')} mph | "
            f"Ball: {self.left_data.get('shot_data', {}).get('BallSpeed', '--')} mph | "
            f"Spin: {self.left_data.get('shot_data', {}).get('TotalSpin', '--')} rpm"
        )
        left_info.setStyleSheet(style_label(weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        top_layout.addWidget(left_info)
        
        top_layout.addStretch()
        
        # Right side info
        right_info = QLabel(
            f"<b>{self.right_data.get('session_name', 'Right')}</b><br>"
            f"Club: {self.right_data.get('shot_data', {}).get('ClubSpeed', '--')} mph | "
            f"Ball: {self.right_data.get('shot_data', {}).get('BallSpeed', '--')} mph | "
            f"Spin: {self.right_data.get('shot_data', {}).get('TotalSpin', '--')} rpm"
        )
        right_info.setStyleSheet(style_label(weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        right_info.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_layout.addWidget(right_info)
        
        layout.addWidget(top_bar)
        
        # Main splitter for side-by-side comparison
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        # Left side panel
        left_panel = self._create_video_panel("Left", self.left_data)
        main_splitter.addWidget(left_panel)
        
        # Right side panel
        right_panel = self._create_video_panel("Right", self.right_data)
        main_splitter.addWidget(right_panel)
        
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([900, 900])
        
        layout.addWidget(main_splitter, 1)
        
        # Shared controls at bottom
        controls = self._create_controls()
        layout.addWidget(controls, 0)
    
    def _create_video_panel(self, side: str, video_data: dict) -> QWidget:
        """Create a video panel for one side."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(0)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Vertical splitter for DTL and Face views
        video_splitter = QSplitter(Qt.Orientation.Vertical, panel)
        video_splitter.setChildrenCollapsible(False)
        video_splitter.setHandleWidth(2)
        video_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        # DTL canvas
        dtl_canvas = VideoCanvas(f"{side} - Down the Line")
        dtl_canvas.setMinimumSize(200, 150)
        dtl_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dtl_canvas.setAutoFillBackground(True)
        dtl_canvas.setStyleSheet(f"""
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
        dtl_canvas.setText(f"{side} - DTL\nWaiting for frames...")
        dtl_canvas.setScaledContents(False)
        dtl_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        dtl_scroll = QScrollArea()
        dtl_scroll.setWidget(dtl_canvas)
        dtl_scroll.setWidgetResizable(True)
        dtl_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        dtl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dtl_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        video_splitter.addWidget(dtl_scroll)
        
        # Face canvas
        face_canvas = VideoCanvas(f"{side} - Face On")
        face_canvas.setMinimumSize(200, 150)
        face_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        face_canvas.setAutoFillBackground(True)
        face_canvas.setStyleSheet(dtl_canvas.styleSheet())
        face_canvas.setText(f"{side} - Face On\nWaiting for frames...")
        face_canvas.setScaledContents(False)
        face_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        face_scroll = QScrollArea()
        face_scroll.setWidget(face_canvas)
        face_scroll.setWidgetResizable(True)
        face_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        face_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        face_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        video_splitter.addWidget(face_scroll)
        
        video_splitter.setStretchFactor(0, 1)
        video_splitter.setStretchFactor(1, 1)
        video_splitter.setSizes([400, 400])
        
        panel_layout.addWidget(video_splitter)
        
        # Store canvas references
        if side == "Left":
            self.left_dtl_canvas = dtl_canvas
            self.left_face_canvas = face_canvas
        else:
            self.right_dtl_canvas = dtl_canvas
            self.right_face_canvas = face_canvas
        
        return panel
    
    def _create_controls(self) -> QWidget:
        """Create shared playback controls."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        controls = QWidget()
        controls.setStyleSheet(f"""
            background-color: {current_colors.BACKGROUND_SURFACE};
            border-top: 1px solid {current_colors.BORDER_DEFAULT};
            padding: {SPACING.SMALL}px;
        """)
        controls.setMinimumHeight(100)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setSpacing(SPACING.SMALL)
        controls_layout.setContentsMargins(SPACING.MEDIUM, SPACING.SMALL, SPACING.MEDIUM, SPACING.SMALL)
        
        # Progress slider
        from app.widgets.marked_slider import MarkedSlider
        self.progress_slider = MarkedSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(max(0, self.max_frames - 1))
        self.progress_slider.valueChanged.connect(self._seek_to_frame)
        self._slider_updating = False
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {current_colors.BORDER_DEFAULT};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {current_colors.ACCENT};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {current_colors.ACCENT};
                border-radius: 2px;
            }}
        """)
        controls_layout.addWidget(self.progress_slider)
        
        # Transport controls
        buttons_bar = QWidget()
        buttons_layout = QHBoxLayout(buttons_bar)
        buttons_layout.setSpacing(SPACING.SMALL)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Transport buttons
        self.rewind_btn = QPushButton("◀◀")
        self.rewind_btn.setToolTip("Rewind 10 frames")
        self.rewind_btn.setFixedSize(32, 32)
        self.rewind_btn.setStyleSheet(style_button(variant="secondary"))
        self.rewind_btn.clicked.connect(self._rewind)
        buttons_layout.addWidget(self.rewind_btn)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setToolTip("Play / Pause (Space)")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setStyleSheet(style_button(variant="primary"))
        self.play_btn.clicked.connect(self._toggle_play)
        buttons_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("■")
        self.stop_btn.setToolTip("Stop (S)")
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setStyleSheet(style_button(variant="secondary"))
        self.stop_btn.clicked.connect(self._stop)
        buttons_layout.addWidget(self.stop_btn)
        
        self.ffwd_btn = QPushButton("▶▶")
        self.ffwd_btn.setToolTip("Forward 10 frames")
        self.ffwd_btn.setFixedSize(32, 32)
        self.ffwd_btn.setStyleSheet(style_button(variant="secondary"))
        self.ffwd_btn.clicked.connect(self._fast_forward)
        buttons_layout.addWidget(self.ffwd_btn)
        
        buttons_layout.addSpacing(16)
        
        # Speed controls
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(style_label(secondary=True))
        buttons_layout.addWidget(speed_label)
        
        speed_presets = ["0.1x", "0.25x", "0.5x", "1x", "2x", "4x"]
        self.speed_preset_buttons = {}
        for preset in speed_presets:
            btn = QPushButton(preset)
            btn.setFixedSize(40, 24)
            btn.setCheckable(True)
            btn.setStyleSheet(style_button(variant="secondary") + f"""
                QPushButton:checked {{
                    background-color: {current_colors.ACCENT};
                    border-color: {current_colors.ACCENT};
                    color: {current_colors.WHITE_TEXT};
                }}
            """)
            btn.clicked.connect(lambda checked, p=preset: self._change_speed(p))
            self.speed_preset_buttons[preset] = btn
            buttons_layout.addWidget(btn)
        
        if "0.1x" in self.speed_preset_buttons:
            self.speed_preset_buttons["0.1x"].setChecked(True)
        
        buttons_layout.addStretch()
        
        # Frame counter
        self.frame_label = QLabel("Frame: 0 / 0")
        self.frame_label.setStyleSheet(style_label(secondary=True))
        buttons_layout.addWidget(self.frame_label)
        
        controls_layout.addWidget(buttons_bar)
        
        return controls
    
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        QShortcut(QKeySequence("Space"), self, self._toggle_play)
        QShortcut(QKeySequence("S"), self, self._stop)
        QShortcut(QKeySequence("Left"), self, self._rewind)
        QShortcut(QKeySequence("Right"), self, self._fast_forward)
        QShortcut(QKeySequence("Shift+Left"), self, lambda: self._step_frame(-1))
        QShortcut(QKeySequence("Shift+Right"), self, lambda: self._step_frame(1))
        QShortcut(QKeySequence("1"), self, lambda: self._change_speed("0.1x"))
        QShortcut(QKeySequence("2"), self, lambda: self._change_speed("0.25x"))
        QShortcut(QKeySequence("3"), self, lambda: self._change_speed("0.5x"))
        QShortcut(QKeySequence("4"), self, lambda: self._change_speed("1x"))
        QShortcut(QKeySequence("5"), self, lambda: self._change_speed("2x"))
        QShortcut(QKeySequence("6"), self, lambda: self._change_speed("4x"))
    
    def _seek_to_frame(self, frame: int) -> None:
        """Seek all videos to specified frame."""
        if self._slider_updating:
            return
        
        self.current_frame = max(0, min(self.max_frames - 1, frame))
        self._update_frames()
        self._update_frame_label()
    
    def _update_frames(self) -> None:
        """Update all video frames to current position."""
        # Update left side
        self._update_canvas_frame(
            self.left_dtl_canvas,
            self.left_dtl_cap,
            self.left_dtl_frames,
            self.left_data.get("shot_data", {}),
        )
        self._update_canvas_frame(
            self.left_face_canvas,
            self.left_face_cap,
            self.left_face_frames,
            self.left_data.get("shot_data", {}),
        )
        
        # Update right side
        self._update_canvas_frame(
            self.right_dtl_canvas,
            self.right_dtl_cap,
            self.right_dtl_frames,
            self.right_data.get("shot_data", {}),
        )
        self._update_canvas_frame(
            self.right_face_canvas,
            self.right_face_cap,
            self.right_face_frames,
            self.right_data.get("shot_data", {}),
        )
    
    def _update_canvas_frame(
        self,
        canvas: VideoCanvas,
        cap: Optional[cv2.VideoCapture],
        total_frames: int,
        shot_data: dict,
    ) -> None:
        """Update a single canvas frame."""
        if not cap or not cap.isOpened():
            canvas.setText("No video available")
            return
        
        frame_num = min(self.current_frame, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if ret and frame is not None:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale to fit canvas while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            canvas.setPixmap(pixmap)
            
            # Add overlay with shot data
            # Convert shot_data keys to match VideoCanvas expected format
            canvas_data = {}
            if shot_data.get("ClubSpeed") is not None:
                canvas_data["club_speed"] = shot_data["ClubSpeed"]
            if shot_data.get("BallSpeed") is not None:
                canvas_data["ball_speed"] = shot_data["BallSpeed"]
            if shot_data.get("TotalSpin") is not None:
                canvas_data["spin_rate"] = shot_data["TotalSpin"]
            if shot_data.get("LaunchAngle") is not None:
                canvas_data["launch_angle"] = shot_data["LaunchAngle"]
            if shot_data.get("CarryDistance") is not None:
                canvas_data["carry_distance"] = shot_data["CarryDistance"]
            
            canvas.set_shot_data_overlay(True, canvas_data if canvas_data else None)
        else:
            canvas.setText("End of video")
    
    
    def _on_playback_tick(self) -> None:
        """Handle playback tick - advance all videos."""
        if self.playing:
            if self.current_frame < self.max_frames - 1:
                self.current_frame += 1
                self._update_frames()
                self._update_slider()
                self._update_frame_label()
            else:
                # End of video
                self._toggle_play()
    
    def _toggle_play(self) -> None:
        """Toggle playback."""
        self.playing = not self.playing
        if self.playing:
            self.play_btn.setText("⏸")
            self.play_btn.setToolTip("Pause (Space)")
            self.playback_worker.resume_playback()
        else:
            self.play_btn.setText("▶")
            self.play_btn.setToolTip("Play (Space)")
            self.playback_worker.pause_playback()
    
    def _stop(self) -> None:
        """Stop playback and return to start."""
        self.playing = False
        self.play_btn.setText("▶")
        self.current_frame = 0
        self._update_frames()
        self._update_slider()
        self._update_frame_label()
        self.playback_worker.pause_playback()
    
    def _rewind(self) -> None:
        """Rewind 10 frames."""
        self.current_frame = max(0, self.current_frame - 10)
        self._update_frames()
        self._update_slider()
        self._update_frame_label()
    
    def _fast_forward(self) -> None:
        """Fast forward 10 frames."""
        self.current_frame = min(self.max_frames - 1, self.current_frame + 10)
        self._update_frames()
        self._update_slider()
        self._update_frame_label()
    
    def _step_frame(self, direction: int) -> None:
        """Step one frame forward or backward."""
        was_playing = self.playing
        if was_playing:
            self._toggle_play()
        
        self.current_frame = max(0, min(self.max_frames - 1, self.current_frame + direction))
        self._update_frames()
        self._update_slider()
        self._update_frame_label()
    
    def _change_speed(self, speed_str: str) -> None:
        """Change playback speed."""
        speed_map = {
            "0.1x": 0.1,
            "0.25x": 0.25,
            "0.5x": 0.5,
            "1x": 1.0,
            "2x": 2.0,
            "4x": 4.0,
        }
        self.playback_speed = speed_map.get(speed_str, 0.1)
        self.playback_worker.playback_speed = self.playback_speed
        
        # Update button states
        for preset, btn in self.speed_preset_buttons.items():
            btn.setChecked(preset == speed_str)
    
    def _update_slider(self) -> None:
        """Update progress slider without triggering seek."""
        self._slider_updating = True
        self.progress_slider.setValue(self.current_frame)
        self._slider_updating = False
    
    def _update_frame_label(self) -> None:
        """Update frame counter label."""
        self.frame_label.setText(f"Frame: {self.current_frame + 1} / {self.max_frames}")
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        self.playback_worker.stop_playback()
        self.playback_worker.wait()
        
        # Release video captures
        for cap in [self.left_dtl_cap, self.left_face_cap, self.right_dtl_cap, self.right_face_cap]:
            if cap:
                cap.release()
        
        event.accept()


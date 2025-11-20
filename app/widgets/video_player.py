"""Video player widget for viewing and annotating saved clips."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


logger = logging.getLogger(__name__)


class VideoPlayer(QWidget):
    """Widget for playing video files with basic controls."""

    def __init__(self, video_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.playing = False
        self.timer: Optional[QTimer] = None
        
        self._load_video()
        self._build_ui()
        self._setup_timer()

    def _load_video(self) -> None:
        """Load video file."""
        if not self.video_path.exists():
            logger.error("Video file not found: %s", self.video_path)
            return
        
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            logger.error("Failed to open video: %s", self.video_path)
            return
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        logger.debug("Loaded video: %d frames, %.1f fps", self.total_frames, self.fps)

    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)

        # Video display
        self.video_label = QLabel("No video loaded")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumHeight(400)
        self.video_label.setAutoFillBackground(True)
        from app.design_constants import  SIZES, TYPOGRAPHY
        self.video_label.setStyleSheet(f"""

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
        layout.addWidget(self.video_label, 1)

        # Controls
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setSpacing(SPACING.SMALL)

        # Progress slider
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(max(0, self.total_frames - 1))
        self.progress_slider.valueChanged.connect(self._seek_to_frame)
        controls_layout.addWidget(self.progress_slider)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACING.SMALL)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._toggle_play)
        buttons_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._stop)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()

        self.frame_label = QLabel("Frame: 0 / 0")
        from app.design_constants import  TYPOGRAPHY
        self.frame_label.setAutoFillBackground(True)
        self.frame_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: 0px; margin: 0px;")
        buttons_layout.addWidget(self.frame_label)

        controls_layout.addLayout(buttons_layout)
        layout.addWidget(controls)

        # Load first frame
        self._update_frame()

    def _setup_timer(self) -> None:
        """Setup playback timer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        interval = int(1000 / self.fps) if self.fps > 0 else 33
        self.timer.setInterval(interval)

    def _toggle_play(self) -> None:
        """Toggle play/pause."""
        if not self.cap or not self.cap.isOpened():
            return
        
        self.playing = not self.playing
        if self.playing:
            self.play_btn.setText("⏸ Pause")
            self.timer.start()
        else:
            self.play_btn.setText("▶ Play")
            self.timer.stop()

    def _stop(self) -> None:
        """Stop playback and reset."""
        self.playing = False
        self.play_btn.setText("▶ Play")
        if self.timer:
            self.timer.stop()
        self.current_frame = 0
        self._update_frame()

    def _next_frame(self) -> None:
        """Advance to next frame."""
        if not self.cap or not self.cap.isOpened():
            return
        
        if self.current_frame >= self.total_frames - 1:
            self._stop()
            return
        
        self.current_frame += 1
        self._update_frame()

    def _seek_to_frame(self, frame: int) -> None:
        """Seek to frame."""
        if not self.cap or not self.cap.isOpened():
            return
        
        self.current_frame = frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        self._update_frame()

    def _update_frame(self) -> None:
        """Update displayed frame."""
        if not self.cap or not self.cap.isOpened():
            return
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        if not ret:
            logger.debug("Failed to read frame %d", self.current_frame)
            return
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb.shape
        bytes_per_line = 3 * width
        qimage = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)
        
        self.progress_slider.setValue(self.current_frame)
        self.frame_label.setText(f"Frame: {self.current_frame + 1} / {self.total_frames}")

    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        event.accept()



from __future__ import annotations

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout, QWidget


class CameraView(QWidget):
    """Widget showing live camera feed."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(200)  # Reduced for smaller screens
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName("cameraView")
        from app.design_constants import get_current_colors, SIZES, SPACING
        current_colors = get_current_colors()
        self.setStyleSheet(f"""
            QWidget#cameraView {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        layout.setSpacing(SPACING.MEDIUM)

        # Header with title and status indicator
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING.SMALL)
        
        self.title_label = QLabel(title)
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        self.title_label.setAutoFillBackground(True)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                font-size: {TYPOGRAPHY.H3}px;
                font-weight: {TYPOGRAPHY.BOLD};
                color: {current_colors.TEXT_PRIMARY};
                padding: 0px;
                margin: 0px;
            }}
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setAutoFillBackground(True)
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        self.status_indicator.setStyleSheet(f"""
            QLabel#statusIndicator {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                font-size: {TYPOGRAPHY.SMALL}px;
                padding: 0px;
                margin: 0px;
            }}
        """)
        self.status_indicator.setToolTip("Camera inactive")
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)

        self.image_label = QLabel("Waiting for frames...")
        self.image_label.setObjectName("image_label")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setAutoFillBackground(True)
        from app.design_constants import get_current_colors, SIZES, TYPOGRAPHY
        current_colors = get_current_colors()
        self.image_label.setStyleSheet(f"""
            QLabel#image_label {{
                background-color: {current_colors.BACKGROUND_BASE};
                border: 1px dashed {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                color: {current_colors.TEXT_SECONDARY};
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
                min-height: 150px;
                padding: 0px;
                margin: 0px;
            }}
        """)
        layout.addWidget(self.image_label, 1)
        
        self._is_active = False

    def update_frame(self, frame: np.ndarray) -> None:
        rgb = cv_to_qimage(frame)
        pixmap = QPixmap.fromImage(rgb).scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("")  # Clear placeholder text when frame arrives
        self.set_active(True)
    
    def set_active(self, active: bool) -> None:
        """Update camera status indicator."""
        if active == self._is_active:
            return
        self._is_active = active
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        if active:
            self.status_indicator.setStyleSheet(f"""
                QLabel#statusIndicator {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    color: {current_colors.SUCCESS};
                    font-size: {TYPOGRAPHY.SMALL}px;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            self.status_indicator.setToolTip("Camera active")
        else:
            self.status_indicator.setStyleSheet(f"""
                QLabel#statusIndicator {{
                    background-color: {current_colors.BACKGROUND_CONTROL};
                    color: {current_colors.TEXT_SECONDARY};
                    font-size: {TYPOGRAPHY.SMALL}px;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            self.status_indicator.setToolTip("Camera inactive")


def cv_to_qimage(frame: np.ndarray) -> QImage:
    """Convert OpenCV BGR frame to QImage RGB format."""
    height, width, channel = frame.shape
    bytes_per_line = 3 * width
    # Convert BGR to RGB and ensure contiguous array
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)


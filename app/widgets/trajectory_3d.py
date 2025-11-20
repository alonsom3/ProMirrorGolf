"""3D trajectory visualization widget for ball flight."""

from __future__ import annotations

import logging
from typing import Optional

import matplotlib
matplotlib.use('QtAgg')
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.analytics import calculate_trajectory_points
from core.session_manager import ShotModel

logger = logging.getLogger(__name__)


class Trajectory3DWidget(QWidget):
    """Widget for displaying 3D ball flight trajectories."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.shots: list[ShotModel] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI with 3D plot and controls."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.SMALL)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(SPACING.SMALL)
        
        # Shot selector
        shot_label = QLabel("Shot:")
        shot_label.setAutoFillBackground(True)
        shot_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        controls_layout.addWidget(shot_label)
        
        self.shot_combo = QComboBox()
        self.shot_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                min-width: 200px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        self.shot_combo.currentIndexChanged.connect(self._update_plot)
        controls_layout.addWidget(self.shot_combo)
        
        # View controls
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.setMinimumHeight(28)
        reset_view_btn.setMaximumHeight(36)
        reset_view_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        reset_view_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        reset_view_btn.clicked.connect(self._reset_view)
        controls_layout.addWidget(reset_view_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # 3D plot
        self.fig = Figure(figsize=(10, 8), facecolor=current_colors.BACKGROUND_BASE)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumHeight(400)
        
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(current_colors.BACKGROUND_BASE)
        
        # Set theme colors
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
        self.ax.yaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
        self.ax.zaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
        
        self.ax.xaxis.label.set_color(current_colors.TEXT_PRIMARY)
        self.ax.yaxis.label.set_color(current_colors.TEXT_PRIMARY)
        self.ax.zaxis.label.set_color(current_colors.TEXT_PRIMARY)
        self.ax.tick_params(colors=current_colors.TEXT_PRIMARY)
        
        self.ax.set_xlabel('Distance (yds)', color=current_colors.TEXT_PRIMARY)
        self.ax.set_ylabel('Lateral (yds)', color=current_colors.TEXT_PRIMARY)
        self.ax.set_zlabel('Height (yds)', color=current_colors.TEXT_PRIMARY)
        self.ax.set_title('3D Ball Flight Trajectory', color=current_colors.TEXT_PRIMARY, fontsize=14, fontweight='bold')
        
        layout.addWidget(self.canvas)
        
        # Info label
        self.info_label = QLabel("Select a shot to view trajectory")
        self.info_label.setAutoFillBackground(True)
        self.info_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.XS}px; margin: 0px;")
        layout.addWidget(self.info_label)
    
    def set_shots(self, shots: list[ShotModel]) -> None:
        """Set the shots to display."""
        self.shots = shots
        
        # Update combo box
        self.shot_combo.blockSignals(True)
        self.shot_combo.clear()
        
        for i, shot in enumerate(shots):
            # Create display text
            if shot.ball_speed and shot.launch_angle and shot.spin_rate:
                label = f"Shot {i+1}: {shot.ball_speed:.1f} mph, {shot.launch_angle:.1f}°"
            else:
                label = f"Shot {i+1}: (incomplete data)"
            self.shot_combo.addItem(label, shot)
        
        self.shot_combo.blockSignals(False)
        
        # Auto-select first shot if available
        if self.shot_combo.count() > 0:
            self.shot_combo.setCurrentIndex(0)
            self._update_plot()
    
    def _update_plot(self) -> None:
        """Update the 3D plot with selected shot."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        if self.shot_combo.count() == 0:
            return
        
        shot: ShotModel = self.shot_combo.currentData()
        if not shot:
            return
        
        # Check if shot has required data
        if not (shot.ball_speed and shot.launch_angle and shot.spin_rate):
            self.ax.clear()
            self.ax.text2D(0.5, 0.5, 'Insufficient data for trajectory calculation', 
                          ha='center', va='center', transform=self.ax.transAxes,
                          color=current_colors.TEXT_PRIMARY, fontsize=12)
            self.canvas.draw()
            self.info_label.setText("Selected shot has insufficient data")
            return
        
        # Calculate trajectory
        try:
            trajectory = calculate_trajectory_points(
                ball_speed=shot.ball_speed,
                launch_angle=shot.launch_angle,
                spin_rate=shot.spin_rate,
                launch_direction=shot.launch_direction,
                side_spin=shot.side_spin,
            )
            
            x = trajectory['x']
            y = trajectory['y']
            z = trajectory['z']
            
            # Clear and plot
            self.ax.clear()
            
            # Plot trajectory line
            self.ax.plot(x, y, z, color=current_colors.ACCENT, linewidth=2.5, label='Trajectory')
            
            # Mark key points
            # Launch point
            self.ax.scatter([x[0]], [y[0]], [z[0]], color=current_colors.SUCCESS, s=100, 
                          marker='o', label='Launch', zorder=10)
            
            # Apex point
            max_idx = np.argmax(z)
            self.ax.scatter([x[max_idx]], [y[max_idx]], [z[max_idx]], color='#ffd700', 
                          s=100, marker='^', label='Apex', zorder=10)
            
            # Landing point
            self.ax.scatter([x[-1]], [y[-1]], [z[-1]], color=current_colors.ACCENT_HOVER, s=100, 
                          marker='s', label='Landing', zorder=10)
            
            # Ground plane (transparent)
            x_range = max(abs(x.max()), abs(x.min())) if len(x) > 0 else 50
            y_range = max(abs(y.max()), abs(y.min())) if len(y) > 0 else 20
            xx, yy = np.meshgrid(
                np.linspace(-x_range*0.1, x_range*1.1, 10),
                np.linspace(-y_range*1.2, y_range*1.2, 10)
            )
            zz = np.zeros_like(xx)
            self.ax.plot_surface(xx, yy, zz, alpha=0.1, color=current_colors.BORDER_HOVER)
            
            # Set labels and title
            self.ax.set_xlabel('Distance (yds)', color=current_colors.TEXT_PRIMARY)
            self.ax.set_ylabel('Lateral (yds)', color=current_colors.TEXT_PRIMARY)
            self.ax.set_zlabel('Height (yds)', color=current_colors.TEXT_PRIMARY)
            self.ax.set_title('3D Ball Flight Trajectory', color=current_colors.TEXT_PRIMARY, fontsize=14, fontweight='bold')
            
            # Set dark theme colors
            self.ax.xaxis.pane.fill = False
            self.ax.yaxis.pane.fill = False
            self.ax.zaxis.pane.fill = False
            self.ax.xaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
            self.ax.yaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
            self.ax.zaxis.pane.set_edgecolor(current_colors.BORDER_HOVER)
            self.ax.xaxis.label.set_color(current_colors.TEXT_PRIMARY)
            self.ax.yaxis.label.set_color(current_colors.TEXT_PRIMARY)
            self.ax.zaxis.label.set_color(current_colors.TEXT_PRIMARY)
            self.ax.tick_params(colors=current_colors.TEXT_PRIMARY)
            
            # Legend
            self.ax.legend(loc='upper left', facecolor=current_colors.BACKGROUND_SURFACE_ELEVATED, edgecolor=current_colors.BORDER_HOVER, 
                          labelcolor=current_colors.TEXT_PRIMARY, fontsize=9)
            
            # Update info label
            carry = trajectory['carry_distance']
            max_h = trajectory['max_height']
            flight_time = trajectory['flight_time']
            self.info_label.setText(
                f"Carry: {carry:.1f} yds | Max Height: {max_h:.1f} yds | Flight Time: {flight_time:.2f}s"
            )
            
            self.canvas.draw()
            
        except Exception as e:
            logger.error("Error calculating trajectory: %s", e, exc_info=True)
            self.ax.clear()
            self.ax.text2D(0.5, 0.5, f'Error calculating trajectory: {str(e)}', 
                          ha='center', va='center', transform=self.ax.transAxes,
                          color=current_colors.ACCENT, fontsize=12)
            self.canvas.draw()
            self.info_label.setText("Error calculating trajectory")
    
    def _reset_view(self) -> None:
        """Reset the 3D view to default."""
        if self.shot_combo.count() == 0:
            return
        
        shot: ShotModel = self.shot_combo.currentData()
        if not shot or not (shot.ball_speed and shot.launch_angle and shot.spin_rate):
            return
        
        try:
            trajectory = calculate_trajectory_points(
                ball_speed=shot.ball_speed,
                launch_angle=shot.launch_angle,
                spin_rate=shot.spin_rate,
                launch_direction=shot.launch_direction,
                side_spin=shot.side_spin,
            )
            
            x = trajectory['x']
            y = trajectory['y']
            z = trajectory['z']
            
            # Check for valid data
            if len(x) == 0 or len(y) == 0 or len(z) == 0:
                return
            
            # Check for NaN or inf values
            if not np.isfinite(x).any() or not np.isfinite(y).any() or not np.isfinite(z).any():
                return
            
            # Calculate ranges with safety checks
            x_range = float(x.max() - x.min()) if len(x) > 0 and np.isfinite(x.max()) and np.isfinite(x.min()) else 100
            y_range = float(y.max() - y.min()) if len(y) > 0 and np.isfinite(y.max()) and np.isfinite(y.min()) else 50
            z_range = float(z.max() - z.min()) if len(z) > 0 and np.isfinite(z.max()) and np.isfinite(z.min()) else 50
            
            max_range = max(x_range, y_range, z_range)
            if not np.isfinite(max_range) or max_range <= 0:
                max_range = 100
            
            mid_x = float((x.max() + x.min()) / 2) if len(x) > 0 and np.isfinite(x.max()) and np.isfinite(x.min()) else 0
            mid_y = float((y.max() + y.min()) / 2) if len(y) > 0 and np.isfinite(y.max()) and np.isfinite(y.min()) else 0
            mid_z = float((z.max() + z.min()) / 2) if len(z) > 0 and np.isfinite(z.max()) and np.isfinite(z.min()) else 0
            
            # Ensure all values are finite before setting limits
            if np.isfinite(mid_x) and np.isfinite(max_range):
                self.ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
            if np.isfinite(mid_y) and np.isfinite(max_range):
                self.ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
            if np.isfinite(max_range):
                self.ax.set_zlim(0, max_range)
            
            # Reset view angle
            self.ax.view_init(elev=20, azim=45)
            
            self.canvas.draw()
            
        except Exception as e:
            logger.error("Error resetting view: %s", e, exc_info=True)


class Trajectory3DDialog(QDialog):
    """Dialog wrapper for 3D trajectory visualization."""
    
    def __init__(self, shots: list[ShotModel], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setWindowTitle("3D Ball Flight Trajectory")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        layout.setSpacing(SPACING.SMALL)
        
        self.trajectory_widget = Trajectory3DWidget(self)
        self.trajectory_widget.set_shots(shots)
        layout.addWidget(self.trajectory_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)


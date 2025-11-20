"""Analysis dashboard for viewing trends and statistics with charts."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.session_manager import SessionManager, SessionModel, ShotModel

logger = logging.getLogger(__name__)


class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding charts."""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=current_colors.BACKGROUND_BASE)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(int(height * dpi))
        
        self.fig.patch.set_facecolor(current_colors.BACKGROUND_BASE)
        self.ax = self.fig.add_subplot(111, facecolor=current_colors.BACKGROUND_BASE)
        self.ax.tick_params(colors=current_colors.TEXT_PRIMARY)
        self.ax.spines['bottom'].set_color(current_colors.BORDER_HOVER)
        self.ax.spines['top'].set_color(current_colors.BORDER_HOVER)
        self.ax.spines['right'].set_color(current_colors.BORDER_HOVER)
        self.ax.spines['left'].set_color(current_colors.BORDER_HOVER)
        self.ax.xaxis.label.set_color(current_colors.TEXT_PRIMARY)
        self.ax.yaxis.label.set_color(current_colors.TEXT_PRIMARY)
        self.ax.title.set_color(current_colors.TEXT_PRIMARY)
        
        self.fig.set_tight_layout(True)


class AnalysisDashboard(QDialog):
    """Dashboard showing trends and statistics across sessions with charts."""

    def __init__(self, session_manager: SessionManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session_manager = session_manager
        self.setWindowTitle("Analysis Dashboard")
        self.setMinimumSize(1000, 600)  # More flexible for smaller screens
        self.resize(1400, 900)  # Smaller default size
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        self._build_ui()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._load_data)

    def _build_ui(self) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)

        # Filter controls - responsive layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(SPACING.SMALL)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        period_label = QLabel("Period:")
        period_label.setAutoFillBackground(True)
        period_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        period_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        filter_layout.addWidget(period_label)
        
        combo_style = f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """
        
        self.period_combo = QComboBox()
        self.period_combo.blockSignals(True)
        self.period_combo.addItems([
            "Today",
            "Last 3 Days",
            "Last 7 Days",
            "Last 30 Days",
            "Last 90 Days",
            "Custom Range...",
            "All Time"
        ])
        self.period_combo.setStyleSheet(combo_style)
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        self.period_combo.blockSignals(False)
        self.period_combo.setMinimumWidth(140)
        self.period_combo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        filter_layout.addWidget(self.period_combo)
        
        self.custom_date_start: Optional[datetime] = None
        self.custom_date_end: Optional[datetime] = None
        self.current_shots: list[ShotModel] = []
        
        club_label = QLabel("Club:")
        club_label.setAutoFillBackground(True)
        club_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        club_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        filter_layout.addWidget(club_label)
        
        self.club_combo = QComboBox()
        self.club_combo.blockSignals(True)
        self.club_combo.addItem("All Clubs", None)
        self.club_combo.setStyleSheet(combo_style)
        self.club_combo.currentIndexChanged.connect(self._load_data)
        self.club_combo.blockSignals(False)
        self.club_combo.setMinimumWidth(120)
        self.club_combo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        filter_layout.addWidget(self.club_combo)
        
        filter_layout.addStretch()
        
        customize_btn = QPushButton("Customize Charts")
        customize_btn.setMinimumHeight(28)
        customize_btn.setMaximumHeight(36)
        customize_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        customize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: 4px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        customize_btn.clicked.connect(self._customize_charts)
        filter_layout.addWidget(customize_btn)
        
        self.export_charts_combo = QComboBox()
        self.export_charts_combo.blockSignals(True)
        self.export_charts_combo.addItems(["Export Charts", "PNG", "SVG"])
        self.export_charts_combo.setCurrentIndex(0)
        self.export_charts_combo.setMinimumHeight(28)
        self.export_charts_combo.setMaximumHeight(36)
        self.export_charts_combo.setMinimumWidth(140)
        self.export_charts_combo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.export_charts_combo.setStyleSheet(combo_style)
        self.export_charts_combo.currentIndexChanged.connect(self._export_charts)
        self.export_charts_combo.blockSignals(False)
        filter_layout.addWidget(self.export_charts_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setMinimumHeight(28)
        refresh_btn.setMaximumHeight(36)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: 4px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-weight: 500;
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)
        
        self.export_data_combo = QComboBox()
        self.export_data_combo.blockSignals(True)
        self.export_data_combo.addItems(["Export Data", "CSV", "Excel"])
        self.export_data_combo.setCurrentIndex(0)
        self.export_data_combo.setMinimumHeight(28)
        self.export_data_combo.setMaximumHeight(36)
        self.export_data_combo.setMinimumWidth(140)
        self.export_data_combo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.export_data_combo.setStyleSheet(combo_style)
        self.export_data_combo.currentIndexChanged.connect(self._export_data)
        self.export_data_combo.blockSignals(False)
        filter_layout.addWidget(self.export_data_combo)
        
        report_btn = QPushButton("Build Report")
        report_btn.setMinimumHeight(28)
        report_btn.setMaximumHeight(36)
        report_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        report_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 4px 10px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        report_btn.clicked.connect(self._open_report_builder)
        filter_layout.addWidget(report_btn)
        
        layout.addLayout(filter_layout)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {current_colors.BORDER_DEFAULT};
                background-color: {current_colors.BACKGROUND_BASE};
            }}
            QTabBar::tab {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {current_colors.BACKGROUND_BASE};
                color: {current_colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        
        # Trends tab with charts - wrapped in scroll area
        trends_scroll = QScrollArea()
        trends_scroll.setWidgetResizable(True)
        trends_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        trends_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        trends_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        trends_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {current_colors.BACKGROUND_BASE};
            }}
            QScrollBar:vertical {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
            QScrollBar:horizontal {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        
        trends_tab = QWidget()
        trends_layout = QVBoxLayout(trends_tab)
        trends_layout.setSpacing(SPACING.MEDIUM)
        trends_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        trends_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)
        
        self.summary_widget = QWidget()
        self.summary_widget.setObjectName("summaryStatsWidget")
        self.summary_widget.setStyleSheet(f"""
            #summaryStatsWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.SMALL + SPACING.XS}px;
            }}
        """)
        self.summary_widget.setMinimumHeight(70)
        self.summary_widget.setMaximumHeight(90)
        self.summary_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.summary_widget.setVisible(True)
        
        summary_layout = QHBoxLayout(self.summary_widget)
        summary_layout.setSpacing(SPACING.LARGE)
        summary_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        self.stats_labels = {}
        for metric in ["Total Shots", "Avg Club Speed", "Avg Ball Speed", "Avg Carry", "Max Carry", "Consistency"]:
            container = QWidget()
            container.setMinimumWidth(100)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(SPACING.XS)
            container_layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel(metric)
            label.setAutoFillBackground(True)
            label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: 500; padding: 0px; margin: 0px;")
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            container_layout.addWidget(label)
            
            value_label = QLabel("--")
            value_label.setObjectName(f"statValue_{metric.replace(' ', '_')}")
            value_label.setAutoFillBackground(True)
            value_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {current_colors.BACKGROUND_BASE};
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.H3}px;
                    font-weight: 700;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            value_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            container_layout.addWidget(value_label)
            
            self.stats_labels[metric] = value_label
            summary_layout.addWidget(container)
        
        summary_layout.addStretch()
        trends_layout.addWidget(self.summary_widget)
        
        charts_grid = QGridLayout()
        charts_grid.setSpacing(SPACING.MEDIUM)
        
        self.speed_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.speed_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.speed_canvas.setMinimumHeight(200)
        charts_grid.addWidget(self.speed_canvas, 0, 0)
        
        self.distance_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.distance_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.distance_canvas.setMinimumHeight(200)
        charts_grid.addWidget(self.distance_canvas, 0, 1)
        
        self.spin_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.spin_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.spin_canvas.setMinimumHeight(200)
        charts_grid.addWidget(self.spin_canvas, 1, 0)
        
        dispersion_container = QWidget()
        dispersion_layout = QVBoxLayout(dispersion_container)
        dispersion_layout.setContentsMargins(0, 0, 0, 0)
        dispersion_layout.setSpacing(SPACING.XS)
        
        heat_map_controls = QHBoxLayout()
        heat_map_controls.setContentsMargins(0, 0, 0, 0)
        
        heat_map_label = QLabel("Dispersion View:")
        heat_map_label.setAutoFillBackground(True)
        heat_map_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        heat_map_controls.addWidget(heat_map_label)
        
        self.heat_map_mode_combo = QComboBox()
        self.heat_map_mode_combo.blockSignals(True)
        self.heat_map_mode_combo.addItems(["Heat Map", "Scatter Plot", "Contour Map"])
        self.heat_map_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.heat_map_mode_combo.currentTextChanged.connect(self._load_data)
        self.heat_map_mode_combo.blockSignals(False)
        heat_map_controls.addWidget(self.heat_map_mode_combo)
        heat_map_controls.addStretch()
        
        dispersion_layout.addLayout(heat_map_controls)
        
        self.dispersion_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.dispersion_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.dispersion_canvas.setMinimumHeight(200)
        dispersion_layout.addWidget(self.dispersion_canvas)
        
        charts_grid.addWidget(dispersion_container, 1, 1)
        
        trends_layout.addLayout(charts_grid)
        
        advanced_label = QLabel("Advanced Analytics")
        advanced_label.setAutoFillBackground(True)
        advanced_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: {SPACING.SMALL}px; margin-top: {SPACING.MEDIUM}px; margin-bottom: 0px;")
        trends_layout.addWidget(advanced_label)
        
        advanced_widget = QWidget()
        advanced_widget.setObjectName("advancedAnalyticsWidget")
        advanced_widget.setStyleSheet(f"""
            #advancedAnalyticsWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.MEDIUM}px;
            }}
        """)
        advanced_layout = QGridLayout(advanced_widget)
        advanced_layout.setSpacing(SPACING.MEDIUM)
        advanced_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        # Tempo Ratio Card
        tempo_card = QWidget()
        tempo_card.setObjectName("tempoCard")
        tempo_card.setStyleSheet(f"""
            #tempoCard {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
        """)
        tempo_layout = QVBoxLayout(tempo_card)
        tempo_layout.setSpacing(SPACING.XS)
        tempo_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        tempo_title = QLabel("Tempo Ratio")
        tempo_title.setAutoFillBackground(True)
        tempo_title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: 500; padding: 0px; margin: 0px;")
        tempo_layout.addWidget(tempo_title)
        
        self.tempo_label = QLabel("--")
        self.tempo_label.setAutoFillBackground(True)
        self.tempo_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: 700; padding: 0px; margin: 0px;")
        tempo_layout.addWidget(self.tempo_label)
        
        tempo_desc = QLabel("Backswing/Downswing")
        tempo_desc.setAutoFillBackground(True)
        tempo_desc.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        tempo_layout.addWidget(tempo_desc)
        
        advanced_layout.addWidget(tempo_card, 0, 0)
        
        # Swing Plane Card
        swing_plane_card = QWidget()
        swing_plane_card.setObjectName("swingPlaneCard")
        swing_plane_card.setStyleSheet(f"""
            #swingPlaneCard {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
        """)
        swing_plane_layout = QVBoxLayout(swing_plane_card)
        swing_plane_layout.setSpacing(SPACING.XS)
        swing_plane_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        swing_plane_title = QLabel("Swing Plane")
        swing_plane_title.setAutoFillBackground(True)
        swing_plane_title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: 500; padding: 0px; margin: 0px;")
        swing_plane_layout.addWidget(swing_plane_title)
        
        self.swing_plane_label = QLabel("--")
        self.swing_plane_label.setAutoFillBackground(True)
        self.swing_plane_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: 700; padding: 0px; margin: 0px;")
        swing_plane_layout.addWidget(self.swing_plane_label)
        
        swing_plane_desc = QLabel("Estimated Angle")
        swing_plane_desc.setAutoFillBackground(True)
        swing_plane_desc.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        swing_plane_layout.addWidget(swing_plane_desc)
        
        advanced_layout.addWidget(swing_plane_card, 0, 1)
        
        # Ball Flight Prediction Card
        ball_flight_card = QWidget()
        ball_flight_card.setObjectName("ballFlightCard")
        ball_flight_card.setStyleSheet(f"""
            #ballFlightCard {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
            }}
        """)
        ball_flight_layout = QVBoxLayout(ball_flight_card)
        ball_flight_layout.setSpacing(SPACING.XS)
        ball_flight_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        ball_flight_title = QLabel("Ball Flight Prediction")
        ball_flight_title.setAutoFillBackground(True)
        ball_flight_title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: 500; padding: 0px; margin: 0px;")
        ball_flight_layout.addWidget(ball_flight_title)
        
        self.ball_flight_label = QLabel("--")
        self.ball_flight_label.setAutoFillBackground(True)
        self.ball_flight_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: 600; padding: 0px; margin: 0px;")
        ball_flight_layout.addWidget(self.ball_flight_label)
        
        ball_flight_desc = QLabel("Carry, Total, Height")
        ball_flight_desc.setAutoFillBackground(True)
        ball_flight_desc.setStyleSheet(f"background-color: {current_colors.BACKGROUND_CONTROL}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0px; margin: 0px;")
        ball_flight_layout.addWidget(ball_flight_desc)
        
        advanced_layout.addWidget(ball_flight_card, 0, 2)
        
        trends_layout.addWidget(advanced_widget)
        
        club_comp_label = QLabel("Club Comparison")
        club_comp_label.setAutoFillBackground(True)
        club_comp_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: {SPACING.SMALL}px; margin: 0px;")
        trends_layout.addWidget(club_comp_label)
        
        self.club_canvas = MplCanvas(trends_tab, width=12, height=4)
        self.club_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.club_canvas.setMinimumHeight(300)
        trends_layout.addWidget(self.club_canvas)
        
        additional_charts_label = QLabel("Distribution Analysis")
        additional_charts_label.setAutoFillBackground(True)
        additional_charts_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: {SPACING.SMALL}px; margin-top: {SPACING.MEDIUM}px; margin-bottom: 0px;")
        trends_layout.addWidget(additional_charts_label)
        
        additional_charts_grid = QGridLayout()
        additional_charts_grid.setSpacing(SPACING.MEDIUM)
        
        self.histogram_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.histogram_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.histogram_canvas.setMinimumHeight(200)
        additional_charts_grid.addWidget(self.histogram_canvas, 0, 0)
        
        self.boxplot_canvas = MplCanvas(trends_tab, width=6, height=3)
        self.boxplot_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.boxplot_canvas.setMinimumHeight(200)
        additional_charts_grid.addWidget(self.boxplot_canvas, 0, 1)
        
        additional_charts_widget = QWidget()
        additional_charts_widget.setLayout(additional_charts_grid)
        trends_layout.addWidget(additional_charts_widget)
        
        self.chart_settings = {
            "colors": {
                "primary": current_colors.ACCENT,
                "secondary": current_colors.SUCCESS,
                "grid": current_colors.BORDER_HOVER,
                "text": current_colors.TEXT_PRIMARY,
            },
            "show_grid": True,
            "show_legend": True,
            "marker_size": 4,
            "line_width": 2,
        }
        
        trends_tab.setLayout(trends_layout)
        trends_scroll.setWidget(trends_tab)
        tabs.addTab(trends_scroll, "Charts & Trends")
        
        data_scroll = QScrollArea()
        data_scroll.setWidgetResizable(True)
        data_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        data_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        data_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        data_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {current_colors.BACKGROUND_BASE};
            }}
            QScrollBar:vertical {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
            QScrollBar:horizontal {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        data_layout.setSpacing(SPACING.MEDIUM)
        data_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)
        
        trends_label = QLabel("Shot Data")
        trends_label.setAutoFillBackground(True)
        trends_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; font-weight: 600; padding: {SPACING.SMALL}px; margin: 0px;")
        data_layout.addWidget(trends_label)
        
        from app.widgets.enhanced_table import FilterableTableWidget
        
        self.trends_table_widget = FilterableTableWidget(
            columns=["Date", "Club", "Club Speed", "Ball Speed", "Spin", "Carry", "Total", "Smash"],
            filterable_columns=list(range(8)),
            table_id="analysis_trends_table",
        )
        self.trends_table = self.trends_table_widget.table
        
        self.trends_table.setSortingEnabled(True)
        self.trends_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.trends_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        header = self.trends_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        
        self.trends_table_widget.set_column_widths([140, 100, 110, 110, 80, 100, 100, 80])
        
        data_layout.addWidget(self.trends_table_widget)
        
        data_tab.setLayout(data_layout)
        data_scroll.setWidget(data_tab)
        tabs.addTab(data_scroll, "Data Table")
        
        layout.addWidget(tabs, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        from app.style_helpers import style_button
        close_btn.setStyleSheet(style_button(variant="secondary"))
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)

    def _load_data(self) -> None:
        """Load and display analysis data with charts."""
        from sqlalchemy.orm import Session
        
        try:
            if not hasattr(self, 'stats_labels') or not self.stats_labels:
                logger.warning("Stats labels not initialized yet, skipping data load")
                return
            
            period_text = self.period_combo.currentText()
            cutoff_start = None
            cutoff_end = None
            
            if period_text == "Today":
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_start = today_start
                cutoff_end = datetime.now()
            elif period_text == "Last 3 Days":
                cutoff_start = datetime.now() - timedelta(days=3)
            elif period_text == "Last 7 Days":
                cutoff_start = datetime.now() - timedelta(days=7)
            elif period_text == "Last 30 Days":
                cutoff_start = datetime.now() - timedelta(days=30)
            elif period_text == "Last 90 Days":
                cutoff_start = datetime.now() - timedelta(days=90)
            elif period_text == "Custom Range..." or period_text.startswith("Custom:"):
                if self.custom_date_start and self.custom_date_end:
                    cutoff_start = self.custom_date_start
                    cutoff_end = self.custom_date_end
                else:
                    logger.warning("Custom date range not set, showing all time")
            
            club_filter = self.club_combo.currentData()
            
            session_map = {}
            with Session(self.session_manager.engine) as session:
                query = session.query(ShotModel).join(SessionModel)
                
                if cutoff_start:
                    query = query.filter(SessionModel.started_at >= cutoff_start)
                if cutoff_end:
                    query = query.filter(SessionModel.started_at <= cutoff_end.replace(hour=23, minute=59, second=59))
                
                if club_filter:
                    query = query.filter(SessionModel.club == club_filter)
                
                shots = query.order_by(ShotModel.recorded_at).all()
                
                for shot in shots:
                    if shot.session_id not in session_map:
                        sess = session.get(SessionModel, shot.session_id)
                        session_map[shot.session_id] = sess.club if sess and sess.club else "Unknown"
            
            logger.debug("Loaded %d shots for analysis dashboard", len(shots))
            
            if shots:
                club_speeds = [s.club_speed for s in shots if s.club_speed]
                ball_speeds = [s.ball_speed for s in shots if s.ball_speed]
                carries = [s.carry_distance for s in shots if s.carry_distance]
                spins = [s.spin_rate for s in shots if s.spin_rate]
                
                self.stats_labels["Total Shots"].setText(str(len(shots)))
                self.stats_labels["Avg Club Speed"].setText(f"{sum(club_speeds)/len(club_speeds):.1f}" if club_speeds else "--")
                self.stats_labels["Avg Ball Speed"].setText(f"{sum(ball_speeds)/len(ball_speeds):.1f}" if ball_speeds else "--")
                self.stats_labels["Avg Carry"].setText(f"{sum(carries)/len(carries):.1f}" if carries else "--")
                self.stats_labels["Max Carry"].setText(f"{max(carries):.1f}" if carries else "--")
                
                if len(carries) > 1:
                    from core.analytics import calculate_consistency_metrics
                    consistency = calculate_consistency_metrics(carries)
                    std_dev = consistency.get("std_dev", 0)
                    self.stats_labels["Consistency"].setText(f"±{std_dev:.1f} yds")
                else:
                    self.stats_labels["Consistency"].setText("--")
                
                logger.debug("Updated stats labels: Total=%d, Avg Club Speed=%s, Avg Carry=%s", 
                           len(shots), 
                           self.stats_labels["Avg Club Speed"].text(),
                           self.stats_labels["Avg Carry"].text())
                
                if hasattr(self, 'summary_widget'):
                    self.summary_widget.update()
                    self.summary_widget.repaint()
                
                self._display_advanced_analytics(shots)
            else:
                for label in self.stats_labels.values():
                    label.setText("--")
                logger.debug("No shots found, reset stats labels to '--'")
                
                if hasattr(self, 'summary_widget'):
                    self.summary_widget.update()
                    self.summary_widget.repaint()
            
            self._update_charts(shots)
            
            self.trends_table_widget.clear()
            for shot in shots[-100:]:
                club_name = session_map.get(shot.session_id, "Unknown")
                
                self.trends_table_widget.add_row([
                    shot.recorded_at.strftime("%Y-%m-%d %H:%M"),
                    club_name,
                    f"{shot.club_speed:.1f}" if shot.club_speed else "--",
                    f"{shot.ball_speed:.1f}" if shot.ball_speed else "--",
                    f"{shot.spin_rate:.0f}" if shot.spin_rate else "--",
                    f"{shot.carry_distance:.1f}" if shot.carry_distance else "--",
                    f"{shot.total_distance:.1f}" if shot.total_distance else "--",
                    f"{shot.smash_factor:.2f}" if shot.smash_factor else "--",
                ])
            
            self._update_club_options()
            self.current_shots = shots
            
        except Exception as e:
            logger.error("Error loading analysis data: %s", e, exc_info=True)
    
    def _display_advanced_analytics(self, shots: list[ShotModel]) -> None:
        """Display advanced analytics metrics with aggregate statistics."""
        from core.analytics import (
            calculate_tempo_ratio,
            estimate_swing_plane_angle,
            predict_ball_flight,
            calculate_consistency_metrics,
        )
        
        if not shots:
            self.tempo_label.setText("--")
            self.swing_plane_label.setText("--")
            self.ball_flight_label.setText("--")
            return
        
        # Tempo Ratio - calculate for shots with timing data, show average
        tempo_ratios = []
        for shot in shots:
            if hasattr(shot, 'backswing_time') and hasattr(shot, 'downswing_time'):
                tempo = calculate_tempo_ratio(
                    getattr(shot, 'backswing_time', None),
                    getattr(shot, 'downswing_time', None),
                )
                if tempo:
                    tempo_ratios.append(tempo)
        
        if tempo_ratios:
            tempo_metrics = calculate_consistency_metrics(tempo_ratios)
            avg_tempo = tempo_metrics["mean"]
            if len(tempo_ratios) > 1:
                self.tempo_label.setText(f"{avg_tempo:.2f} (avg)")
                self.tempo_label.setToolTip(f"Average tempo ratio from {len(tempo_ratios)} shots\nRange: {tempo_metrics['min']:.2f} - {tempo_metrics['max']:.2f}")
            else:
                self.tempo_label.setText(f"{avg_tempo:.2f}")
                self.tempo_label.setToolTip("Backswing/Downswing ratio")
        else:
            self.tempo_label.setText("--")
            self.tempo_label.setToolTip("Requires video analysis (backswing/downswing timing)")
        
        # Swing Plane - calculate for shots with path data, show average
        swing_planes = []
        for shot in shots:
            if shot.club_path is not None and shot.attack_angle is not None:
                plane = estimate_swing_plane_angle(shot.club_path, shot.attack_angle)
                if plane:
                    swing_planes.append(plane)
        
        if swing_planes:
            plane_metrics = calculate_consistency_metrics(swing_planes)
            avg_plane = plane_metrics["mean"]
            if len(swing_planes) > 1:
                self.swing_plane_label.setText(f"{avg_plane:.1f}° (avg)")
                self.swing_plane_label.setToolTip(f"Average swing plane from {len(swing_planes)} shots\nRange: {plane_metrics['min']:.1f}° - {plane_metrics['max']:.1f}°")
            else:
                self.swing_plane_label.setText(f"{avg_plane:.1f}°")
                self.swing_plane_label.setToolTip("Estimated swing plane angle")
        else:
            self.swing_plane_label.setText("--")
            self.swing_plane_label.setToolTip("Requires club path & attack angle data")
        
        # Ball Flight Prediction - show average prediction
        predictions = []
        for shot in shots:
            if shot.ball_speed and shot.launch_angle and shot.spin_rate:
                prediction = predict_ball_flight(
                    ball_speed=shot.ball_speed,
                    launch_angle=shot.launch_angle,
                    spin_rate=shot.spin_rate,
                    launch_direction=shot.launch_direction,
                )
                if prediction:
                    predictions.append(prediction)
        
        if predictions:
            avg_carry = sum(p.get("carry_distance", 0) for p in predictions) / len(predictions)
            avg_total = sum(p.get("total_distance", 0) for p in predictions) / len(predictions)
            avg_height = sum(p.get("max_height", 0) for p in predictions) / len(predictions)
            
            if len(predictions) > 1:
                self.ball_flight_label.setText(
                    f"{avg_carry:.0f} yds carry (avg)\n{avg_total:.0f} yds total (avg)\n{avg_height:.0f} yds height (avg)"
                )
                self.ball_flight_label.setToolTip(f"Average ball flight prediction from {len(predictions)} shots")
            else:
                self.ball_flight_label.setText(
                    f"{avg_carry:.0f} yds carry\n{avg_total:.0f} yds total\n{avg_height:.0f} yds height"
                )
                self.ball_flight_label.setToolTip("Predicted ball flight")
        else:
            self.ball_flight_label.setText("--")
            self.ball_flight_label.setToolTip("Requires ball speed, launch angle, and spin rate")

    def _update_charts(self, shots: list[ShotModel]) -> None:
        """Update all charts with shot data."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        if not shots:
            return
        
        from sqlalchemy.orm import Session
        
        with Session(self.session_manager.engine) as session:
            session_map = {}
            for shot in shots:
                if shot.session_id not in session_map:
                    sess = session.get(SessionModel, shot.session_id)
                    session_map[shot.session_id] = sess.club if sess and sess.club else "Unknown"
        
        self.speed_canvas.ax.clear()
        dates = [s.recorded_at for s in shots if s.club_speed and s.ball_speed]
        club_speeds = [s.club_speed for s in shots if s.club_speed and s.ball_speed]
        ball_speeds = [s.ball_speed for s in shots if s.club_speed and s.ball_speed]
        
        if dates:
            colors = self.chart_settings['colors']
            marker_size = self.chart_settings['marker_size']
            line_width = self.chart_settings['line_width']
            
            self.speed_canvas.ax.plot(dates, club_speeds, 'o-', color=colors['primary'], label='Club Speed', 
                                    linewidth=line_width, markersize=marker_size, alpha=0.6)
            self.speed_canvas.ax.plot(dates, [b/1.5 for b in ball_speeds], 's-', color=colors['secondary'], 
                                    label='Ball Speed/1.5', linewidth=line_width, markersize=marker_size, alpha=0.6)
            
            # Add moving averages (7-shot window)
            if len(club_speeds) >= 7:
                window = 7
                ma_club = np.convolve(club_speeds, np.ones(window)/window, mode='valid')
                ma_dates = dates[window-1:]
                self.speed_canvas.ax.plot(ma_dates, ma_club, '-', color=colors['primary'], 
                                        label=f'Club Speed MA ({window})', linewidth=line_width+1, alpha=0.9)
                
                ma_ball = np.convolve([b/1.5 for b in ball_speeds], np.ones(window)/window, mode='valid')
                self.speed_canvas.ax.plot(ma_dates, ma_ball, '-', color=colors['secondary'], 
                                        label=f'Ball Speed MA ({window})', linewidth=line_width+1, alpha=0.9)
            self.speed_canvas.ax.set_xlabel('Date', color=colors['text'])
            self.speed_canvas.ax.set_ylabel('Speed (mph)', color=colors['text'])
            self.speed_canvas.ax.set_title('Speed Trends', color=colors['text'], fontsize=12, fontweight='bold')
            
            if self.chart_settings['show_legend']:
                self.speed_canvas.ax.legend(loc='best', facecolor=current_colors.BACKGROUND_SURFACE, edgecolor=current_colors.BORDER_DEFAULT, labelcolor=colors['text'])
            
            if self.chart_settings['show_grid']:
                self.speed_canvas.ax.grid(True, alpha=0.2, color=colors['grid'])
        self.speed_canvas.draw()
        
        # Distance trend
        self.distance_canvas.ax.clear()
        dates_dist = [s.recorded_at for s in shots if s.carry_distance]
        carries = [s.carry_distance for s in shots if s.carry_distance]
        totals = [s.total_distance for s in shots if s.carry_distance and s.total_distance]
        
        if dates_dist:
            colors = self.chart_settings['colors']
            marker_size = self.chart_settings['marker_size']
            line_width = self.chart_settings['line_width']
            
            self.distance_canvas.ax.plot(dates_dist, carries, 'o-', color=colors['primary'], label='Carry', 
                                       linewidth=line_width, markersize=marker_size, alpha=0.6)
            if totals:
                self.distance_canvas.ax.plot(dates_dist, totals, 's-', color=colors['secondary'], label='Total', 
                                           linewidth=line_width, markersize=marker_size, alpha=0.6)
            
            # Add moving averages (7-shot window)
            if len(carries) >= 7:
                window = 7
                ma_carry = np.convolve(carries, np.ones(window)/window, mode='valid')
                ma_dates_dist = dates_dist[window-1:]
                self.distance_canvas.ax.plot(ma_dates_dist, ma_carry, '-', color=colors['primary'], 
                                            label=f'Carry MA ({window})', linewidth=line_width+1, alpha=0.9)
                
                if totals and len(totals) >= 7:
                    ma_total = np.convolve(totals, np.ones(window)/window, mode='valid')
                    self.distance_canvas.ax.plot(ma_dates_dist, ma_total, '-', color=colors['secondary'], 
                                                label=f'Total MA ({window})', linewidth=line_width+1, alpha=0.9)
            self.distance_canvas.ax.set_xlabel('Date', color=colors['text'])
            self.distance_canvas.ax.set_ylabel('Distance (yds)', color=colors['text'])
            self.distance_canvas.ax.set_title('Distance Trends', color=colors['text'], fontsize=12, fontweight='bold')
            
            if self.chart_settings['show_legend']:
                self.distance_canvas.ax.legend(loc='best', facecolor=current_colors.BACKGROUND_SURFACE, edgecolor=current_colors.BORDER_DEFAULT, labelcolor=colors['text'])
            
            if self.chart_settings['show_grid']:
                self.distance_canvas.ax.grid(True, alpha=0.2, color=colors['grid'])
        self.distance_canvas.draw()
        
        self.spin_canvas.ax.clear()
        dates_spin = [s.recorded_at for s in shots if s.spin_rate]
        spins = [s.spin_rate for s in shots if s.spin_rate]
        
        if dates_spin:
            colors = self.chart_settings['colors']
            marker_size = self.chart_settings['marker_size']
            line_width = self.chart_settings['line_width']
            
            self.spin_canvas.ax.plot(dates_spin, spins, 'o-', color=colors['primary'], 
                                    linewidth=line_width, markersize=marker_size)
            self.spin_canvas.ax.set_xlabel('Date', color=colors['text'])
            self.spin_canvas.ax.set_ylabel('Spin Rate (rpm)', color=colors['text'])
            self.spin_canvas.ax.set_title('Spin Rate Trends', color=colors['text'], fontsize=12, fontweight='bold')
            
            if self.chart_settings['show_grid']:
                self.spin_canvas.ax.grid(True, alpha=0.2, color=colors['grid'])
        self.spin_canvas.draw()
        
        self.dispersion_canvas.ax.clear()
        carries_disp = [s.carry_distance for s in shots if s.carry_distance and (s.launch_direction or s.side_spin)]
        directions = [s.launch_direction if s.launch_direction else (s.side_spin/100 if s.side_spin else 0) 
                     for s in shots if s.carry_distance and (s.launch_direction or s.side_spin)]
        
        if carries_disp and directions:
            colors = self.chart_settings['colors']
            marker_size = self.chart_settings['marker_size']
            
            view_mode = self.heat_map_mode_combo.currentText()
            is_heat_map = view_mode == "Heat Map"
            is_contour = view_mode == "Contour Map"
            
            if (is_heat_map or is_contour) and len(carries_disp) >= 3:
                x_range = max(directions) - min(directions) if directions else 50
                y_range = max(carries_disp) - min(carries_disp) if carries_disp else 100
                
                x_bins = max(20, min(50, int(x_range / 2)))
                y_bins = max(20, min(50, int(y_range / 5)))
                
                H, xedges, yedges = np.histogram2d(directions, carries_disp, bins=[x_bins, y_bins])
                
                try:
                    from scipy.ndimage import gaussian_filter
                    H = gaussian_filter(H, sigma=1.0)
                except ImportError:
                    pass
                
                X, Y = np.meshgrid(xedges[:-1], yedges[:-1])
                
                if is_contour:
                    # Contour map with filled contours
                    contour = self.dispersion_canvas.ax.contourf(X, Y, H.T, levels=15, cmap='YlOrRd', alpha=0.8)
                    contour_lines = self.dispersion_canvas.ax.contour(X, Y, H.T, levels=10, colors='black', alpha=0.3, linewidths=0.5)
                    cbar = self.dispersion_canvas.fig.colorbar(contour, ax=self.dispersion_canvas.ax)
                    cbar.set_label('Shot Density', color=colors['text'], fontsize=10)
                    cbar.ax.tick_params(colors=colors['text'])
                else:
                    # Heat map with pcolormesh
                    im = self.dispersion_canvas.ax.pcolormesh(X, Y, H.T, cmap='YlOrRd', shading='gouraud', alpha=0.8)
                    cbar = self.dispersion_canvas.fig.colorbar(im, ax=self.dispersion_canvas.ax)
                    cbar.set_label('Shot Density', color=colors['text'], fontsize=10)
                    cbar.ax.tick_params(colors=colors['text'])
                
                # Overlay actual shot points
                self.dispersion_canvas.ax.scatter(directions, carries_disp, c='white', s=marker_size*3, 
                                                 alpha=0.3, edgecolors='none', zorder=10)
            else:
                scatter = self.dispersion_canvas.ax.scatter(directions, carries_disp, c=range(len(carries_disp)), 
                                                           cmap='RdYlGn', s=marker_size*10, alpha=0.7, 
                                                           edgecolors=colors['grid'])
            
            self.dispersion_canvas.ax.axvline(0, color=colors['grid'], linestyle='--', linewidth=1, alpha=0.5)
            mean_carry = np.mean(carries_disp) if carries_disp else 0
            self.dispersion_canvas.ax.axhline(mean_carry, color=colors['grid'], linestyle='--', linewidth=1, alpha=0.5)
            
            mean_dir = np.mean(directions) if directions else 0
            self.dispersion_canvas.ax.plot(mean_dir, mean_carry, 'o', color=colors['primary'], 
                                          markersize=10, markeredgecolor='white', markeredgewidth=2, 
                                          label='Mean', zorder=20)
            
            self.dispersion_canvas.ax.set_xlabel('Launch Direction / Side Spin (degrees)', color=colors['text'])
            self.dispersion_canvas.ax.set_ylabel('Carry Distance (yds)', color=colors['text'])
            if is_heat_map:
                title = 'Shot Dispersion Heat Map'
            elif is_contour:
                title = 'Shot Dispersion Contour Map'
            else:
                title = 'Shot Dispersion'
            self.dispersion_canvas.ax.set_title(title, color=colors['text'], fontsize=12, fontweight='bold')
            
            if self.chart_settings['show_grid']:
                self.dispersion_canvas.ax.grid(True, alpha=0.2, color=colors['grid'])
            
            if self.chart_settings['show_legend'] and not is_heat_map:
                self.dispersion_canvas.ax.legend(loc='upper right', facecolor=current_colors.BACKGROUND_SURFACE, 
                                               edgecolor=current_colors.BORDER_DEFAULT, labelcolor=colors['text'], fontsize=9)
        else:
            colors = self.chart_settings['colors']
            self.dispersion_canvas.ax.text(0.5, 0.5, 'No dispersion data available', 
                                         ha='center', va='center', transform=self.dispersion_canvas.ax.transAxes,
                                         color=colors['text'], fontsize=12)
            self.dispersion_canvas.ax.set_xlabel('Launch Direction / Side Spin', color=colors['text'])
            self.dispersion_canvas.ax.set_ylabel('Carry Distance (yds)', color=colors['text'])
            self.dispersion_canvas.ax.set_title('Shot Dispersion', color=colors['text'], fontsize=12, fontweight='bold')
        
        self.dispersion_canvas.draw()
        
        self.club_canvas.ax.clear()
        club_stats = {}
        for shot in shots:
            club = session_map.get(shot.session_id, "Unknown")
            if club not in club_stats:
                club_stats[club] = {"carries": [], "speeds": []}
            if shot.carry_distance:
                club_stats[club]["carries"].append(shot.carry_distance)
            if shot.club_speed:
                club_stats[club]["speeds"].append(shot.club_speed)
        
        if club_stats:
            clubs = list(club_stats.keys())
            avg_carries = [np.mean(club_stats[c]["carries"]) if club_stats[c]["carries"] else 0 for c in clubs]
            avg_speeds = [np.mean(club_stats[c]["speeds"]) if club_stats[c]["speeds"] else 0 for c in clubs]
            
            x = np.arange(len(clubs))
            width = 0.35
            
            ax1 = self.club_canvas.ax
            ax2 = ax1.twinx()
            
            colors = self.chart_settings['colors']
            
            bars1 = ax1.bar(x - width/2, avg_carries, width, label='Avg Carry', color=colors['primary'], alpha=0.8)
            bars2 = ax2.bar(x + width/2, avg_speeds, width, label='Avg Club Speed', color=colors['secondary'], alpha=0.8)
            
            ax1.set_xlabel('Club', color=colors['text'])
            ax1.set_ylabel('Carry Distance (yds)', color=colors['text'])
            ax2.set_ylabel('Club Speed (mph)', color=colors['text'])
            ax1.set_title('Club Comparison', color=colors['text'], fontsize=12, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(clubs, color=colors['text'])
            ax1.tick_params(colors=colors['text'])
            ax2.tick_params(colors=colors['text'])
            
            if self.chart_settings['show_grid']:
                ax1.grid(True, alpha=0.2, color=colors['grid'])
            
            if self.chart_settings['show_legend']:
                ax1.legend(loc='upper left', facecolor=current_colors.BACKGROUND_SURFACE, edgecolor=current_colors.BORDER_DEFAULT, labelcolor=colors['text'])
                ax2.legend(loc='upper right', facecolor=current_colors.BACKGROUND_SURFACE, edgecolor=current_colors.BORDER_DEFAULT, labelcolor=colors['text'])
        self.club_canvas.draw()
        
        self.histogram_canvas.ax.clear()
        carries_hist = [s.carry_distance for s in shots if s.carry_distance]
        if carries_hist:
            colors_hist = self.chart_settings['colors']
            self.histogram_canvas.ax.hist(carries_hist, bins=20, color=colors_hist['primary'], 
                                         alpha=0.7, edgecolor=colors_hist['grid'], linewidth=1)
            self.histogram_canvas.ax.set_xlabel('Carry Distance (yds)', color=colors_hist['text'])
            self.histogram_canvas.ax.set_ylabel('Frequency', color=colors_hist['text'])
            self.histogram_canvas.ax.set_title('Carry Distance Distribution', color=colors_hist['text'], 
                                              fontsize=12, fontweight='bold')
            if self.chart_settings['show_grid']:
                self.histogram_canvas.ax.grid(True, alpha=0.2, color=colors_hist['grid'])
        self.histogram_canvas.draw()
        
        self.boxplot_canvas.ax.clear()
        club_speeds_dict = {}
        for shot in shots:
            club = session_map.get(shot.session_id, "Unknown")
            if shot.club_speed:
                if club not in club_speeds_dict:
                    club_speeds_dict[club] = []
                club_speeds_dict[club].append(shot.club_speed)
        
        if club_speeds_dict:
            colors_box = self.chart_settings['colors']
            clubs_list = list(club_speeds_dict.keys())
            speeds_list = [club_speeds_dict[club] for club in clubs_list]
            
            bp = self.boxplot_canvas.ax.boxplot(speeds_list, labels=clubs_list, patch_artist=True,
                                               boxprops=dict(facecolor=colors_box['primary'], alpha=0.7),
                                               medianprops=dict(color=colors_box['secondary'], linewidth=2),
                                               whiskerprops=dict(color=colors_box['grid']),
                                               capprops=dict(color=colors_box['grid']))
            
            self.boxplot_canvas.ax.set_xlabel('Club', color=colors_box['text'])
            self.boxplot_canvas.ax.set_ylabel('Club Speed (mph)', color=colors_box['text'])
            self.boxplot_canvas.ax.set_title('Club Speed Distribution by Club', color=colors_box['text'], 
                                            fontsize=12, fontweight='bold')
            if self.chart_settings['show_grid']:
                self.boxplot_canvas.ax.grid(True, alpha=0.2, color=colors_box['grid'], axis='y')
        self.boxplot_canvas.draw()

    def _update_club_options(self) -> None:
        """Update club filter combo with available clubs."""
        from sqlalchemy.orm import Session
        
        try:
            with Session(self.session_manager.engine) as session:
                clubs = session.query(SessionModel.club).distinct().filter(SessionModel.club.isnot(None)).all()
                current_club = self.club_combo.currentData()
                
                self.club_combo.blockSignals(True)
                self.club_combo.clear()
                self.club_combo.addItem("All Clubs", None)
                
                for (club,) in clubs:
                    if club:
                        self.club_combo.addItem(club, club)
                
                if current_club:
                    idx = self.club_combo.findData(current_club)
                    if idx >= 0:
                        self.club_combo.setCurrentIndex(idx)
                
                self.club_combo.blockSignals(False)
        except Exception as e:
            logger.error("Error updating club options: %s", e, exc_info=True)
    
    def _customize_charts(self) -> None:
        """Open chart customization dialog."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog, QCheckBox, QSpinBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Customize Charts")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        color_layout = QHBoxLayout()
        color_label = QLabel("Primary Color:")
        color_label.setAutoFillBackground(True)
        color_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: 0px; margin: 0px;")
        color_layout.addWidget(color_label)
        
        primary_color_btn = QPushButton()
        primary_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.chart_settings['colors']['primary']};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 4px;
                min-width: 60px;
                min-height: 24px;
            }}
        """)
        primary_color_btn.clicked.connect(lambda: self._pick_color(primary_color_btn, 'primary'))
        color_layout.addWidget(primary_color_btn)
        
        secondary_color_btn = QPushButton()
        secondary_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.chart_settings['colors']['secondary']};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 4px;
                min-width: 60px;
                min-height: 24px;
            }}
        """)
        secondary_color_btn.clicked.connect(lambda: self._pick_color(secondary_color_btn, 'secondary'))
        color_layout.addWidget(secondary_color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        show_grid_check = QCheckBox("Show Grid")
        show_grid_check.setChecked(self.chart_settings['show_grid'])
        show_grid_check.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px;")
        layout.addWidget(show_grid_check)
        
        show_legend_check = QCheckBox("Show Legend")
        show_legend_check.setChecked(self.chart_settings['show_legend'])
        show_legend_check.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px;")
        layout.addWidget(show_legend_check)
        
        marker_layout = QHBoxLayout()
        marker_label = QLabel("Marker Size:")
        marker_label.setAutoFillBackground(True)
        marker_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: 0px; margin: 0px;")
        marker_layout.addWidget(marker_label)
        
        marker_spin = QSpinBox()
        marker_spin.setMinimum(1)
        marker_spin.setMaximum(20)
        marker_spin.setValue(self.chart_settings['marker_size'])
        marker_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
            }}
        """)
        marker_layout.addWidget(marker_spin)
        marker_layout.addStretch()
        layout.addLayout(marker_layout)
        
        layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.chart_settings['show_grid'] = show_grid_check.isChecked()
            self.chart_settings['show_legend'] = show_legend_check.isChecked()
            self.chart_settings['marker_size'] = marker_spin.value()
            self._load_data()
    
    def _on_period_changed(self, text: str) -> None:
        """Handle period combo box changes."""
        if text == "Custom Range..." or text.startswith("Custom:"):
            if text.startswith("Custom:") and self.custom_date_start and self.custom_date_end:
                self._open_date_range_dialog()
            else:
                self._open_date_range_dialog()
        else:
            self._load_data()
    
    def _open_date_range_dialog(self) -> None:
        """Open dialog to select custom date range."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date Range")
        dialog.setMinimumSize(400, 200)
        dialog.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        start_layout = QHBoxLayout()
        start_label = QLabel("From:")
        start_label.setAutoFillBackground(True)
        start_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; min-width: 60px; padding: 0px; margin: 0px;")
        start_layout.addWidget(start_label)
        
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate().addDays(-7))
        start_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QDateEdit:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QCalendarWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QCalendarWidget QTableView {{
                selection-background-color: {current_colors.ACCENT};
            }}
        """)
        start_layout.addWidget(start_date)
        start_layout.addStretch()
        layout.addLayout(start_layout)
        
        end_layout = QHBoxLayout()
        end_label = QLabel("To:")
        end_label.setAutoFillBackground(True)
        end_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.SMALL}px; min-width: 60px; padding: 0px; margin: 0px;")
        end_layout.addWidget(end_label)
        
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDate(QDate.currentDate())
        end_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QDateEdit:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QCalendarWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QCalendarWidget QTableView {{
                selection-background-color: {current_colors.ACCENT};
            }}
        """)
        end_layout.addWidget(end_date)
        end_layout.addStretch()
        layout.addLayout(end_layout)
        
        if self.custom_date_start:
            start_date.setDate(QDate.fromString(
                self.custom_date_start.strftime("%Y-%m-%d"), 
                "yyyy-MM-dd"
            ))
        if self.custom_date_end:
            end_date.setDate(QDate.fromString(
                self.custom_date_end.strftime("%Y-%m-%d"), 
                "yyyy-MM-dd"
            ))
        
        layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            start_qdate = start_date.date()
            end_qdate = end_date.date()
            
            self.custom_date_start = datetime(
                start_qdate.year(), 
                start_qdate.month(), 
                start_qdate.day(), 
                0, 0, 0
            )
            self.custom_date_end = datetime(
                end_qdate.year(), 
                end_qdate.month(), 
                end_qdate.day(), 
                23, 59, 59
            )
            
            start_str = start_qdate.toString("MMM d, yyyy")
            end_str = end_qdate.toString("MMM d, yyyy")
            self.period_combo.blockSignals(True)
            idx = self.period_combo.findText("Custom Range...")
            if idx >= 0:
                self.period_combo.setItemText(idx, f"Custom: {start_str} - {end_str}")
            self.period_combo.blockSignals(False)
            self._load_data()
    
    def _export_charts(self, index: int) -> None:
        """Export all charts as images."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        if index == 0:
            return
        
        from pathlib import Path
        
        ext = "png" if index == 1 else "svg"
        dpi = 300 if ext == "png" else None
        
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save Charts",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not output_dir:
            self.export_charts_combo.blockSignals(True)
            self.export_charts_combo.setCurrentIndex(0)
            self.export_charts_combo.blockSignals(False)
            return
        
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        charts = [
            ("speed_trend", self.speed_canvas, "Speed Trends"),
            ("distance_trend", self.distance_canvas, "Distance Trends"),
            ("spin_trend", self.spin_canvas, "Spin Rate Trends"),
            ("dispersion", self.dispersion_canvas, "Shot Dispersion"),
            ("club_comparison", self.club_canvas, "Club Comparison"),
        ]
        
        saved_count = 0
        for chart_id, canvas, title in charts:
            try:
                filename = f"{chart_id}_{timestamp}.{ext}"
                filepath = output_path / filename
                canvas.fig.savefig(
                    str(filepath),
                    format=ext,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor=current_colors.BACKGROUND_BASE,
                    edgecolor='none'
                )
                saved_count += 1
                logger.info("Exported chart %s to %s", title, filepath)
            except Exception as e:
                logger.error("Error exporting chart %s: %s", title, e, exc_info=True)
        
        self.export_charts_combo.blockSignals(True)
        self.export_charts_combo.setCurrentIndex(0)
        self.export_charts_combo.blockSignals(False)
        
        if saved_count > 0:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {saved_count} chart(s) to:\n{output_path}"
            )
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                "Failed to export charts. Check logs for details."
            )
    
    def _export_data(self, index: int) -> None:
        """Export filtered shot data to CSV or Excel."""
        if index == 0:
            return
        
        if not self.current_shots:
            QMessageBox.warning(
                self,
                "No Data",
                "No shot data available to export. Please load data first."
            )
            self.export_data_combo.blockSignals(True)
            self.export_data_combo.setCurrentIndex(0)
            self.export_data_combo.blockSignals(False)
            return
        
        is_excel = index == 2
        ext = "xlsx" if is_excel else "csv"
        
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"shots_export_{timestamp}.{ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Shot Data",
            str(Path.home() / default_name),
            f"{ext.upper()} Files (*.{ext})"
        )
        
        if not file_path:
            self.export_data_combo.blockSignals(True)
            self.export_data_combo.setCurrentIndex(0)
            self.export_data_combo.blockSignals(False)
            return
        
        output_path = Path(file_path)
        
        try:
            if is_excel:
                try:
                    import pandas as pd
                    
                    rows = []
                    for shot in self.current_shots:
                        row = {
                            "Date": shot.recorded_at.strftime("%Y-%m-%d"),
                            "Time": shot.recorded_at.strftime("%H:%M:%S"),
                            "Club Speed (mph)": shot.club_speed,
                            "Ball Speed (mph)": shot.ball_speed,
                            "Launch Angle (deg)": shot.launch_angle,
                            "Spin Rate (rpm)": shot.spin_rate,
                            "Carry Distance (yds)": shot.carry_distance,
                            "Total Distance (yds)": shot.total_distance,
                            "Side Spin (rpm)": shot.side_spin,
                            "Back Spin (rpm)": shot.back_spin,
                            "Launch Direction (deg)": shot.launch_direction,
                            "Apex Height (yds)": shot.apex_height,
                            "Descent Angle (deg)": shot.descent_angle,
                            "Smash Factor": shot.smash_factor,
                            "Dynamic Loft (deg)": shot.dynamic_loft,
                            "Attack Angle (deg)": shot.attack_angle,
                            "Club Path (deg)": shot.club_path,
                            "Face Angle (deg)": shot.face_angle,
                            "Notes": shot.notes or "",
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    df.to_excel(output_path, index=False, engine='openpyxl')
                    logger.info("Exported %d shots to Excel: %s", len(self.current_shots), output_path)
                    
                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Excel Export Unavailable",
                        "Excel export requires pandas and openpyxl.\n"
                        "Install with: pip install pandas openpyxl\n\n"
                        "Falling back to CSV export."
                    )
                    is_excel = False
                    output_path = output_path.with_suffix('.csv')
            
            if not is_excel:
                import csv
                from sqlalchemy.orm import Session
                
                session_map = {}
                with Session(self.session_manager.engine) as session:
                    for shot in self.current_shots:
                        if shot.session_id not in session_map:
                            sess = session.get(SessionModel, shot.session_id)
                            session_map[shot.session_id] = sess.club if sess and sess.club else "Unknown"
                
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    headers = [
                        "Date", "Time", "Club", "Club Speed (mph)", "Ball Speed (mph)",
                        "Launch Angle (deg)", "Spin Rate (rpm)", "Carry Distance (yds)",
                        "Total Distance (yds)", "Side Spin (rpm)", "Back Spin (rpm)",
                        "Launch Direction (deg)", "Apex Height (yds)", "Descent Angle (deg)",
                        "Smash Factor", "Dynamic Loft (deg)", "Attack Angle (deg)",
                        "Club Path (deg)", "Face Angle (deg)", "Notes"
                    ]
                    writer.writerow(headers)
                    
                    for shot in self.current_shots:
                        club_name = session_map.get(shot.session_id, "Unknown")
                        row = [
                            shot.recorded_at.strftime("%Y-%m-%d"),
                            shot.recorded_at.strftime("%H:%M:%S"),
                            club_name,
                            shot.club_speed or "",
                            shot.ball_speed or "",
                            shot.launch_angle or "",
                            shot.spin_rate or "",
                            shot.carry_distance or "",
                            shot.total_distance or "",
                            shot.side_spin or "",
                            shot.back_spin or "",
                            shot.launch_direction or "",
                            shot.apex_height or "",
                            shot.descent_angle or "",
                            shot.smash_factor or "",
                            shot.dynamic_loft or "",
                            shot.attack_angle or "",
                            shot.club_path or "",
                            shot.face_angle or "",
                            shot.notes or "",
                        ]
                        writer.writerow(row)
                
                logger.info("Exported %d shots to CSV: %s", len(self.current_shots), output_path)
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(self.current_shots)} shot(s) to:\n{output_path}"
            )
            
        except Exception as e:
            logger.error("Error exporting data: %s", e, exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export data:\n{str(e)}"
            )
        finally:
            self.export_data_combo.blockSignals(True)
            self.export_data_combo.setCurrentIndex(0)
            self.export_data_combo.blockSignals(False)
    
    def _pick_color(self, button: QPushButton, color_key: str) -> None:
        """Pick a color for chart customization."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        current_color = QColor(self.chart_settings['colors'][color_key])
        color = QColorDialog.getColor(current_color, self, f"Select {color_key.title()} Color")
        if color.isValid():
            self.chart_settings['colors'][color_key] = color.name()
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    min-width: 60px;
                    min-height: 24px;
                }}
            """)
    
    def _open_report_builder(self) -> None:
        """Open report builder dialog."""
        from app.widgets.report_builder_dialog import ReportBuilderDialog
        
        dialog = ReportBuilderDialog(self.session_manager, self)
        dialog.exec()
    
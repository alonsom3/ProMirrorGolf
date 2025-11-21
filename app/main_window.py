from __future__ import annotations

import datetime as dt
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QShortcut, QAction, QKeySequence, QIcon, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.buffer import CircularBuffer
from core.camera_service import CameraService, detect_cameras
from core.config import ConfigManager
from core.session_manager import SessionManager

from .theme import get_current_theme
from .design_constants import COLORS, SPACING, TYPOGRAPHY, SIZES
from .style_helpers import style_button, style_input, style_label
from .widgets.camera_view import CameraView
from .widgets.import_dialog import ImportDialog
from .widgets.session_browser import SessionBrowser
from .widgets.settings_dialog import SettingsDialog
from .widgets.shot_review_window import ShotReviewWindow
from .widgets.video_player import VideoPlayer

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        camera_service: CameraService,
        session_manager: SessionManager,
        shot_callback: callable[[dict], None],
        buffer_seconds: int,
        fps: int,
        clips_dir: str,
        config: ConfigManager,
    ) -> None:
        super().__init__()
        self.setWindowTitle("ProMirrorGolf")
        self.setMinimumSize(1200, 700)
        self.camera_service = camera_service
        self.session_manager = session_manager
        self.shot_callback = shot_callback
        self.config = config
        self.current_session_name: Optional[str] = None
        self.current_session_id: Optional[int] = None
        self.buffer_frames = max(buffer_seconds * fps, fps)
        self.dtl_buffer = CircularBuffer(self.buffer_frames)
        self.face_buffer = CircularBuffer(self.buffer_frames)
        self.clips_dir = Path(clips_dir)
        self.fps = fps
        self._clip_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="clip-writer")
        self._session_browser = None
        self._stacked_widget = None
        self._current_view_index = 0  # 0 = main session view
        self._view_widgets = {}  # Store view widgets
        from core.layout_manager import LayoutManager
        self.layout_manager = LayoutManager(Path("data/layouts.json"))
        self._main_splitter = None  # Will be set in _build_ui
        self._bridge_status_widget = None  # Bridge status indicator
        self._club_options = [
            "Driver",
            "3 Wood",
            "5 Wood",
            "2 Hybrid",
            "3 Hybrid",
            "4 Hybrid",
            "4 Iron",
            "5 Iron",
            "6 Iron",
            "7 Iron",
            "8 Iron",
            "9 Iron",
            "Pitching Wedge",
            "Gap Wedge",
            "Sand Wedge",
            "Lob Wedge",
            "Putter",
        ]

        self._apply_theme()
        self._build_ui()
        self._wire_signals()
        self._setup_shortcuts()
        self._setup_context_menus()
        self._apply_multi_monitor_layout()
        # Load saved layout after UI is built
        self._load_saved_layout()

    def _apply_theme(self) -> None:
        """Apply dark theme with explicit color settings."""
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setStyleSheet(get_current_theme())
    
    def _apply_multi_monitor_layout(self) -> None:
        """Apply optimal multi-monitor layout."""
        try:
            from core.multi_monitor import get_optimal_window_rect
            rect = get_optimal_window_rect(self, "main", 0)
            self.setGeometry(rect)
        except Exception as e:
            logger.debug("Error applying multi-monitor layout: %s", e)

    def _build_ui(self) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        # Create menu bar
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
                border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
                padding: {SPACING.XS}px;
            }}
            QMenuBar::item {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QMenuBar::item:selected {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QMenu {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
                border: 1px solid {current_colors.BORDER_HOVER};
                padding: {SPACING.XS}px;
            }}
            QMenu::item {{
                padding: {SPACING.SMALL}px {SPACING.LARGE}px {SPACING.SMALL}px {SPACING.MEDIUM}px;
            }}
            QMenu::item:selected {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
        """)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import Data...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._open_import_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        duplicate_action = QAction("Find Duplicates...", self)
        duplicate_action.triggered.connect(self._find_duplicates)
        file_menu.addAction(duplicate_action)
        
        # Main splitter for sidebar + content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter = main_splitter  # Store for layout management
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        # Left sidebar navigation
        sidebar = QWidget()
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Navigation list (no header, just icons)
        nav_list = QListWidget()
        nav_list.setSpacing(SPACING.XS)
        nav_list.setStyleSheet(f"""
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
        
        # Navigation items with icons (Unicode symbols)
        nav_items = [
            ("🏠", "Recording", 0, self._show_main_session),
            ("📊", "Sessions", 1, self._show_session_browser),
            ("📈", "Analysis", 2, self._show_analysis),
            ("⚖️", "Compare", 3, self._show_comparison),
            ("🎯", "Goals", 4, self._show_goals),
            ("🏋️", "Practice Drills", 5, self._show_practice_drills),
            ("🕐", "Recent Shots", 6, self._show_recent_shots),
            ("🖼️", "Thumbnails", 7, self._show_thumbnail_grid),
            ("🎬", "View Clips", 8, self._show_clips_viewer),
            ("⚙️", "Settings", 9, self._show_settings),
            ("❓", "Help", 10, self._show_help),
        ]
        
        # Create icon font for better rendering
        icon_font = QFont()
        icon_font.setPointSize(12)  # Reduced from 16 to make buttons smaller
        
        for icon, text, view_index, handler in nav_items:
            item = QListWidgetItem(f"{icon} {text}")
            item.setFont(icon_font)
            item.setData(Qt.ItemDataRole.UserRole, view_index)
            nav_list.addItem(item)
        
        def on_nav_clicked(item: QListWidgetItem) -> None:
            view_index = item.data(Qt.ItemDataRole.UserRole)
            if view_index is not None:
                # Find handler
                for _, _, idx, handler in nav_items:
                    if idx == view_index:
                        handler()
                        nav_list.setCurrentItem(item)
                        break
        
        nav_list.itemClicked.connect(on_nav_clicked)
        
        sidebar_layout.addWidget(nav_list, 1)
        main_splitter.addWidget(sidebar)
        main_splitter.setStretchFactor(0, 0)
        
        # Main content area
        central = QWidget()
        central.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(SPACING.PANEL_PADDING_H, SPACING.PANEL_PADDING_V, SPACING.PANEL_PADDING_H, SPACING.PANEL_PADDING_V)
        layout.setSpacing(SPACING.SECTION_SPACING)
        
        # Add empty state label for shot table (initially hidden)
        self.shot_table_empty_label = QLabel("No shots recorded yet.\nStart a session and capture shots to see them here.")
        self.shot_table_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shot_table_empty_label.setAutoFillBackground(True)
        self.shot_table_empty_label.setStyleSheet(f"""
            QLabel {{
                background-color: {current_colors.BACKGROUND_BASE};
                color: {current_colors.TEXT_SECONDARY};
                font-size: {TYPOGRAPHY.H3}px;
                padding: {SPACING.XXL}px {SPACING.LARGE}px;
                margin: 0px;
            }}
        """)
        self.shot_table_empty_label.hide()

        # Top control container
        control_container = QWidget()
        control_container.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
        """)
        control_bar = QVBoxLayout(control_container)
        control_bar.setContentsMargins(SPACING.PANEL_PADDING_H, SPACING.PANEL_PADDING_V, SPACING.PANEL_PADDING_H, SPACING.PANEL_PADDING_V)
        control_bar.setSpacing(SPACING.FORM_FIELD_SPACING)
        
        self.session_label = QLabel("Session: Not Started")
        self.session_label.setAutoFillBackground(True)
        self.session_label.setStyleSheet(style_label(size=TYPOGRAPHY.H2, weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_SURFACE}; color: {current_colors.TEXT_PRIMARY}; padding: 0px; margin: 0px;")
        
        # Compact toolbar buttons
        self.start_btn = QPushButton("Start")
        self.start_btn.setToolTip("Start a new recording session")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setToolTip("Stop the current session")
        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)
        self.save_btn.setToolTip("Manually save the last captured clip")
        self.test_shot_btn = QPushButton("Test")
        self.test_shot_btn.setEnabled(False)
        self.test_shot_btn.setToolTip("Simulate a shot detection to test auto-recording")
        self.test_shot_btn.clicked.connect(self._test_shot)
        
        # Style compact buttons
        compact_buttons = [self.start_btn, self.stop_btn, self.save_btn, self.test_shot_btn]
        for btn in compact_buttons:
            btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
            btn.setMaximumHeight(SIZES.BUTTON_MIN_HEIGHT)
            btn.setMinimumWidth(60)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {current_colors.BACKGROUND_SURFACE};
                    border: 1px solid {current_colors.BORDER_DEFAULT};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.SMALL}px;
                    font-weight: {TYPOGRAPHY.MEDIUM};
                }}
                QPushButton:hover {{
                    background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                    border-color: {current_colors.BORDER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {current_colors.BORDER_DEFAULT};
                }}
            """)
        
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.ACCENT};
                border: none;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                color: {current_colors.WHITE_TEXT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.DANGER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                color: {current_colors.DANGER_TEXT};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.DANGER_HOVER};
                color: {current_colors.WHITE_TEXT};
            }}
        """)

        details_row = QHBoxLayout()
        details_row.setSpacing(SPACING.SMALL)
        details_row.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel("Name")
        name_label.setAutoFillBackground(True)
        name_label.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.SMALL, weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: 0px; margin: 0px;")
        details_row.addWidget(name_label)

        self.session_name_edit = QLineEdit()
        self.session_name_edit.setPlaceholderText("Session name")
        self.session_name_edit.editingFinished.connect(self._persist_session_details)
        self.session_name_edit.setStyleSheet(style_input())
        details_row.addWidget(self.session_name_edit, 2)

        club_label = QLabel("Club")
        club_label.setAutoFillBackground(True)
        club_label.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.SMALL, weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: 0px; margin: 0px;")
        details_row.addWidget(club_label)

        self.session_club_combo = QComboBox()
        self.session_club_combo.setEditable(True)
        self.session_club_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.session_club_combo.addItems(self._club_options)
        self.session_club_combo.setCurrentIndex(-1)
        self.session_club_combo.setPlaceholderText("Club (optional)")
        self.session_club_combo.lineEdit().editingFinished.connect(self._persist_session_details)
        self.session_club_combo.currentIndexChanged.connect(self._persist_session_details)
        self.session_club_combo.setStyleSheet(style_input())
        details_row.addWidget(self.session_club_combo, 1)

        notes_label = QLabel("Notes")
        notes_label.setAutoFillBackground(True)
        notes_label.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.SMALL, weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: 0px; margin: 0px;")
        details_row.addWidget(notes_label)

        self.session_notes_edit = QLineEdit()
        self.session_notes_edit.setPlaceholderText("Notes (optional)")
        self.session_notes_edit.editingFinished.connect(self._persist_session_details)
        self.session_notes_edit.setStyleSheet(style_input())
        
        # Notes template button
        from PyQt6.QtWidgets import QToolButton
        notes_template_btn = QToolButton()
        notes_template_btn.setText("📝")
        notes_template_btn.setToolTip("Load notes template")
        notes_template_btn.setFixedSize(32, 32)
        notes_template_btn.clicked.connect(self._load_notes_template)
        details_row.addWidget(self.session_notes_edit, 2)
        details_row.addWidget(notes_template_btn)
        
        # Compact toolbar
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(SPACING.SMALL)
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.addWidget(self.start_btn)
        toolbar_row.addWidget(self.stop_btn)
        toolbar_row.addWidget(self.save_btn)
        toolbar_row.addWidget(self.test_shot_btn)
        toolbar_row.addStretch()
        
        # Web Dashboard button (top right)
        self.web_dashboard_btn = QPushButton("🌐 Web Dashboard")
        self.web_dashboard_btn.setToolTip("Open web dashboard in browser")
        self.web_dashboard_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
        self.web_dashboard_btn.setMaximumHeight(SIZES.BUTTON_MIN_HEIGHT)
        self.web_dashboard_btn.setMinimumWidth(120)
        self.web_dashboard_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.web_dashboard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.web_dashboard_btn.clicked.connect(self._open_web_dashboard)
        self.web_dashboard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
        """)
        toolbar_row.addWidget(self.web_dashboard_btn)
        
        control_bar.addWidget(self.session_label)
        control_bar.addLayout(details_row)
        control_bar.addLayout(toolbar_row)
        layout.addWidget(control_container)

        # Camera views with responsive resizable splitter
        camera_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        camera_splitter.setChildrenCollapsible(False)
        camera_splitter.setHandleWidth(4)
        camera_splitter.setStyleSheet(f"""
            QSplitter {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        self.dtl_view = CameraView("Down the Line")
        self.face_view = CameraView("Face On")
        self.dtl_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.face_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        camera_splitter.addWidget(self.dtl_view)
        camera_splitter.addWidget(self.face_view)
        camera_splitter.setStretchFactor(0, 1)
        camera_splitter.setStretchFactor(1, 1)
        camera_splitter.setSizes([500, 500])  # Initial 50/50 split
        
        layout.addWidget(camera_splitter, 2)

        # Shots table with enhanced features
        from app.widgets.enhanced_table import FilterableTableWidget
        
        self.shot_table_widget = FilterableTableWidget(
            columns=["Time", "Club Speed", "Ball Speed", "Total Spin", "Tags", "Favorite"],
            filterable_columns=[0, 1, 2, 3, 4, 5],  # All columns filterable
            table_id="main_window_shots_table",
        )
        self.shot_table = self.shot_table_widget.table  # Keep reference for compatibility
        
        # Set column widths
        self.shot_table_widget.set_column_widths([120, 140, 140, 140, 150, 80])
        
        # Connect signals
        self.shot_table.itemDoubleClicked.connect(self._on_shot_double_clicked)
        self.shot_table.itemClicked.connect(self._on_shot_clicked)
        
        # Enable sorting
        self.shot_table.setSortingEnabled(True)
        
        # Make headers visible and clickable
        header = self.shot_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        
        # Enable scroll wheel
        self.shot_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.shot_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        self._update_table_columns()
        
        # Create container for table with empty state overlay
        table_container = QWidget()
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(0)
        table_container_layout.addWidget(self.shot_table_widget)
        table_container_layout.addWidget(self.shot_table_empty_label)
        
        layout.addWidget(table_container, 1)
        
        # Create stacked widget for views
        self._stacked_widget = QStackedWidget()
        self._stacked_widget.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
        
        # Add main session view (index 0)
        self._stacked_widget.addWidget(central)
        self._view_widgets[0] = central
        
        main_splitter.addWidget(self._stacked_widget)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([220, 1000])
        
        # Set central widget to splitter
        central_widget = QWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.setContentsMargins(0, 0, 0, 0)
        central_widget_layout.setSpacing(0)
        central_widget_layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)

        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-top: 1px solid {current_colors.BORDER_DEFAULT};
                color: {current_colors.TEXT_SECONDARY};
                font-size: {TYPOGRAPHY.SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
            }}
        """)
        self.status_bar.showMessage("Ready")
        
        # Add bridge status indicator if bridge is enabled
        if self.config.get("springbok_bridge.enabled", False):
            self._build_bridge_status_indicator()
    
    def _build_bridge_status_indicator(self) -> None:
        """Build bridge connection status indicator in status bar."""
        from app.design_constants import get_current_colors, TYPOGRAPHY, SPACING
        current_colors = get_current_colors()
        
        # Create container widget
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(SPACING.SMALL, 0, SPACING.SMALL, 0)
        status_layout.setSpacing(SPACING.SMALL)
        
        # Springbok status
        self._springbok_status_label = QLabel("Springbok: ●")
        self._springbok_status_label.setObjectName("springbokStatus")
        self._springbok_status_label.setToolTip("Springbok connector connection status")
        status_layout.addWidget(self._springbok_status_label)
        
        # GSPro status
        self._gspro_status_label = QLabel("GSPro: ●")
        self._gspro_status_label.setObjectName("gsproStatus")
        self._gspro_status_label.setToolTip("GSPro API Connect connection status")
        status_layout.addWidget(self._gspro_status_label)
        
        # Style the labels
        self._update_bridge_status_style(False, False)
        
        # Add to status bar (permanent widget on the right)
        self.status_bar.addPermanentWidget(status_container)
    
    def _update_bridge_status_style(self, springbok_connected: bool, gspro_connected: bool) -> None:
        """Update bridge status indicator styles."""
        from app.design_constants import get_current_colors, TYPOGRAPHY, SPACING
        current_colors = get_current_colors()
        
        if not hasattr(self, '_springbok_status_label') or not hasattr(self, '_gspro_status_label'):
            return
        
        # Springbok status
        springbok_color = current_colors.SUCCESS if springbok_connected else current_colors.TEXT_DISABLED
        self._springbok_status_label.setStyleSheet(f"""
            QLabel#springbokStatus {{
                color: {springbok_color};
                font-size: {TYPOGRAPHY.SMALL}px;
                padding: 0px {SPACING.XS}px;
            }}
        """)
        self._springbok_status_label.setText(f"Springbok: {'●' if springbok_connected else '○'}")
        self._springbok_status_label.setToolTip(
            "Springbok connector: Connected" if springbok_connected 
            else "Springbok connector: Not connected (waiting for Springbok to connect)"
        )
        
        # GSPro status
        gspro_color = current_colors.SUCCESS if gspro_connected else current_colors.TEXT_DISABLED
        self._gspro_status_label.setStyleSheet(f"""
            QLabel#gsproStatus {{
                color: {gspro_color};
                font-size: {TYPOGRAPHY.SMALL}px;
                padding: 0px {SPACING.XS}px;
            }}
        """)
        self._gspro_status_label.setText(f"GSPro: {'●' if gspro_connected else '○'}")
        self._gspro_status_label.setToolTip(
            "GSPro API Connect: Connected" if gspro_connected 
            else "GSPro API Connect: Not connected (make sure GSPro API Connect is running)"
        )
    
    def update_bridge_status(self, springbok_connected: bool, gspro_connected: bool) -> None:
        """Update bridge connection status (called from bridge thread).
        
        Args:
            springbok_connected: Whether Springbok connector is connected.
            gspro_connected: Whether GSPro API Connect is connected.
        """
        # Use QTimer.singleShot to update UI from background thread
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_bridge_status_style(springbok_connected, gspro_connected))

    def _persist_session_details(self) -> None:
        """Save session edits to database."""
        if not self.current_session_id:
            return

        name = self.session_name_edit.text().strip() or self.current_session_name or ""
        if not name:
            self.session_name_edit.setText(self.current_session_name or "")
            self.status_bar.showMessage("Session name cannot be blank.")
            return

        club_text = self.session_club_combo.currentText().strip()
        club = club_text or None
        notes = self.session_notes_edit.text().strip() or None

        if self.session_manager.update_session(self.current_session_id, name=name, club=club, notes=notes):
            self.current_session_name = name
            self.session_label.setText(f"Session: {self.current_session_name} (#{self.current_session_id})")
            self.status_bar.showMessage("Session details updated.", 2000)
            if self._session_browser:
                self._session_browser.refresh_sessions(self.current_session_id)
        else:
            self.status_bar.showMessage("Failed to update session details.")
    
    def _load_notes_template(self) -> None:
        """Load a notes template into the session notes field."""
        from core.session_notes_templates import NotesTemplateManager
        from pathlib import Path
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QDialogButtonBox
        
        templates_file = Path("data/notes_templates.json")
        template_manager = NotesTemplateManager(templates_file)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Notes Template")
        dialog.setMinimumSize(400, 300)
        dialog.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        label = QLabel("Select a template:")
        layout.addWidget(label)
        
        templates_list = QListWidget()
        for template in template_manager.get_all_templates():
            item = QListWidgetItem(f"{template.name} - {template.description}")
            item.setData(Qt.ItemDataRole.UserRole, template)
            templates_list.addItem(item)
        layout.addWidget(templates_list)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            current_item = templates_list.currentItem()
            if current_item:
                template = current_item.data(Qt.ItemDataRole.UserRole)
                if template:
                    self.session_notes_edit.setText(template.content)
                    self.status_bar.showMessage(f"Loaded template: {template.name}", 2000)
    
    def _wire_signals(self) -> None:
        self.start_btn.clicked.connect(self._start_session)
        self.stop_btn.clicked.connect(self._stop_session)
        self.save_btn.clicked.connect(self._save_clip)

        self.camera_service.dtl_frame.connect(lambda frame, _: self._update_camera(self.dtl_view, frame))
        self.camera_service.face_frame.connect(lambda frame, _: self._update_camera(self.face_view, frame))
        self.camera_service.dtl_status.connect(lambda ok, msg: self._camera_status("DTL", ok, msg))
        self.camera_service.face_status.connect(lambda ok, msg: self._camera_status("Face", ok, msg))
    
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common actions."""
        # Session controls
        QShortcut(QKeySequence("Ctrl+S"), self, self._start_session)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self._stop_session)
        
        # Quick tagging shortcuts (Ctrl+1-9 for common tags)
        self.quick_tag_shortcuts = {}
        common_tags = ["practice", "good", "bad", "slice", "hook", "long", "short", "favorite", "review"]
        for i, tag in enumerate(common_tags[:9], start=1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda checked, t=tag: self._quick_tag_selected_shot(t))
            self.quick_tag_shortcuts[tag] = shortcut
    
    def _quick_tag_selected_shot(self, tag: str) -> None:
        """Quick tag the currently selected shot."""
        current_row = self.shot_table.currentRow()
        if current_row >= 0:
            time_item = self.shot_table.item(current_row, 0)
            if time_item:
                shot_id = time_item.data(Qt.ItemDataRole.UserRole)
                if shot_id:
                    self._quick_tag_shot(shot_id, tag)
        
        # Navigation
        QShortcut(QKeySequence("Ctrl+B"), self, self._open_session_browser)
        QShortcut(QKeySequence("Ctrl+A"), self, self._open_analysis)
        QShortcut(QKeySequence("Ctrl+C"), self, self._open_comparison)
        QShortcut(QKeySequence("Ctrl+,"), self, self._open_settings)
        
        # Shot table shortcuts
        QShortcut(QKeySequence("Return"), self.shot_table, lambda: self._on_shot_double_clicked(self.shot_table.currentItem()) if self.shot_table.currentItem() else None)
        QShortcut(QKeySequence("Enter"), self.shot_table, lambda: self._on_shot_double_clicked(self.shot_table.currentItem()) if self.shot_table.currentItem() else None)
        QShortcut(QKeySequence("Delete"), self.shot_table, self._delete_selected_shots)
    
    def _setup_context_menus(self) -> None:
        """Set up context menus for tables."""
        self.shot_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.shot_table.customContextMenuRequested.connect(self._show_shot_table_context_menu)
    
    def _show_shot_table_context_menu(self, position) -> None:
        """Show context menu for shot table."""
        item = self.shot_table.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(get_current_theme())
        
        review_action = QAction("Review Shot", self)
        review_action.setShortcut(QKeySequence("Return"))
        review_action.triggered.connect(lambda: self._on_shot_double_clicked(item))
        menu.addAction(review_action)
        
        menu.addSeparator()
        
        row = item.row()
        shot_id_item = self.shot_table.item(row, 0)
        if shot_id_item:
            shot_id = shot_id_item.data(Qt.ItemDataRole.UserRole)
            if shot_id:
                # Get shot metadata
                import json
                from sqlalchemy.orm import Session
                from core.session_manager import ShotModel
                
                with Session(self.session_manager.engine) as session:
                    shot = session.get(ShotModel, shot_id)
                    if shot:
                        # Toggle favorite
                        favorite_action = QAction("Toggle Favorite", self)
                        favorite_action.setShortcut(QKeySequence("F"))
                        favorite_action.triggered.connect(lambda: self._toggle_shot_favorite(shot_id))
                        menu.addAction(favorite_action)
                        
                        tags_action = QAction("Edit Tags", self)
                        tags_action.setShortcut(QKeySequence("T"))
                        tags_action.triggered.connect(lambda: self._edit_shot_tags(shot_id))
                        menu.addAction(tags_action)
                        
                        notes_action = QAction("Edit Notes", self)
                        notes_action.setShortcut(QKeySequence("N"))
                        notes_action.triggered.connect(lambda: self._edit_shot_notes(shot_id))
                        menu.addAction(notes_action)
        
        menu.exec(self.shot_table.mapToGlobal(position))
    
    def _toggle_shot_favorite(self, shot_id: int) -> None:
        """Toggle favorite status for a shot."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        
        with Session(self.session_manager.engine) as session:
            shot = session.get(ShotModel, shot_id)
            if shot:
                new_status = not shot.is_favorite
                if self.session_manager.update_shot(shot_id, is_favorite=new_status):
                    current_row = self.shot_table.currentRow()
                    if current_row >= 0:
                        self._refresh_shot_row(current_row, shot_id)
                    self.status_bar.showMessage(f"Shot {'marked as' if new_status else 'removed from'} favorite", 2000)
    
    def _quick_tag_shot(self, shot_id: int, tag: str) -> None:
        """Quickly add a tag to a shot using keyboard shortcut.
        
        Args:
            shot_id: Shot ID
            tag: Tag to add
        """
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        import json
        
        with Session(self.session_manager.engine) as session:
            shot = session.get(ShotModel, shot_id)
            if shot:
                current_tags = json.loads(shot.tags) if shot.tags else []
                if tag not in current_tags:
                    current_tags.append(tag)
                    if self.session_manager.update_shot(shot_id, tags=json.dumps(current_tags)):
                        current_row = self.shot_table.currentRow()
                        if current_row >= 0:
                            self._refresh_shot_row(current_row, shot_id)
                        self.status_bar.showMessage(f"Tag '{tag}' added", 2000)
    
    def _edit_shot_tags(self, shot_id: int) -> None:
        """Edit tags for a shot."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        from core.tag_manager import TagManager
        from pathlib import Path
        from app.widgets.tag_edit_dialog import TagEditDialog
        import json
        
        with Session(self.session_manager.engine) as session:
            shot = session.get(ShotModel, shot_id)
            if shot:
                current_tags = json.loads(shot.tags) if shot.tags else []
                
                # Create tag manager
                tags_file = Path("data/tags.json")
                tag_manager = TagManager(tags_file, self.session_manager)
                
                dialog = TagEditDialog(tag_manager, current_tags, self)
                if dialog.exec() == dialog.DialogCode.Accepted:
                    new_tags = dialog.get_tags()
                    if self.session_manager.update_shot(shot_id, tags=new_tags):
                        current_row = self.shot_table.currentRow()
                        if current_row >= 0:
                            self._refresh_shot_row(current_row, shot_id)
                        self.status_bar.showMessage("Tags updated", 2000)
    
    def _edit_shot_notes(self, shot_id: int) -> None:
        """Edit notes for a shot."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        from PyQt6.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        
        with Session(self.session_manager.engine) as session:
            shot = session.get(ShotModel, shot_id)
            if shot:
                dialog = QDialog(self)
                dialog.setWindowTitle("Edit Shot Notes")
                dialog.setMinimumSize(500, 300)
                dialog.resize(600, 400)
                dialog.setStyleSheet(get_current_theme())
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
                layout.setSpacing(SPACING.MEDIUM)
                
                label = QLabel("Notes:")
                label.setAutoFillBackground(True)
                from app.design_constants import TYPOGRAPHY
                label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
                layout.addWidget(label)
                
                notes_edit = QPlainTextEdit()
                notes_edit.setPlainText(shot.notes or "")
                from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
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
                from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
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
                
                fields_file = Path("data/custom_fields.json")
                field_manager = CustomFieldManager(fields_file)
                custom_fields_form = CustomFieldsForm(field_manager, "shots", dialog)
                layout.addWidget(custom_fields_form)
                
                # Load existing custom fields
                if shot.custom_fields:
                    custom_fields_form.set_values(shot.custom_fields)
                
                layout.addLayout(buttons)
                
                if dialog.exec() == dialog.DialogCode.Accepted:
                    new_notes = notes_edit.toPlainText().strip() or None
                    # Get custom fields
                    from core.custom_fields import set_custom_fields_to_json
                    custom_fields_values = custom_fields_form.get_values()
                    custom_fields_json = set_custom_fields_to_json(custom_fields_values)
                    
                    if self.session_manager.update_shot(shot_id, notes=new_notes, custom_fields=custom_fields_json):
                        current_row = self.shot_table.currentRow()
                        if current_row >= 0:
                            self._refresh_shot_row(current_row, shot_id)
                        self.status_bar.showMessage("Notes updated", 2000)
    
    def _delete_selected_shots(self) -> None:
        """Delete selected shots."""
        selected_items = self.shot_table.selectedItems()
        if not selected_items:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        
        rows = set(item.row() for item in selected_items)
        shot_ids = []
        for row in rows:
            item = self.shot_table.item(row, 0)
            if item:
                shot_id = item.data(Qt.ItemDataRole.UserRole)
                if shot_id:
                    shot_ids.append(shot_id)
        
        if not shot_ids:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Shots",
            f"Are you sure you want to delete {len(shot_ids)} shot(s)?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from sqlalchemy.orm import Session
            from core.session_manager import ShotModel
            
            deleted = 0
            with Session(self.session_manager.engine) as session:
                for shot_id in shot_ids:
                    shot = session.get(ShotModel, shot_id)
                    if shot:
                        session.delete(shot)
                        deleted += 1
                session.commit()
            
            if deleted > 0:
                # Refresh table
                self._refresh_shot_table()
                self.status_bar.showMessage(f"Deleted {deleted} shot(s)", 3000)
    
    def _refresh_shot_table(self) -> None:
        """Refresh the shot table from database."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        if not self.current_session_id:
            return
        
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        import json
        
        # Use query optimizer for efficient queries
        from core.query_optimizer import QueryOptimizer
        
        with Session(self.session_manager.engine) as session:
            # Get total count
            total_count = session.query(ShotModel).filter(
                ShotModel.session_id == self.current_session_id
            ).count()
            
                # Enable pagination if more than 100 shots
            if total_count > 100:
                def load_page(offset: int, limit: int):
                    # Use a new session context for each page load
                    with Session(self.session_manager.engine) as page_session:
                        shots = page_session.query(ShotModel).filter(
                            ShotModel.session_id == self.current_session_id
                        ).order_by(ShotModel.recorded_at).offset(offset).limit(limit).all()
                        
                        # Load all data before closing the session context
                        shot_data_list = []
                        for shot in shots:
                            shot_data_list.append({
                                'id': shot.id,
                                'recorded_at': shot.recorded_at,
                                'club_speed': shot.club_speed,
                                'ball_speed': shot.ball_speed,
                                'spin_rate': shot.spin_rate,
                                'dtl_video_path': shot.dtl_video_path,
                                'face_video_path': shot.face_video_path,
                                'tags': shot.tags,
                                'is_favorite': shot.is_favorite,
                            })
                        
                        # Now build rows outside the database session context
                        rows = []
                        for shot_data in shot_data_list:
                            time_item = QTableWidgetItem(shot_data['recorded_at'].strftime("%H:%M:%S"))
                            time_item.setData(Qt.ItemDataRole.UserRole, shot_data['id'])
                            
                            has_video = bool(shot_data['dtl_video_path'] or shot_data['face_video_path'])
                            if has_video:
                                time_item.setForeground(QColor(current_colors.SUCCESS))
                                time_item.setToolTip("Click to review video")
                            else:
                                time_item.setToolTip("No video available")
                            
                            # Tags
                            tags_text = ""
                            if shot_data['tags']:
                                try:
                                    tags_list = json.loads(shot_data['tags'])
                                    tags_text = ", ".join(tags_list) if tags_list else ""
                                except:
                                    tags_text = ""
                            
                            # Favorite
                            favorite_text = "★" if shot_data['is_favorite'] else ""
                            favorite_item = QTableWidgetItem(favorite_text)
                            if shot_data['is_favorite']:
                                favorite_item.setForeground(QColor(current_colors.ACCENT))
                            favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            
                            # Ensure data is properly formatted - use explicit None checks
                            club_speed = shot_data['club_speed']
                            ball_speed = shot_data['ball_speed']
                            spin_rate = shot_data['spin_rate']
                            
                            club_speed_item = QTableWidgetItem(f"{club_speed:.1f}" if club_speed is not None else "--")
                            ball_speed_item = QTableWidgetItem(f"{ball_speed:.1f}" if ball_speed is not None else "--")
                            spin_item = QTableWidgetItem(f"{spin_rate:.0f}" if spin_rate is not None else "--")
                            
                            rows.append([
                                time_item,
                                club_speed_item,
                                ball_speed_item,
                                spin_item,
                                QTableWidgetItem(tags_text),
                                favorite_item,
                            ])
                        return rows
                
                self.shot_table_widget.enable_pagination(total_count, load_page)
            else:
                self.shot_table_widget.disable_pagination()
                self.shot_table_widget.clear()
                
                # Disable sorting while populating to avoid issues
                was_sorting_enabled = self.shot_table.isSortingEnabled()
                self.shot_table.setSortingEnabled(False)
                
                shots = session.query(ShotModel).filter(
                    ShotModel.session_id == self.current_session_id
                ).order_by(ShotModel.recorded_at).all()
                
                # Load all data before closing the session context
                shot_data_list = []
                for shot in shots:
                    shot_data_list.append({
                        'id': shot.id,
                        'recorded_at': shot.recorded_at,
                        'club_speed': shot.club_speed,
                        'ball_speed': shot.ball_speed,
                        'spin_rate': shot.spin_rate,
                        'dtl_video_path': shot.dtl_video_path,
                        'face_video_path': shot.face_video_path,
                        'tags': shot.tags,
                        'is_favorite': shot.is_favorite,
                    })
                
                # Now populate the table outside the database session context
                for shot_data in shot_data_list:
                    time_item = QTableWidgetItem(shot_data['recorded_at'].strftime("%H:%M:%S"))
                    time_item.setData(Qt.ItemDataRole.UserRole, shot_data['id'])
                    
                    has_video = bool(shot_data['dtl_video_path'] or shot_data['face_video_path'])
                    if has_video:
                        time_item.setForeground(QColor(current_colors.SUCCESS))
                        time_item.setToolTip("Click to review video")
                    else:
                        time_item.setToolTip("No video available")
                    
                    # Tags
                    tags_text = ""
                    if shot_data['tags']:
                        try:
                            tags_list = json.loads(shot_data['tags'])
                            tags_text = ", ".join(tags_list) if tags_list else ""
                        except:
                            tags_text = ""
                    
                    # Favorite
                    favorite_text = "★" if shot_data['is_favorite'] else ""
                    favorite_item = QTableWidgetItem(favorite_text)
                    if shot_data['is_favorite']:
                        favorite_item.setForeground(QColor(current_colors.ACCENT))
                    favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Ensure data is properly formatted - use explicit None checks
                    club_speed = shot_data['club_speed']
                    ball_speed = shot_data['ball_speed']
                    spin_rate = shot_data['spin_rate']
                    
                    club_speed_item = QTableWidgetItem(f"{club_speed:.1f}" if club_speed is not None else "--")
                    ball_speed_item = QTableWidgetItem(f"{ball_speed:.1f}" if ball_speed is not None else "--")
                    spin_item = QTableWidgetItem(f"{spin_rate:.0f}" if spin_rate is not None else "--")
                    
                    self.shot_table_widget.add_row([
                        time_item,
                        club_speed_item,
                        ball_speed_item,
                        spin_item,
                        QTableWidgetItem(tags_text),
                        favorite_item,
                    ])
                
                # Re-enable sorting after all rows are added
                if was_sorting_enabled:
                    self.shot_table.setSortingEnabled(True)

    def _update_camera(self, view: CameraView, frame: np.ndarray) -> None:
        view.update_frame(frame)
        if view is self.dtl_view:
            self.dtl_buffer.add(frame, dt.datetime.now().timestamp())
        else:
            self.face_buffer.add(frame, dt.datetime.now().timestamp())

    def _camera_status(self, name: str, ok: bool, msg: str) -> None:
        self.status_bar.showMessage(f"{name} camera: {'OK' if ok else msg}")
        if name == "DTL":
            self.dtl_view.set_active(ok)
        elif name == "Face":
            self.face_view.set_active(ok)

    def _start_session(self) -> None:
        """Start a new recording session with optional template."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        # Check for templates and offer selection
        from app.widgets.session_template_dialog import SessionTemplateDialog
        
        template_dialog = SessionTemplateDialog(self)
        selected_template = None
        
        if template_dialog.exec() == template_dialog.DialogCode.Accepted:
            selected_template = template_dialog.selected_template
        
        # Apply template if selected
        if selected_template:
            if not self.session_name_edit.text().strip():
                self.session_name_edit.setText(selected_template.name)
            if selected_template.club and not self.session_club_combo.currentText().strip():
                idx = self.session_club_combo.findText(selected_template.club)
                if idx >= 0:
                    self.session_club_combo.setCurrentIndex(idx)
                else:
                    self.session_club_combo.setEditText(selected_template.club)
            if selected_template.notes and not self.session_notes_edit.text().strip():
                self.session_notes_edit.setText(selected_template.notes)
            if selected_template.tags:
                # Tags would be applied when session is created
                pass
        
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        custom_name = self.session_name_edit.text().strip()
        self.current_session_name = custom_name if custom_name else f"Session {timestamp}"
        
        # Start session with template data
        club = self.session_club_combo.currentText().strip() or None
        notes = self.session_notes_edit.text().strip() or None
        tags = selected_template.tags if selected_template else None
        
        session_id = self.session_manager.start_session(
            self.current_session_name,
            club=club,
            notes=notes,
            tags=tags,
        )
        self.current_session_id = session_id
        logger.info("Starting session with cameras: DTL=%s, Face=%s", 
                   self.camera_service.dtl_id, self.camera_service.face_id)
        self.session_label.setText(f"Session: {self.current_session_name} (#{session_id})")
        from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
        self.session_label.setStyleSheet(f"""
            QLabel {{
                color: {current_colors.SUCCESS};
                font-size: {TYPOGRAPHY.H3}px;
                font-weight: {TYPOGRAPHY.BOLD};
                padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                background-color: {current_colors.ACCENT_LIGHT};
                border: 1px solid {current_colors.SUCCESS};
            }}
        """)
        self.session_name_edit.setText(self.current_session_name)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.test_shot_btn.setEnabled(True)
        
        # Clear buffers when starting new session to ensure clean recording
        self.dtl_buffer.clear()
        self.face_buffer.clear()
        logger.debug("Buffers cleared at session start")
        
        self.camera_service.start()
        self.status_bar.showMessage("Session running")
        self._persist_session_details()

    def _stop_session(self) -> None:
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        
        self.session_manager.end_session()
        self.camera_service.stop()
        
        # Reset camera status indicators
        self.dtl_view.set_active(False)
        self.face_view.set_active(False)
        
        self.session_label.setText("Session: Not Started")
        self.session_label.setStyleSheet(f"""
            QLabel {{
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.H3}px;
                font-weight: {TYPOGRAPHY.BOLD};
                background: transparent;
            }}
        """)
        self.current_session_id = None
        self.current_session_name = None
        self.session_name_edit.clear()
        self.session_notes_edit.clear()
        self.session_club_combo.setCurrentIndex(-1)
        self.session_club_combo.setEditText("")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.test_shot_btn.setEnabled(False)
        
        if self.shot_table.rowCount() == 0:
            self.shot_table_empty_label.show()
        
        self.status_bar.showMessage("Session stopped")
        if self._session_browser:
            self._session_browser.refresh_sessions()

    def add_shot(self, payload: dict) -> None:
        """Handle shot detection: auto-save clips and log to database."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        try:
            # Get current time to filter buffer frames
            current_time = dt.datetime.now().timestamp()
            buffer_window = self.buffer_frames / self.fps  # Convert frames to seconds
            
            # Auto-save clips from buffer (only frames within buffer window)
            all_dtl_frames = self.dtl_buffer.dump()
            all_face_frames = self.face_buffer.dump()
            
            # Filter frames to only include those within the buffer window
            dtl_frames = [
                frame for frame in all_dtl_frames
                if (current_time - frame.timestamp) <= buffer_window
            ]
            face_frames = [
                frame for frame in all_face_frames
                if (current_time - frame.timestamp) <= buffer_window
            ]
            
            logger.info("Shot detected - DTL frames: %d (filtered from %d), Face frames: %d (filtered from %d)", 
                       len(dtl_frames), len(all_dtl_frames), len(face_frames), len(all_face_frames))
            
            dtl_path = None
            face_path = None
            
            if len(dtl_frames) > 0 or len(face_frames) > 0:
                try:
                    self.clips_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                    clip_jobs = []
                    
                    if len(dtl_frames) > 0:
                        dtl_file = self.clips_dir / f"{timestamp}_dtl.mp4"
                        clip_jobs.append(("dtl", dtl_file, dtl_frames))
                    
                    if len(face_frames) > 0:
                        face_file = self.clips_dir / f"{timestamp}_face.mp4"
                        clip_jobs.append(("face", face_file, face_frames))

                    results = self._write_clips_concurrently(clip_jobs)
                    dtl_path = results.get("dtl")
                    face_path = results.get("face")
                    if dtl_path:
                        logger.info("Auto-saved DTL clip: %s", dtl_path)
                        # Generate thumbnail in background
                        self._generate_thumbnail_async(Path(dtl_path))
                    if face_path:
                        logger.info("Auto-saved face clip: %s", face_path)
                        # Generate thumbnail in background
                        self._generate_thumbnail_async(Path(face_path))
                    
                    # Clear buffers after saving to prevent old frames in next shot
                    # (The circular buffer will continue filling with new frames)
                    self.dtl_buffer.clear()
                    self.face_buffer.clear()
                    logger.debug("Buffers cleared after saving shot")
                except Exception as e:
                    logger.error("Error saving video clips: %s", e, exc_info=True)
                    self.status_bar.showMessage(f"Warning: Failed to save video clips: {str(e)}", 5000)
            
            if not dtl_path and not face_path:
                logger.warning("No video frames available to save for this shot")
            
            # Validate shot data before logging
            from core.data_validation import validate_shot_data_dict
            validation_result = validate_shot_data_dict(payload)
            
            if validation_result.has_issues():
                warnings_text = "\n".join(validation_result.warnings)
                errors_text = "\n".join(validation_result.errors)
                if validation_result.errors:
                    logger.warning("Shot data validation errors: %s", errors_text)
                    self.status_bar.showMessage(f"Warning: Data validation errors detected. Check logs.", 5000)
                if validation_result.warnings:
                    logger.info("Shot data validation warnings: %s", warnings_text)
            
            try:
                shot_id = self.session_manager.log_shot(payload, dtl_path, face_path)
            except Exception as e:
                logger.error("Error logging shot to database: %s", e, exc_info=True)
                self.status_bar.showMessage(f"Error: Failed to log shot: {str(e)}", 5000)
                return
            
            try:
                # Hide empty state label when adding first shot
                if self.shot_table.rowCount() == 0:
                    self.shot_table_empty_label.hide()
                
                time_item = QTableWidgetItem(dt.datetime.now().strftime("%H:%M:%S"))
                time_item.setData(Qt.ItemDataRole.UserRole, shot_id)
                
                # Visual indicator for shots with video
                has_video = bool(dtl_path or face_path)
                if has_video:
                    time_item.setForeground(QColor(current_colors.SUCCESS))
                    time_item.setToolTip("Click to review video")
                else:
                    time_item.setToolTip("No video available")
                
                tags_item = QTableWidgetItem("")
                favorite_item = QTableWidgetItem("")
                favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                self.shot_table_widget.add_row([
                    time_item,
                    QTableWidgetItem(str(payload.get("ClubSpeed", "--"))),
                    QTableWidgetItem(str(payload.get("BallSpeed", "--"))),
                    QTableWidgetItem(str(payload.get("TotalSpin", "--"))),
                    tags_item,
                    favorite_item,
                ])
                
                row = self.shot_table.rowCount() - 1
                self._refresh_shot_row(row, shot_id)
                
                self.shot_table.scrollToBottom()
                
                if has_video:
                    self.status_bar.showMessage(f"Shot #{shot_id} recorded with video clips", 3000)
                else:
                    self.status_bar.showMessage(f"Shot #{shot_id} recorded (no video)", 3000)
            except Exception as e:
                logger.error("Error updating UI for shot: %s", e, exc_info=True)
                self.status_bar.showMessage(f"Shot logged but UI update failed: {str(e)}", 5000)
        except Exception as e:
            logger.error("Critical error in add_shot: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error processing shot: {str(e)}", 5000)

    def _save_clip(self) -> None:
        try:
            dtl_frames = self.dtl_buffer.dump()
            face_frames = self.face_buffer.dump()
            
            logger.info("Save clip requested: DTL frames=%d, Face frames=%d", 
                       len(dtl_frames), len(face_frames))
            
            if len(dtl_frames) == 0 and len(face_frames) == 0:
                self.status_bar.showMessage("No frames buffered yet. Start a session and capture some frames first.")
                return
            
            if len(dtl_frames) == 0:
                self.status_bar.showMessage("Warning: No DTL frames. Saving face clip only.")
            elif len(face_frames) == 0:
                self.status_bar.showMessage("Warning: No face frames. Saving DTL clip only.")

            self.clips_dir = Path(self.config.get("storage.clips_dir", "data/clips"))
            self.clips_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_files = []
            
            clip_jobs = []
            if len(dtl_frames) > 0:
                dtl_path = self.clips_dir / f"{timestamp}_dtl.mp4"
                clip_jobs.append(("dtl", dtl_path, dtl_frames))
            if len(face_frames) > 0:
                face_path = self.clips_dir / f"{timestamp}_face.mp4"
                clip_jobs.append(("face", face_path, face_frames))

            results = self._write_clips_concurrently(clip_jobs)
            for label, path in results.items():
                saved_files.append(Path(path).name)
                logger.info("Saved %s clip: %s", label.upper(), path)
            
            if saved_files:
                self.status_bar.showMessage(f"Clips saved: {', '.join(saved_files)}", 5000)
            else:
                self.status_bar.showMessage("Failed to save clips. Check logs for details.")
        except Exception as e:
            logger.error("Error saving clip: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error saving clip: {str(e)}")

    def _write_video(self, path: Path, frames: list) -> bool:
        """Write frames to video file.
        
        Args:
            path: Output file path for video
            frames: List of frame records from circular buffer
            
        Returns:
            True if video was written successfully, False otherwise
        """
        if not frames:
            logger.warning("No frames to write")
            return False
        
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed to create directory %s: %s", path.parent, e)
                return False
        
        try:
            # Validate first frame
            if not hasattr(frames[0], 'frame') or frames[0].frame is None:
                logger.error("Invalid frame data in buffer")
                return False
            
            height, width, _ = frames[0].frame.shape
            if width <= 0 or height <= 0:
                logger.error("Invalid frame dimensions: %dx%d", width, height)
                return False
            
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(path), fourcc, self.fps, (width, height))
            
            if not writer.isOpened():
                logger.error("Failed to open video writer for %s (codec: mp4v, fps: %d, size: %dx%d)", 
                           path, self.fps, width, height)
                return False
            
            frames_written = 0
            for record in frames:
                if not hasattr(record, 'frame') or record.frame is None:
                    logger.warning("Skipping invalid frame in buffer")
                    continue
                writer.write(record.frame)
                frames_written += 1
            
            writer.release()
            
            if frames_written == 0:
                logger.error("No frames were written to %s", path)
                if path.exists():
                    path.unlink()  # Remove empty file
                return False
            
            # Verify file was created and has content
            if not path.exists() or path.stat().st_size == 0:
                logger.error("Video file %s was not created or is empty", path)
                return False
            
            logger.info("Successfully wrote %d/%d frames to %s (%d bytes)", 
                       frames_written, len(frames), path, path.stat().st_size)
            return True
        except cv2.error as e:
            logger.error("OpenCV error writing video to %s: %s", path, e, exc_info=True)
            # Clean up partial file
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.error("Error writing video to %s: %s", path, e, exc_info=True)
            # Clean up partial file
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass
            return False

    def _write_clips_concurrently(self, clip_jobs: list[tuple[str, Path, list]]) -> dict[str, str]:
        """Write multiple clips concurrently using thread pool.
        
        Args:
            clip_jobs: List of tuples (label, path, frames) for each clip to write
            
        Returns:
            Dictionary mapping clip labels to file paths for successfully written clips
        """
        if not clip_jobs:
            return {}

        futures: list[tuple[str, Path, Any]] = []
        for label, path, frames in clip_jobs:
            if not frames:
                logger.warning("Skipping %s clip - no frames available", label)
                continue
            futures.append((label, path, self._clip_executor.submit(self._write_video, path, frames)))

        if not futures:
            logger.warning("No valid clip jobs to process")
            return {}

        results: dict[str, str] = {}
        for label, path, future in futures:
            try:
                # Set timeout to prevent hanging (30 seconds per clip)
                if future.result(timeout=30):
                    results[label] = str(path)
                else:
                    logger.warning("Failed to write %s clip to %s", label, path)
            except TimeoutError:
                logger.error("Timeout writing %s clip to %s (exceeded 30s)", label, path)
                future.cancel()
            except Exception as exc:
                logger.error("Error writing %s clip: %s", label, exc, exc_info=True)
        
        if len(results) < len(clip_jobs):
            logger.warning("Only %d/%d clips written successfully", len(results), len(clip_jobs))
        
        return results
    
    def _generate_thumbnail_async(self, video_path: Path) -> None:
        """Generate thumbnail for video asynchronously.
        
        Args:
            video_path: Path to video file for thumbnail generation
        """
        if not video_path or not video_path.exists():
            logger.warning("Cannot generate thumbnail - video file does not exist: %s", video_path)
            return
        
        from core.thumbnails import generate_thumbnail
        
        def generate() -> None:
            try:
                result = generate_thumbnail(video_path)
                if result:
                    logger.debug("Thumbnail generated successfully: %s", result)
                else:
                    logger.warning("Thumbnail generation returned None for %s", video_path)
            except Exception as e:
                logger.error("Error generating thumbnail for %s: %s", video_path, e, exc_info=True)
        
        self._clip_executor.submit(generate)

    def _open_settings(self) -> None:
        """Open settings dialog (kept for backward compatibility)."""
        self._show_settings()
    
    def _show_help(self) -> None:
        """Show help dialog."""
        from app.widgets.help_system import HelpDialog
        help_dialog = HelpDialog("main", self)
        help_dialog.exec()
    
    def _show_practice_drills(self) -> None:
        """Show practice drills dialog."""
        from app.widgets.practice_drill_manager import PracticeDrillDialog
        drill_dialog = PracticeDrillDialog(self.session_manager, self)
        drill_dialog.exec()
    
    def _show_settings(self) -> None:
        """Show settings view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        view_index = 9
        if view_index not in self._view_widgets:
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            available_cameras = detect_cameras()
            from app.widgets.settings_dialog import SettingsDialog
            settings_dialog = SettingsDialog(self.config, available_cameras, wrapper)
            settings_dialog.setWindowFlags(Qt.WindowType.Widget)
            settings_dialog.setParent(wrapper)
            layout.addWidget(settings_dialog)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_session_browser(self) -> None:
        """Show session browser view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 1
        if view_index not in self._view_widgets:
            from app.widgets.session_browser import SessionBrowser
            # Create wrapper widget
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Create browser dialog and embed it
            browser = SessionBrowser(self.session_manager, wrapper)
            browser.setWindowFlags(Qt.WindowType.Widget)
            browser.setParent(wrapper)
            
            layout.addWidget(browser)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
            self._session_browser = browser
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_analysis(self) -> None:
        """Show analysis dashboard in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 2
        if view_index not in self._view_widgets:
            from app.widgets.analysis_dashboard import AnalysisDashboard
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            dashboard = AnalysisDashboard(self.session_manager, wrapper)
            dashboard.setWindowFlags(Qt.WindowType.Widget)
            dashboard.setParent(wrapper)
            layout.addWidget(dashboard)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_comparison(self) -> None:
        """Show comparison view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 3
        if view_index not in self._view_widgets:
            from app.widgets.session_comparison import SessionComparison
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            comparison = SessionComparison(self.session_manager, wrapper)
            comparison.setWindowFlags(Qt.WindowType.Widget)
            comparison.setParent(wrapper)
            layout.addWidget(comparison)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_goals(self) -> None:
        """Show goals view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 4
        if view_index not in self._view_widgets:
            from app.widgets.goals_dialog import GoalsDialog
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            goals = GoalsDialog(self.session_manager, wrapper)
            goals.setWindowFlags(Qt.WindowType.Widget)
            goals.setParent(wrapper)
            layout.addWidget(goals)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_recent_shots(self) -> None:
        """Show recent shots view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 6
        if view_index not in self._view_widgets:
            from app.widgets.recent_shots_dialog import RecentShotsDialog
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            recent = RecentShotsDialog(self.session_manager, wrapper)
            recent.setWindowFlags(Qt.WindowType.Widget)
            recent.setParent(wrapper)
            layout.addWidget(recent)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_thumbnail_grid(self) -> None:
        """Show thumbnail grid view in stacked widget."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        view_index = 7
        if view_index not in self._view_widgets:
            from app.widgets.thumbnail_grid import ThumbnailGridDialog
            wrapper = QWidget()
            wrapper.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            thumbnails = ThumbnailGridDialog(self.session_manager, wrapper)
            thumbnails.setWindowFlags(Qt.WindowType.Widget)
            thumbnails.setParent(wrapper)
            layout.addWidget(thumbnails)
            
            self._stacked_widget.addWidget(wrapper)
            self._view_widgets[view_index] = wrapper
        
        self._stacked_widget.setCurrentWidget(self._view_widgets[view_index])
        self._current_view_index = view_index
    
    def _show_clips_viewer(self) -> None:
        """Show clips viewer - opens file dialog (kept as dialog for file selection)."""
        self._open_clips_viewer()
    
    def _show_main_session(self) -> None:
        """Show main session view (index 0)."""
        self._stacked_widget.setCurrentIndex(0)
        self._current_view_index = 0

    def _update_table_columns(self) -> None:
        """Update visible table columns."""
        display_cols = self.config.get("display.columns", {
            "time": True,
            "club_speed": True,
            "ball_speed": True,
            "total_spin": True,
            "tags": True,
            "favorite": True,
        })
        self.shot_table.setColumnHidden(0, not display_cols.get("time", True))
        self.shot_table.setColumnHidden(1, not display_cols.get("club_speed", True))
        self.shot_table.setColumnHidden(2, not display_cols.get("ball_speed", True))
        self.shot_table.setColumnHidden(3, not display_cols.get("total_spin", True))
        self.shot_table.setColumnHidden(4, not display_cols.get("tags", True))
        self.shot_table.setColumnHidden(5, not display_cols.get("favorite", True))
    
    def _refresh_shot_row(self, row: int, shot_id: int) -> None:
        """Refresh shot row with tags and favorite status from database."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        try:
            import json
            from sqlalchemy.orm import Session
            from core.session_manager import ShotModel
            
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, shot_id)
                if shot:
                    tags_item = self.shot_table.item(row, 4)
                    if tags_item:
                        if shot.tags:
                            tags_list = json.loads(shot.tags)
                            tags_item.setText(", ".join(tags_list) if tags_list else "")
                        else:
                            tags_item.setText("")
                    
                    favorite_item = self.shot_table.item(row, 5)
                    if favorite_item:
                        if shot.is_favorite:
                            favorite_item.setText("★")
                            favorite_item.setForeground(QColor(current_colors.ACCENT))
                        else:
                            favorite_item.setText("")
        except Exception as e:
            logger.error("Error refreshing shot row: %s", e, exc_info=True)

    def closeEvent(self, event) -> None:
        """Cleanup on window close."""
        try:
            # Save current layout
            self._save_current_layout()
        except Exception as e:
            logger.debug("Error saving layout: %s", e)
        
        try:
            self._clip_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            logger.debug("Clip executor shutdown encountered a problem", exc_info=True)
        super().closeEvent(event)
    
    def _save_current_layout(self) -> None:
        """Save current window layout."""
        if not self._main_splitter:
            return
        
        try:
            layout_data = {
                "sidebar_width": self._main_splitter.sizes()[0] if self._main_splitter.count() > 0 else 250,
                "main_splitter": self._main_splitter.sizes(),
                "window_geometry": {
                    "width": self.width(),
                    "height": self.height(),
                    "x": self.x(),
                    "y": self.y(),
                },
            }
            self.layout_manager.save_layout("default", layout_data)
        except Exception as e:
            logger.debug("Error saving layout: %s", e)
    
    def _load_saved_layout(self) -> None:
        """Load saved window layout."""
        try:
            layout = self.layout_manager.load_layout("default")
            if not layout:
                layout = self.layout_manager.get_default_layout()
            
            self._apply_layout(layout)
        except Exception as e:
            logger.debug("Error loading layout: %s", e)
    
    def _apply_layout(self, layout: dict) -> None:
        """Apply a layout configuration to the window.
        
        Args:
            layout: Layout dictionary with window_geometry and main_splitter keys
        """
        try:
            # Restore window geometry
            if "window_geometry" in layout:
                geo = layout["window_geometry"]
                self.setGeometry(geo.get("x", 100), geo.get("y", 100), 
                               geo.get("width", 1400), geo.get("height", 900))
            
            # Restore splitter sizes
            if self._main_splitter and "main_splitter" in layout:
                sizes = layout["main_splitter"]
                if len(sizes) == self._main_splitter.count():
                    self._main_splitter.setSizes(sizes)
        except Exception as e:
            logger.debug("Error applying layout: %s", e)

    def _open_clips_viewer(self) -> None:
        """Open video clip viewer dialog."""
        from PyQt6.QtWidgets import QFileDialog, QDialog, QVBoxLayout
        
        clips_dir = Path(self.config.get("storage.clips_dir", "data/clips"))
        if not clips_dir.exists():
            clips_dir = Path("data/clips")
        
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video Clip to View",
            str(clips_dir),
            "Video Files (*.mp4 *.avi *.mov);;All Files (*)",
        )
        
        if video_path:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Video Player - {Path(video_path).name}")
            dialog.setMinimumSize(800, 600)
            dialog.resize(1000, 700)
            dialog.setSizeGripEnabled(True)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            dialog.setStyleSheet(get_current_theme())
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            player = VideoPlayer(Path(video_path), dialog)
            layout.addWidget(player)
            
            dialog.exec()

    def _on_shot_clicked(self, item: QTableWidgetItem) -> None:
        """Handle single click on shot - review if video exists."""
        row = item.row()
        shot_id = self.shot_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if shot_id:
            self._review_shot_by_id(shot_id)
    
    def _on_shot_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on shot."""
        row = item.row()
        shot_id = self.shot_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if shot_id:
            self._review_shot_by_id(shot_id)
    
    def _review_shot_by_id(self, shot_id: int) -> None:
        """Open shot review window."""
        try:
            # Get shot data from database
            from sqlalchemy.orm import Session
            from core.session_manager import ShotModel
            
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, shot_id)
                if not shot:
                    self.status_bar.showMessage("Shot not found")
                    logger.warning("Shot %d not found in database", shot_id)
                    return
                
                shot_data = {
                    "ClubSpeed": shot.club_speed,
                    "BallSpeed": shot.ball_speed,
                    "TotalSpin": shot.spin_rate,
                    "LaunchAngle": shot.launch_angle,
                }
                
                dtl_path = Path(shot.dtl_video_path) if shot.dtl_video_path else None
                face_path = Path(shot.face_video_path) if shot.face_video_path else None
                
                if not dtl_path and not face_path:
                    self.status_bar.showMessage("No video clips found for this shot")
                    return
                
                # Track recent shot view
                try:
                    from core.recent_shots import RecentShotsTracker
                    cache_file = Path("data/recent_shots.json")
                    tracker = RecentShotsTracker(cache_file)
                    tracker.add_shot(shot.id, shot.session_id, shot_data)
                except Exception as e:
                    logger.debug("Error tracking recent shot: %s", e)
            
            # Open review window
            from PyQt6.QtWidgets import QDialog
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Shot Review - #{shot_id}")
            dialog.setMinimumSize(1200, 700)
            dialog.resize(1400, 800)
            dialog.setSizeGripEnabled(True)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            dialog.setStyleSheet(get_current_theme())
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            review = ShotReviewWindow(dtl_path, face_path, shot_data, dialog, shot_id=shot_id, session_manager=self.session_manager)
            layout.addWidget(review)
            
            dialog.exec()
        except Exception as e:
            logger.error("Error opening shot review: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening shot review: {str(e)}", 5000)

    def _open_session_browser(self) -> None:
        """Open session browser."""
        from app.widgets.session_browser import SessionBrowser
        
        # Always close and recreate to ensure fresh UI
        if self._session_browser:
            self._session_browser.close()
            self._session_browser = None
        
        browser = SessionBrowser(self.session_manager, self)
        browser.setModal(False)
        browser.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        browser.finished.connect(lambda _: setattr(self, "_session_browser", None))
        browser.show()
        self._session_browser = browser

    def _open_analysis(self) -> None:
        """Open analysis dashboard."""
        try:
            from app.widgets.analysis_dashboard import AnalysisDashboard
            
            dashboard = AnalysisDashboard(self.session_manager, self)
            dashboard.exec()
        except Exception as e:
            logger.error("Error opening analysis dashboard: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening analysis dashboard: {str(e)}", 5000)

    def _open_comparison(self) -> None:
        """Open session comparison."""
        try:
            from app.widgets.session_comparison import SessionComparison
            
            comparison = SessionComparison(self.session_manager, self)
            comparison.exec()
        except Exception as e:
            logger.error("Error opening session comparison: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening session comparison: {str(e)}", 5000)
    
    def _open_goals(self) -> None:
        """Open goals management dialog."""
        try:
            from app.widgets.goals_dialog import GoalsDialog
            dialog = GoalsDialog(self.session_manager, self)
            dialog.exec()
        except Exception as e:
            logger.error("Error opening goals: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening goals: {str(e)}", 5000)
    
    def _open_recent_shots(self) -> None:
        """Open recent shots dialog."""
        try:
            from app.widgets.recent_shots_dialog import RecentShotsDialog
            dialog = RecentShotsDialog(self.session_manager, self)
            dialog.exec()
        except Exception as e:
            logger.error("Error opening recent shots: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening recent shots: {str(e)}", 5000)
    
    def _open_thumbnail_grid(self) -> None:
        """Open thumbnail grid dialog."""
        try:
            from app.widgets.thumbnail_grid import ThumbnailGridDialog
            dialog = ThumbnailGridDialog(self.session_manager, self)
            if dialog.exec() == dialog.DialogCode.Accepted and dialog.selected_shot_id:
                # Open shot review for selected shot
                self._review_shot_from_id(dialog.selected_shot_id)
        except Exception as e:
            logger.error("Error opening thumbnail grid: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening thumbnail grid: {str(e)}", 5000)
    
    def _open_import_dialog(self) -> None:
        """Open import dialog for CSV/Excel files."""
        try:
            dialog = ImportDialog(self.session_manager, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.status_bar.showMessage("Data imported successfully", 3000)
                # Refresh shot table if it exists
                if hasattr(self, 'shot_table') and self.shot_table:
                    self._refresh_shot_table()
        except Exception as e:
            logger.error("Error opening import dialog: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error opening import dialog: {str(e)}", 5000)
    
    def _find_duplicates(self) -> None:
        """Find and merge duplicate shots."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        try:
            from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QDialogButtonBox
            from core.duplicate_detection import detect_and_merge_duplicates
            
            # First, run dry run to show results
            results = detect_and_merge_duplicates(self.session_manager, similarity_threshold=0.85, dry_run=True)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Find Duplicates")
            dialog.setMinimumSize(600, 400)
            dialog.setStyleSheet(get_current_theme())
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
            layout.setSpacing(SPACING.MEDIUM)
            
            info_label = QLabel(f"Found {results['duplicates_found']} potential duplicate pair(s).")
            info_label.setAutoFillBackground(True)
            info_label.setStyleSheet(style_label(weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
            layout.addWidget(info_label)
            
            if results['matches']:
                matches_text = QTextEdit()
                matches_text.setReadOnly(True)
                from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
                matches_text.setStyleSheet(f"""
                    QTextEdit {{
                        background-color: {current_colors.BACKGROUND_CONTROL};
                        border: 1px solid {current_colors.BORDER_HOVER};
                        border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                        padding: {SPACING.SMALL}px;
                        color: {current_colors.TEXT_PRIMARY};
                        font-size: {TYPOGRAPHY.SMALL}px;
                    }}
                """)
                
                matches_list = []
                for match in results['matches'][:20]:  # Show first 20
                    matches_list.append(
                        f"Shot #{match['shot1_id']} ↔ Shot #{match['shot2_id']} "
                        f"(Similarity: {match['similarity']:.1%})\n"
                        f"  Reason: {match['reason']}"
                    )
                
                if len(results['matches']) > 20:
                    matches_list.append(f"\n... and {len(results['matches']) - 20} more")
                
                matches_text.setText("\n\n".join(matches_list))
                layout.addWidget(matches_text)
            else:
                no_duplicates_label = QLabel("No duplicates found.")
                no_duplicates_label.setAutoFillBackground(True)
                no_duplicates_label.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.SMALL) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
                layout.addWidget(no_duplicates_label)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            
            if results['duplicates_found'] > 0:
                merge_btn = QPushButton("Merge Duplicates")
                from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
                merge_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {current_colors.SUCCESS};
                        color: white;
                        border: none;
                        border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                        padding: {SPACING.SMALL}px {SPACING.MEDIUM + SPACING.XS}px;
                        font-size: {TYPOGRAPHY.BODY}px;
                        font-weight: {TYPOGRAPHY.BOLD};
                    }}
                    QPushButton:hover {{
                        background-color: {current_colors.SUCCESS_HOVER};
                    }}
                """)
                merge_btn.clicked.connect(lambda: self._merge_duplicates(dialog))
                buttons.addButton(merge_btn, QDialogButtonBox.ButtonRole.ActionRole)
            
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.exec()
        except Exception as e:
            logger.error("Error finding duplicates: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error finding duplicates: {str(e)}", 5000)
    
    def _merge_duplicates(self, parent_dialog) -> None:
        """Merge duplicate shots."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from core.duplicate_detection import detect_and_merge_duplicates
            
            reply = QMessageBox.question(
                self,
                "Confirm Merge",
                "This will merge duplicate shots and remove duplicates. This action cannot be undone.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                results = detect_and_merge_duplicates(self.session_manager, similarity_threshold=0.85, dry_run=False)
                
                QMessageBox.information(
                    self,
                    "Merge Complete",
                    f"Merged {results['duplicates_merged']} duplicate pair(s).\n"
                    f"Removed {results['shots_removed']} duplicate shot(s)."
                )
                
                parent_dialog.accept()
                
                # Refresh tables
                if hasattr(self, 'shot_table') and self.shot_table:
                    self._refresh_shot_table()
                if self._session_browser:
                    self._session_browser.refresh_sessions()
                
                self.status_bar.showMessage(f"Merged {results['duplicates_merged']} duplicate pairs", 3000)
        except Exception as e:
            logger.error("Error merging duplicates: %s", e, exc_info=True)
            self.status_bar.showMessage(f"Error merging duplicates: {str(e)}", 5000)
    
    def _review_shot_from_id(self, shot_id: int) -> None:
        """Open shot review window for a specific shot ID."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import ShotModel, SessionModel
            from app.widgets.shot_review_window import ShotReviewWindow
            
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, shot_id)
                if not shot:
                    self.status_bar.showMessage(f"Shot #{shot_id} not found", 3000)
                    return
                
                sess = session.get(SessionModel, shot.session_id)
                if not sess:
                    self.status_bar.showMessage(f"Session for shot #{shot_id} not found", 3000)
                    return
                
                # Video paths are stored on ShotModel, not SessionModel
                dtl_path = Path(shot.dtl_video_path) if shot.dtl_video_path else None
                face_path = Path(shot.face_video_path) if shot.face_video_path else None
                
                if not dtl_path and not face_path:
                    self.status_bar.showMessage(f"Shot #{shot_id} has no video files", 3000)
                    return
                
                # Build shot data dict
                shot_data = {
                    'ClubSpeed': shot.club_speed,
                    'BallSpeed': shot.ball_speed,
                    'TotalSpin': shot.spin_rate,
                    'LaunchAngle': shot.launch_angle,
                    'CarryDistance': shot.carry_distance,
                    'TotalDistance': shot.total_distance,
                }
                
                # Track recent shot view
                try:
                    from core.recent_shots import RecentShotsTracker
                    cache_file = Path("data/recent_shots.json")
                    tracker = RecentShotsTracker(cache_file)
                    tracker.add_shot(shot.id, shot.session_id, shot_data)
                except Exception as e:
                    logger.debug("Error tracking recent shot: %s", e)
                
                # Open review window
                review_window = ShotReviewWindow(
                    dtl_video_path=dtl_path if dtl_path and dtl_path.exists() else None,
                    face_video_path=face_path if face_path and face_path.exists() else None,
                    shot_data=shot_data,
                    parent=self,
                    shot_id=shot_id,
                    session_manager=self.session_manager,
                )
                review_window.show()
                
        except Exception as e:
            logger.error("Error reviewing shot %d: %s", shot_id, e, exc_info=True)
            self.status_bar.showMessage(f"Error reviewing shot: {str(e)}", 5000)

    def _test_shot(self) -> None:
        """Simulate shot detection for testing."""
        import random
        
        # Generate test shot data
        test_payload = {
            "ClubSpeed": round(random.uniform(80, 120), 1),
            "BallSpeed": round(random.uniform(100, 160), 1),
            "TotalSpin": round(random.uniform(2000, 4000), 0),
            "LaunchAngle": round(random.uniform(8, 16), 1),
            "CarryDistance": round(random.uniform(180, 280), 1),
            "TotalDistance": round(random.uniform(200, 300), 1),
            "TestShot": True,  # Mark as test shot
        }
        
        logger.info("Test shot triggered: %s", test_payload)
        self.status_bar.showMessage("Test shot detected - recording video...", 2000)
        
        # Simulate shot detection
        self.add_shot(test_payload)
    
    def _open_web_dashboard(self) -> None:
        """Open web dashboard in default browser."""
        import webbrowser
        
        web_url = "http://127.0.0.1:5000"
        
        try:
            webbrowser.open(web_url)
            self.status_bar.showMessage(f"Opening web dashboard at {web_url}...", 3000)
            logger.info("Opened web dashboard in browser: %s", web_url)
        except Exception as e:
            logger.error("Error opening web dashboard: %s", e, exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Web Dashboard",
                f"Failed to open web dashboard.\n\n"
                f"Please manually navigate to:\n{web_url}\n\n"
                f"Error: {str(e)}"
            )


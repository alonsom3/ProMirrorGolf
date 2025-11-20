"""Session browser for viewing past sessions and their shots."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.session_manager import SessionModel, ShotModel

logger = logging.getLogger(__name__)


class SessionEditDialog(QDialog):
    """Dialog for editing session name, notes, and club."""
    
    def __init__(self, session: SessionModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session = session
        self.setWindowTitle("Edit Session")
        self.setMinimumSize(450, 300)
        self.resize(500, 350)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.LARGE)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Name
        name_label = QLabel("Session Name")
        name_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD}; margin-bottom: {SPACING.XS}px;")
        layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(session.name)
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        layout.addWidget(self.name_edit)
        
        # Club
        club_label = QLabel("Club")
        club_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD}; margin-top: {SPACING.SMALL}px; margin-bottom: {SPACING.XS}px;")
        layout.addWidget(club_label)
        
        self.club_edit = QLineEdit()
        self.club_edit.setText(session.club or "")
        self.club_edit.setPlaceholderText("e.g., Driver, 7 Iron, Putter")
        self.club_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        layout.addWidget(self.club_edit)
        
        notes_label = QLabel("Notes")
        notes_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD}; margin-top: {SPACING.SMALL}px; margin-bottom: {SPACING.XS}px;")
        layout.addWidget(notes_label)
        
        self.notes_edit = QLineEdit()
        self.notes_edit.setText(session.notes or "")
        self.notes_edit.setPlaceholderText("Add any notes about this session...")
        self.notes_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        layout.addWidget(self.notes_edit)
        
        # Custom fields
        from core.custom_fields import CustomFieldManager
        from pathlib import Path
        from app.widgets.custom_fields_form import CustomFieldsForm
        
        fields_file = Path("data/custom_fields.json")
        self.field_manager = CustomFieldManager(fields_file)
        self.custom_fields_form = CustomFieldsForm(self.field_manager, "sessions", self)
        layout.addWidget(self.custom_fields_form)
        
        # Load existing custom fields
        if session.custom_fields:
            self.custom_fields_form.set_values(session.custom_fields)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
                min-width: {SIZES.BUTTON_MIN_WIDTH}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QPushButton#okButton {{
                background-color: {current_colors.ACCENT};
                border-color: {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
            }}
            QPushButton#okButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SessionBrowser(QDialog):
    """Dialog for browsing sessions and viewing their shots."""

    def __init__(self, session_manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.session_manager = session_manager
        self.setWindowTitle("Session Browser")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        self.setSizeGripEnabled(True)
        # Ensure window can be maximized
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
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
                min-height: {SIZES.FOCUS_OUTLINE_OFFSET * 10}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        self._sessions_cache: list[dict] = []
        self.session_meta: dict[int, dict] = {}
        
        self.active_quick_filter = "all"
        
        # Initialize filter manager
        from core.filters import FilterManager
        from pathlib import Path
        filters_file = Path("data/filters.json")
        self.filter_manager = FilterManager(filters_file)
        
        self._build_ui()
        self._load_sessions()

    def _build_ui(self) -> None:
        """Build UI components - Scope Rank Tracking Software style."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        # Use QSplitter for resizable sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)  # Prevent sidebar from being completely hidden
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {current_colors.BORDER_DEFAULT};
            }}
            QSplitter::handle:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(splitter)

        # Left sidebar - Clean modern navigation
        sidebar = QWidget()
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(600)
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar header
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: {SPACING.LARGE}px; border-bottom: 1px solid {current_colors.BORDER_DEFAULT};")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING.MEDIUM)
        
        title_label = QLabel("Sessions")
        title_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H2}px; font-weight: {TYPOGRAPHY.BOLD};")
        header_layout.addWidget(title_label)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(SPACING.SMALL)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search sessions…")
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.setClearButtonEnabled(True)
        search_layout.addWidget(self.search_edit)
        
        # Advanced search button
        advanced_search_btn = QPushButton("🔍 Advanced")
        advanced_search_btn.setToolTip("Open Advanced Search")
        advanced_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        advanced_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.ACCENT};
            }}
        """)
        advanced_search_btn.clicked.connect(self._open_advanced_search)
        search_layout.addWidget(advanced_search_btn)
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        search_layout.addWidget(self.search_edit)
        
        # Advanced search button
        advanced_search_btn = QPushButton("🔍 Advanced")
        advanced_search_btn.setToolTip("Open Advanced Search")
        advanced_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        advanced_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.ACCENT};
            }}
        """)
        advanced_search_btn.clicked.connect(self._open_advanced_search)
        search_layout.addWidget(advanced_search_btn)
        
        header_layout.addLayout(search_layout)
        
        sidebar_layout.addWidget(header_widget)
        
        # Filter section
        filter_container = QWidget()
        filter_container.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: {SPACING.MEDIUM + SPACING.XS}px {SPACING.LARGE}px; border-bottom: 1px solid {current_colors.BORDER_DEFAULT};")
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(SPACING.SMALL)
        
        filter_label = QLabel("Filter")
        filter_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD}; margin-bottom: {SPACING.XS}px;")
        filter_layout.addWidget(filter_label)
        
        filter_chips = QHBoxLayout()
        filter_chips.setSpacing(SPACING.SMALL)
        self.quick_filter_group = QButtonGroup(self)
        self.quick_filter_group.setExclusive(True)
        quick_defs = [
            ("all", "All"),
            ("today", "Today"),
            ("week", "Week"),
        ]
        for key, label in quick_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if key == "all":
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                    border: 1px solid {current_colors.BORDER_HOVER};
                    border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                    padding: {SPACING.BUTTON_PADDING_V}px {SPACING.BUTTON_PADDING_H}px;
                    color: {current_colors.TEXT_PRIMARY};
                    font-size: {TYPOGRAPHY.BODY}px;
                    font-weight: {TYPOGRAPHY.MEDIUM};
                    min-height: {SIZES.BUTTON_MIN_HEIGHT}px;
                }}
                QPushButton:hover {{
                    background-color: {current_colors.BORDER_HOVER};
                    border-color: {current_colors.BORDER_ACTIVE};
                }}
                QPushButton:checked {{
                    background-color: {current_colors.ACCENT};
                    border-color: {current_colors.ACCENT};
                    color: {current_colors.WHITE_TEXT};
                }}
                QPushButton:checked:hover {{
                    background-color: {current_colors.ACCENT_HOVER};
                }}
            """)
            filter_chips.addWidget(btn)
            self.quick_filter_group.addButton(btn)
            btn.clicked.connect(lambda checked, k=key: self._on_quick_filter_clicked(k))
        
        filter_layout.addLayout(filter_chips)
        
        self.club_filter_combo = QComboBox()
        self.club_filter_combo.setEnabled(False)
        self.club_filter_combo.addItem("Any Club", "")
        self.club_filter_combo.currentIndexChanged.connect(self._on_quick_filter_changed)
        self.club_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.INPUT_PADDING_V}px {SPACING.INPUT_PADDING_H}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                min-height: {SIZES.INPUT_MIN_HEIGHT}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        """)
        filter_layout.addWidget(self.club_filter_combo)
        
        # Smart filters
        smart_filters_layout = QHBoxLayout()
        smart_filters_layout.setSpacing(SPACING.SMALL)
        
        save_filter_btn = QPushButton("Save Filter")
        save_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 4px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        save_filter_btn.clicked.connect(self._save_filter_preset)
        smart_filters_layout.addWidget(save_filter_btn)
        
        load_filter_btn = QPushButton("Load Filter")
        load_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_filter_btn.setStyleSheet(save_filter_btn.styleSheet())
        load_filter_btn.clicked.connect(self._load_filter_preset)
        smart_filters_layout.addWidget(load_filter_btn)
        
        filter_layout.addLayout(smart_filters_layout)
        
        sidebar_layout.addWidget(filter_container)
        
        # Sessions list
        sessions_container = QWidget()
        sessions_container.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE};")
        sessions_layout = QVBoxLayout(sessions_container)
        sessions_layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        sessions_layout.setSpacing(SPACING.SMALL)
        
        self.sessions_list = QListWidget()
        self.sessions_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.sessions_list.setSpacing(SPACING.XS)  # Reduced spacing for compact list
        self.sessions_list.setWordWrap(True)  # Enable word wrapping
        self.sessions_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: none;
                border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: 0px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                margin: 0px;
                color: {current_colors.TEXT_PRIMARY};
                min-height: {SIZES.BUTTON_MIN_HEIGHT}px;
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QListWidget::item:selected:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        self.sessions_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.sessions_list.itemClicked.connect(self._on_session_clicked)
        self.sessions_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sessions_layout.addWidget(self.sessions_list, 1)
        
        sidebar_layout.addWidget(sessions_container, 1)
        
        # Action buttons
        actions_container = QWidget()
        actions_container.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: {SPACING.MEDIUM + SPACING.XS}px {SPACING.LARGE}px; border-top: 1px solid {current_colors.BORDER_DEFAULT};")
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(SPACING.SMALL)
        
        self.selection_label = QLabel("No selection")
        self.selection_label.setAutoFillBackground(True)
        self.selection_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.XS}px 0; margin: 0px;")
        actions_layout.addWidget(self.selection_label)
        
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(SPACING.SMALL)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(self._edit_session)
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QPushButton:disabled {{
                color: {current_colors.TEXT_DISABLED};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        action_buttons.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._delete_sessions)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.DANGER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.DANGER_TEXT};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.DANGER_HOVER};
                border-color: {current_colors.DANGER};
                color: {current_colors.WHITE_TEXT};
            }}
            QPushButton:disabled {{
                color: {current_colors.TEXT_DISABLED};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        action_buttons.addWidget(self.delete_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_sessions)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QPushButton:disabled {{
                color: {current_colors.TEXT_DISABLED};
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
        """)
        action_buttons.addWidget(self.export_btn)
        
        actions_layout.addLayout(action_buttons)
        sidebar_layout.addWidget(actions_container)
        
        # Add sidebar to splitter
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 0)  # Sidebar doesn't stretch

        # Right panel - Main content area
        right_panel = QWidget()
        right_panel.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header bar
        header_bar = QWidget()
        header_bar.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: {SPACING.LARGE}px {SPACING.XL}px; border-bottom: 1px solid {current_colors.BORDER_DEFAULT};")
        header_bar_layout = QHBoxLayout(header_bar)
        header_bar_layout.setContentsMargins(0, 0, 0, 0)
        header_bar_layout.setSpacing(SPACING.MEDIUM)
        
        shots_title = QLabel("Shots")
        shots_title.setAutoFillBackground(True)
        shots_title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_SURFACE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H2}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        header_bar_layout.addWidget(shots_title)
        
        # 3D Trajectory
        trajectory_btn = QPushButton("3D Trajectory")
        trajectory_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        trajectory_btn.clicked.connect(self._open_trajectory_3d)
        trajectory_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        header_bar_layout.addWidget(trajectory_btn)
        
        # Batch operations
        batch_btn = QPushButton("Batch Operations")
        batch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        batch_btn.clicked.connect(self._batch_operations)
        batch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        header_bar_layout.addWidget(batch_btn)
        
        header_bar_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        header_bar_layout.addWidget(close_btn)
        
        right_layout.addWidget(header_bar)
        
        # Use enhanced table widget with filtering - directly in layout, no extra scroll area needed
        from app.widgets.enhanced_table import FilterableTableWidget
        
        self.shots_table_widget = FilterableTableWidget(
            columns=["Time", "Club Speed", "Ball Speed", "Spin", "Tags", "Favorite"],
            filterable_columns=list(range(6)),
            table_id="session_browser_shots_table",
        )
        self.shots_table = self.shots_table_widget.table
        
        # Enable sorting
        self.shots_table.setSortingEnabled(True)
        
        # Enable scroll wheel
        self.shots_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.shots_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Make headers visible and clickable
        header = self.shots_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        header.setDefaultSectionSize(120)
        
        # Set column widths
        self.shots_table_widget.set_column_widths([120, 120, 120, 100, 150, 80])
        
        # Set size policy to expand properly
        self.shots_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.shots_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable scrollbars on the table itself
        self.shots_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.shots_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.shots_table.itemDoubleClicked.connect(self._on_shot_double_clicked)
        self.shots_table.itemClicked.connect(self._on_shot_clicked)
        
        # Add directly to layout - table handles its own scrolling
        right_layout.addWidget(self.shots_table_widget, 1)
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)  # Right panel stretches
        
        # Set initial sizes (sidebar: 300px, rest to right panel)
        splitter.setSizes([300, 1100])

    def _load_sessions(self, preserve_selection: list[int] | None = None) -> None:
        """Load all sessions from database."""
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        
        try:
            with Session(self.session_manager.engine) as session:
                sessions = session.query(SessionModel).order_by(desc(SessionModel.started_at)).all()
                
                logger.info("Found %d sessions in database", len(sessions))
                self._sessions_cache = []
                self.session_meta = {}

                for sess in sessions:
                    shot_count = len(sess.shots) if sess.shots else 0
                    started = sess.started_at.strftime('%Y-%m-%d %H:%M')
                    club_badge = f" • {sess.club}" if sess.club else ""
                    # Compact single-line format: Name [Club] | Date | Shots
                    item_text = f"{sess.name}{club_badge} | {started} | {shot_count} shot{'s' if shot_count != 1 else ''}"
                    # Store full display text separately for tooltip
                    full_text = f"{sess.name}{club_badge}\n{started}  •  {shot_count} shot{'s' if shot_count != 1 else ''}"
                    if sess.notes:
                        full_text += f"\n{sess.notes}"
                    entry = {
                        "id": sess.id,
                        "name": sess.name,
                        "club": sess.club or "",
                        "notes": sess.notes or "",
                        "shots": shot_count,
                        "started": started,
                        "display": item_text,
                        "full_text": full_text,
                        "started_dt": sess.started_at,
                    }
                    self._sessions_cache.append(entry)
                    self.session_meta[sess.id] = entry

            self._update_club_filter_options()
            self._apply_session_filter(preserve_selection or [])
        except Exception as e:
            logger.error("Error loading sessions: %s", e, exc_info=True)
            if hasattr(self, 'sessions_list') and self.sessions_list is not None:
                try:
                    item = QListWidgetItem(f"Error loading sessions: {str(e)}")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.sessions_list.addItem(item)
                except RuntimeError:
                    pass
    
    def refresh_sessions(self, focus_id: int | None = None) -> None:
        """Public hook to refresh session list, preserving selection or focusing a session."""
        if focus_id:
            self._load_sessions([focus_id])
        else:
            self._load_sessions(self._selected_session_ids())

    def _open_advanced_search(self) -> None:
        """Open advanced search dialog."""
        from app.widgets.advanced_search_dialog import AdvancedSearchDialog
        
        dialog = AdvancedSearchDialog(self.session_manager, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            criteria = dialog.get_criteria()
            if criteria:
                # Apply advanced search
                from sqlalchemy.orm import Session
                from core.search import search_shots_advanced
                
                try:
                    with Session(self.session_manager.engine) as db_session:
                        shots, total = search_shots_advanced(db_session, criteria)
                        # Update shots table with results
                        self._display_advanced_search_results(shots)
                except Exception as e:
                    logger.error("Error in advanced search: %s", e, exc_info=True)
                    QMessageBox.warning(self, "Search Error", f"Error performing search: {str(e)}")
    
    def _display_advanced_search_results(self, shots: list) -> None:
        """Display advanced search results in the shots table."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        import json
        from core.thumbnails import get_thumbnail_path
        
        self.shots_table_widget.clear()
        
        if not shots:
            self.shots_table_widget.add_row(["No shots match the search criteria", "", "", "", "", ""])
            return
        
        for shot in shots:
            time_str = shot.recorded_at.strftime("%H:%M:%S")
            club_speed_str = f"{shot.club_speed:.1f}" if shot.club_speed else "--"
            ball_speed_str = f"{shot.ball_speed:.1f}" if shot.ball_speed else "--"
            spin_str = f"{shot.spin_rate:.0f}" if shot.spin_rate else "--"
            
            time_item = QTableWidgetItem(time_str)
            time_item.setData(Qt.ItemDataRole.UserRole, shot.id)
            has_video = bool(shot.dtl_video_path or shot.face_video_path)
            if has_video:
                time_item.setForeground(QColor(current_colors.SUCCESS))
                video_path = Path(shot.dtl_video_path) if shot.dtl_video_path else Path(shot.face_video_path)
                thumb_path = get_thumbnail_path(video_path)
                if thumb_path.exists():
                    pixmap = QPixmap(str(thumb_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        icon = QIcon(scaled)
                        time_item.setIcon(icon)
            
            tags_text = ""
            if shot.tags:
                tags_list = json.loads(shot.tags)
                tags_text = ", ".join(tags_list) if tags_list else ""
            
            favorite_text = "★" if shot.is_favorite else ""
            favorite_item = QTableWidgetItem(favorite_text)
            if shot.is_favorite:
                favorite_item.setForeground(QColor(current_colors.ACCENT))
            favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.shots_table_widget.add_row([
                time_item,
                QTableWidgetItem(club_speed_str),
                QTableWidgetItem(ball_speed_str),
                QTableWidgetItem(spin_str),
                QTableWidgetItem(tags_text),
                favorite_item,
            ])
    
    def _on_search_changed(self, _: str) -> None:
        """Reapply session filter when the search text changes."""
        self._apply_session_filter(self._selected_session_ids())

    def _selected_session_ids(self) -> list[int]:
        """Return the IDs of currently-selected sessions."""
        ids: list[int] = []
        for item in self.sessions_list.selectedItems():
            session_id = item.data(Qt.ItemDataRole.UserRole)
            if session_id:
                ids.append(session_id)
        return ids

    def _current_shot_ids(self) -> list[int]:
        """Return the shot IDs currently visible in the table."""
        shot_ids: list[int] = []
        for row in range(self.shots_table.rowCount()):
            if self.shots_table.isRowHidden(row):
                continue
            item = self.shots_table.item(row, 0)
            if not item:
                continue
            shot_id = item.data(Qt.ItemDataRole.UserRole)
            if shot_id:
                shot_ids.append(shot_id)
        return shot_ids

    def _apply_session_filter(self, preserve_selection: list[int] | None = None) -> None:
        """Populate the sessions list according to the search query."""
        if preserve_selection is None:
            preserve_selection = []

        query = (self.search_edit.text().strip() if hasattr(self, "search_edit") else "")
        if hasattr(self, 'sessions_list') and self.sessions_list is not None:
            try:
                self.sessions_list.clear()
            except RuntimeError:
                return

        if not self._sessions_cache:
            if hasattr(self, 'sessions_list') and self.sessions_list is not None:
                try:
                    item = QListWidgetItem("No sessions found")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.sessions_list.addItem(item)
                except RuntimeError:
                    pass
            self._update_selection_label()
            return

        # Use advanced search if query is provided
        if query:
            try:
                from core.search import search_sessions
                from sqlalchemy.orm import Session
                
                with Session(self.session_manager.engine) as db_session:
                    matching_sessions = search_sessions(
                        db_session,
                        query,
                        include_name=True,
                        include_notes=True,
                        include_club=True,
                        include_tags=True,
                    )
                    matching_ids = {s.id for s in matching_sessions}
                    
                    # Filter cache by matching IDs
                    filtered = [e for e in self._sessions_cache if e.get("id") in matching_ids]
            except Exception as e:
                logger.error("Error in advanced search: %s", e, exc_info=True)
                # Fallback to simple search
                query_lower = query.lower()
                filtered = []
                for entry in self._sessions_cache:
                    haystack = " ".join(
                        filter(
                            None,
                            [
                                entry.get("name", ""),
                                entry.get("club", ""),
                                entry.get("notes", ""),
                                entry.get("started", ""),
                            ],
                        )
                    ).lower()
                    if query_lower in haystack:
                        filtered.append(entry)
        else:
            filtered = self._sessions_cache.copy()
        
        # Apply quick filters
        today = datetime.now().date()
        week_cutoff = datetime.now() - timedelta(days=7)
        final_filtered = []
        for entry in filtered:
            if self.active_quick_filter == "today":
                if not entry.get("started_dt") or entry["started_dt"].date() != today:
                    continue
            elif self.active_quick_filter == "week":
                if not entry.get("started_dt") or entry["started_dt"] < week_cutoff:
                    continue
            elif self.active_quick_filter == "club":
                club_value = self.club_filter_combo.currentData()
                if club_value:
                    if entry.get("club", "").lower() != club_value:
                        continue
            final_filtered.append(entry)
        
        filtered = final_filtered

        if not filtered:
            if hasattr(self, 'sessions_list') and self.sessions_list is not None:
                try:
                    item = QListWidgetItem("No sessions match your search")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.sessions_list.addItem(item)
                except RuntimeError:
                    pass
            self._update_selection_label()
            return

        restored_selection = False
        if hasattr(self, 'sessions_list') and self.sessions_list is not None:
            try:
                for entry in filtered:
                    item = QListWidgetItem(entry["display"])
                    item.setData(Qt.ItemDataRole.UserRole, entry["id"])
                    # Add tooltip with full information
                    full_text = entry.get("full_text", entry["display"])
                    item.setToolTip(full_text)
                    self.sessions_list.addItem(item)
                    if entry["id"] in preserve_selection:
                        item.setSelected(True)
                        restored_selection = True

                if not restored_selection and self.sessions_list.count() > 0:
                    self.sessions_list.setCurrentRow(0)

                current_item = self.sessions_list.currentItem()
                if current_item and current_item.data(Qt.ItemDataRole.UserRole):
                    self._on_session_clicked(current_item)
            except RuntimeError:
                pass

        self._update_selection_label()

    def _update_selection_label(self) -> None:
        """Update the helper label that explains the current selection."""
        if not hasattr(self, "selection_label"):
            return

        selected_ids = self._selected_session_ids()
        if not selected_ids:
            self.selection_label.setText("No selection")
            return

        total_shots = sum(self.session_meta.get(sid, {}).get("shots", 0) for sid in selected_ids)
        self.selection_label.setText(f"{len(selected_ids)} session{'s' if len(selected_ids) != 1 else ''} • {total_shots} shot{'s' if total_shots != 1 else ''}")

    def _on_quick_filter_clicked(self, filter_key: str) -> None:
        """Handle quick filter button clicks."""
        self.active_quick_filter = filter_key
        self.club_filter_combo.setEnabled(filter_key == "club")
        if filter_key != "club":
            self.club_filter_combo.setCurrentIndex(0)
        self._apply_session_filter(self._selected_session_ids())

    def _save_filter_preset(self) -> None:
        """Save current filter as a preset."""
        from PyQt6.QtWidgets import QInputDialog
        from core.filters import FilterPreset
        
        name, ok = QInputDialog.getText(
            self,
            "Save Filter",
            "Filter name:",
            QLineEdit.EchoMode.Normal,
        )
        
        if not ok or not name.strip():
            return
        
        preset = FilterPreset(
            name=name.strip(),
            query=self.search_edit.text(),
            quick_filter=self.active_quick_filter,
            club_filter=self.club_filter_combo.currentData(),
        )
        
        self.filter_manager.add_preset(preset)
        self._show_message(QMessageBox.Icon.Information, "Filter Saved", f"Filter '{name}' saved successfully.")
    
    def _load_filter_preset(self) -> None:
        """Load a saved filter preset."""
        presets = self.filter_manager.list_presets()
        if not presets:
            self._show_message(QMessageBox.Icon.Information, "No Presets", "No saved filter presets available.")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        preset_names = [p.name for p in presets]
        name, ok = QInputDialog.getItem(
            self,
            "Load Filter",
            "Select filter preset:",
            preset_names,
            0,
            False,
        )
        
        if not ok:
            return
        
        preset = self.filter_manager.get_preset(name)
        if preset:
            self.search_edit.setText(preset.query)
            self.active_quick_filter = preset.quick_filter
            
            # Update quick filter buttons
            for btn in self.quick_filter_group.buttons():
                if btn.text().lower() == preset.quick_filter:
                    btn.setChecked(True)
                    break
            
            # Update club filter
            if preset.club_filter:
                index = self.club_filter_combo.findData(preset.club_filter)
                if index >= 0:
                    self.club_filter_combo.setCurrentIndex(index)
            
            self._apply_session_filter()
    
    def _on_quick_filter_changed(self) -> None:
        """Triggered when the club combo changes."""
        if self.active_quick_filter == "club":
            self._apply_session_filter(self._selected_session_ids())

    def _update_club_filter_options(self) -> None:
        """Populate the club filter combo from available sessions."""
        clubs = sorted({entry["club"] for entry in self._sessions_cache if entry.get("club")})
        current = self.club_filter_combo.currentData() if self.club_filter_combo.count() else ""
        self.club_filter_combo.blockSignals(True)
        self.club_filter_combo.clear()
        self.club_filter_combo.addItem("Any Club", "")
        for club in clubs:
            self.club_filter_combo.addItem(club, club.lower())
        index = self.club_filter_combo.findData(current) if current else 0
        if index >= 0:
            self.club_filter_combo.setCurrentIndex(index)
        self.club_filter_combo.blockSignals(False)
        self.club_filter_combo.setEnabled(self.active_quick_filter == "club")

    def _show_message(
        self,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.StandardButton.Ok,
        default: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    ) -> QMessageBox.StandardButton:
        """Create a consistently-themed message box."""
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(buttons)
        box.setDefaultButton(default)
        box.setStyleSheet(get_current_theme())
        return box.exec()

    def _on_selection_changed(self) -> None:
        """Handle selection changes - enable/disable buttons."""
        selected_items = self.sessions_list.selectedItems()
        has_selection = len(selected_items) > 0
        single_selection = len(selected_items) == 1
        
        self.edit_btn.setEnabled(single_selection)
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        
        # If single selection, load shots for that session
        if single_selection:
            self._on_session_clicked(selected_items[0])
        
        self._update_selection_label()

    def _on_session_clicked(self, item: QListWidgetItem) -> None:
        """Handle single session click - load shots."""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        
        if not session_id:
            self.shots_table_widget.clear()
            return
        
        self._load_shots_for_session(session_id)

    def _load_shots_for_session(self, session_id: int) -> None:
        """Load shots for selected session with pagination support.
        
        Automatically enables pagination for sessions with 100+ shots
        to improve performance. Smaller sessions load all shots at once.
        """
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()

        if not session_id:
            self.shots_table_widget.clear()
            self.shots_table_widget.disable_pagination()
            return
        
        from sqlalchemy.orm import Session
        from sqlalchemy import func
        
        try:
            with Session(self.session_manager.engine) as session:
                # Get total count
                total_shots = session.query(func.count(ShotModel.id)).filter(
                    ShotModel.session_id == session_id
                ).scalar()
                
                logger.info("Found %d shots for session %d", total_shots, session_id)
                
                if total_shots == 0:
                    self.shots_table_widget.clear()
                    self.shots_table_widget.disable_pagination()
                    self.shots_table_widget.add_row(["No shots in this session", "", "", "", "", ""])
                    return
                
                # Enable pagination if more than 100 shots
                if total_shots > 100:
                    def load_shot_page(offset: int, limit: int) -> list:
                        """Load a page of shots."""
                        shots = session.query(ShotModel).filter(
                            ShotModel.session_id == session_id
                        ).order_by(ShotModel.recorded_at).offset(offset).limit(limit).all()
                        
                        import json
                        from core.thumbnails import get_thumbnail_path
                        rows = []
                        
                        for shot in shots:
                            time_str = shot.recorded_at.strftime("%H:%M:%S")
                            club_speed_str = f"{shot.club_speed:.1f}" if shot.club_speed else "--"
                            ball_speed_str = f"{shot.ball_speed:.1f}" if shot.ball_speed else "--"
                            spin_str = f"{shot.spin_rate:.0f}" if shot.spin_rate else "--"
                            
                            time_item = QTableWidgetItem(time_str)
                            time_item.setData(Qt.ItemDataRole.UserRole, shot.id)
                            has_video = bool(shot.dtl_video_path or shot.face_video_path)
                            if has_video:
                                time_item.setForeground(QColor(current_colors.SUCCESS))
                                video_path = Path(shot.dtl_video_path) if shot.dtl_video_path else Path(shot.face_video_path)
                                thumb_path = get_thumbnail_path(video_path)
                                if thumb_path.exists():
                                    pixmap = QPixmap(str(thumb_path))
                                    if not pixmap.isNull():
                                        scaled = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                        icon = QIcon(scaled)
                                        time_item.setIcon(icon)
                            
                            tags_text = ""
                            if shot.tags:
                                tags_list = json.loads(shot.tags)
                                tags_text = ", ".join(tags_list) if tags_list else ""
                            
                            favorite_text = "★" if shot.is_favorite else ""
                            favorite_item = QTableWidgetItem(favorite_text)
                            if shot.is_favorite:
                                favorite_item.setForeground(QColor(current_colors.ACCENT))
                            favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            
                            rows.append([
                                time_item,
                                QTableWidgetItem(club_speed_str),
                                QTableWidgetItem(ball_speed_str),
                                QTableWidgetItem(spin_str),
                                QTableWidgetItem(tags_text),
                                favorite_item,
                            ])
                        return rows
                    
                    self.shots_table_widget.enable_pagination(total_shots, load_shot_page)
                else:
                    # Load all shots for small sessions
                    self.shots_table_widget.disable_pagination()
                    shots = session.query(ShotModel).filter(
                        ShotModel.session_id == session_id
                    ).order_by(ShotModel.recorded_at).all()
                    
                    import json
                    from core.thumbnails import get_thumbnail_path
                    
                    self.shots_table_widget.clear()
                    for shot in shots:
                        time_str = shot.recorded_at.strftime("%H:%M:%S")
                        club_speed_str = f"{shot.club_speed:.1f}" if shot.club_speed else "--"
                        ball_speed_str = f"{shot.ball_speed:.1f}" if shot.ball_speed else "--"
                        spin_str = f"{shot.spin_rate:.0f}" if shot.spin_rate else "--"
                        
                        time_item = QTableWidgetItem(time_str)
                        time_item.setData(Qt.ItemDataRole.UserRole, shot.id)
                        has_video = bool(shot.dtl_video_path or shot.face_video_path)
                        if has_video:
                            time_item.setForeground(QColor(current_colors.SUCCESS))
                            video_path = Path(shot.dtl_video_path) if shot.dtl_video_path else Path(shot.face_video_path)
                            thumb_path = get_thumbnail_path(video_path)
                            if thumb_path.exists():
                                pixmap = QPixmap(str(thumb_path))
                                if not pixmap.isNull():
                                    scaled = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    icon = QIcon(scaled)
                                    time_item.setIcon(icon)
                        
                        tags_text = ""
                        if shot.tags:
                            tags_list = json.loads(shot.tags)
                            tags_text = ", ".join(tags_list) if tags_list else ""
                        
                        favorite_text = "★" if shot.is_favorite else ""
                        favorite_item = QTableWidgetItem(favorite_text)
                        if shot.is_favorite:
                            favorite_item.setForeground(QColor(current_colors.ACCENT))
                        favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        self.shots_table_widget.add_row([
                            time_item,
                            QTableWidgetItem(club_speed_str),
                            QTableWidgetItem(ball_speed_str),
                            QTableWidgetItem(spin_str),
                            QTableWidgetItem(tags_text),
                            favorite_item,
                        ])
        except Exception as e:
            logger.error("Error loading shots: %s", e, exc_info=True)
            self.shots_table_widget.clear()
            self.shots_table_widget.disable_pagination()
            self.shots_table_widget.add_row([f"Error: {str(e)}", "", "", "", "", ""])

    def _get_shot_info(self, shot_id: int) -> tuple[tuple[Optional[Path], Optional[Path]], dict] | None:
        """Retrieve shot metadata and clip paths for a given shot id."""
        from sqlalchemy.orm import Session
        
        try:
            with Session(self.session_manager.engine) as session:
                shot = session.get(ShotModel, shot_id)
                if not shot:
                    return None
                
                shot_data = {
                    "ClubSpeed": shot.club_speed,
                    "BallSpeed": shot.ball_speed,
                    "TotalSpin": shot.spin_rate,
                    "LaunchAngle": shot.launch_angle,
                }
                
                dtl_path = Path(shot.dtl_video_path) if shot.dtl_video_path else None
                face_path = Path(shot.face_video_path) if shot.face_video_path else None
                
                if dtl_path and not dtl_path.exists():
                    logger.warning("DTL video file not found: %s", dtl_path)
                    dtl_path = None
                if face_path and not face_path.exists():
                    logger.warning("Face video file not found: %s", face_path)
                    face_path = None
                
                return (dtl_path, face_path), shot_data
        except Exception as exc:
            logger.error("Error fetching shot %d: %s", shot_id, exc, exc_info=True)
            return None

    def _edit_session(self) -> None:
        """Edit selected session."""
        selected_items = self.sessions_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if not session_id:
            return
        
        from sqlalchemy.orm import Session
        
        try:
            with Session(self.session_manager.engine) as session:
                sess = session.get(SessionModel, session_id)
                if not sess:
                    self._show_message(QMessageBox.Icon.Warning, "Error", "Session not found")
                    return
                
                dialog = SessionEditDialog(sess, self)
                if dialog.exec() == dialog.DialogCode.Accepted:
                    name = dialog.name_edit.text().strip()
                    club = dialog.club_edit.text().strip() or None
                    notes = dialog.notes_edit.text().strip() or None
                    
                    if not name:
                        self._show_message(QMessageBox.Icon.Warning, "Error", "Session name cannot be empty")
                        return
                    
                    # Get custom fields
                    from core.custom_fields import set_custom_fields_to_json
                    custom_fields_values = dialog.custom_fields_form.get_values()
                    custom_fields_json = set_custom_fields_to_json(custom_fields_values)
                    
                    if self.session_manager.update_session(session_id, name=name, club=club, notes=notes, custom_fields=custom_fields_json):
                        self._load_sessions([session_id])
                        self._show_message(QMessageBox.Icon.Information, "Success", "Session updated successfully")
                    else:
                        self._show_message(QMessageBox.Icon.Warning, "Error", "Failed to update session")
        except Exception as e:
            logger.error("Error editing session: %s", e, exc_info=True)
            self._show_message(QMessageBox.Icon.Critical, "Error", f"Failed to edit session: {str(e)}")

    def _delete_sessions(self) -> None:
        """Delete selected sessions."""
        selected_items = self.sessions_list.selectedItems()
        if not selected_items:
            return
        
        from sqlalchemy.orm import Session
        
        try:
            session_ids = []
            session_names = []
            total_shots = 0
            
            with Session(self.session_manager.engine) as session:
                for item in selected_items:
                    session_id = item.data(Qt.ItemDataRole.UserRole)
                    if session_id:
                        sess = session.get(SessionModel, session_id)
                        if sess:
                            session_ids.append(session_id)
                            session_names.append(sess.name)
                            total_shots += len(sess.shots) if sess.shots else 0
            
            if not session_ids:
                self._show_message(QMessageBox.Icon.Warning, "Error", "No valid sessions selected")
                return
            
            if len(session_names) == 1:
                msg = f"Are you sure you want to delete '{session_names[0]}'?\n\n"
            else:
                msg = f"Are you sure you want to delete {len(session_names)} sessions?\n\n"
                msg += f"Sessions: {', '.join(session_names[:3])}"
                if len(session_names) > 3:
                    msg += f" and {len(session_names) - 3} more...\n\n"
                else:
                    msg += "\n\n"
            
            msg += f"This will delete {total_shots} shot(s) total and cannot be undone."
            
            reply = self._show_message(
                QMessageBox.Icon.Question,
                "Delete Sessions",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                deleted_count = 0
                for session_id in session_ids:
                    if self.session_manager.delete_session(session_id):
                        deleted_count += 1
                
                if deleted_count > 0:
                    self._load_sessions()
                    self._show_message(
                        QMessageBox.Icon.Information,
                        "Success",
                        f"Deleted {deleted_count} session(s) successfully",
                    )
                else:
                    self._show_message(QMessageBox.Icon.Warning, "Error", "Failed to delete sessions")
        except Exception as e:
            logger.error("Error deleting sessions: %s", e, exc_info=True)
            self._show_message(QMessageBox.Icon.Critical, "Error", f"Failed to delete sessions: {str(e)}")

    def _export_sessions(self) -> None:
        """Export selected sessions."""
        from PyQt6.QtWidgets import QFileDialog
        from core.export import export_session_to_csv, export_session_to_json, export_session_to_pdf
        from sqlalchemy.orm import Session
        
        selected_items = self.sessions_list.selectedItems()
        if not selected_items:
            return
        
        session_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        if not session_ids:
            self._show_message(QMessageBox.Icon.Warning, "Error", "No valid sessions selected")
            return
        
        format_dialog = QMessageBox(self)
        format_dialog.setWindowTitle("Export Format")
        format_dialog.setText("Choose export format:")
        csv_btn = format_dialog.addButton("CSV", QMessageBox.ButtonRole.AcceptRole)
        json_btn = format_dialog.addButton("JSON", QMessageBox.ButtonRole.AcceptRole)
        pdf_btn = format_dialog.addButton("PDF", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = format_dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        format_dialog.setStyleSheet(get_current_theme())
        format_dialog.exec()
        
        clicked = format_dialog.clickedButton()
        if clicked == cancel_btn:
            return
        
        if clicked == csv_btn:
            ext = "csv"
            export_func = export_session_to_csv
        elif clicked == json_btn:
            ext = "json"
            export_func = export_session_to_json
        elif clicked == pdf_btn:
            ext = "pdf"
            export_func = export_session_to_pdf
        else:
            return
        
        if len(session_ids) == 1:
            default_name = f"session_{session_ids[0]}.{ext}"
        else:
            default_name = f"sessions_{len(session_ids)}.{ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Sessions as {ext.upper()}",
            default_name,
            f"{ext.upper()} Files (*.{ext});;All Files (*)",
        )
        
        if not file_path:
            return
        
        output_path = Path(file_path)
        
        try:
            with Session(self.session_manager.engine) as db_session:
                for idx, session_id in enumerate(session_ids):
                    sess = db_session.get(SessionModel, session_id)
                    if not sess:
                        continue
                    
                    shots = list(sess.shots) if sess.shots else []
                    
                    if len(session_ids) > 1:
                        if idx == 0:
                            final_path = output_path
                        else:
                            final_path = output_path.parent / f"{output_path.stem}_{idx}{output_path.suffix}"
                    else:
                        final_path = output_path
                    
                    if export_func(sess, shots, final_path):
                        logger.info("Exported session %d to %s", session_id, final_path)
                    else:
                        self._show_message(QMessageBox.Icon.Warning, "Export Error", f"Failed to export session {sess.name}")
                        return
            
            self._show_message(
                QMessageBox.Icon.Information,
                "Export Complete",
                f"Successfully exported {len(session_ids)} session(s) to {output_path.parent}",
            )
        except Exception as e:
            logger.error("Error exporting sessions: %s", e, exc_info=True)
            self._show_message(QMessageBox.Icon.Critical, "Error", f"Failed to export sessions: {str(e)}")

    def _on_shot_clicked(self, item: QTableWidgetItem) -> None:
        """Handle single click on shot - review if video exists."""
        shot_id = item.data(Qt.ItemDataRole.UserRole)
        if shot_id:
            # Check if video exists before opening review
            result = self._get_shot_info(shot_id)
            if result:
                (dtl_path, face_path), _ = result
                if dtl_path or face_path:
                    self._review_shot(shot_id)
    
    def _on_shot_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on shot."""
        shot_id = item.data(Qt.ItemDataRole.UserRole)
        if shot_id:
            self._review_shot(shot_id)

    def _open_trajectory_3d(self) -> None:
        """Open 3D trajectory visualization for selected shots."""
        from app.widgets.trajectory_3d import Trajectory3DDialog
        from sqlalchemy.orm import Session
        
        selected_items = self.shots_table.selectedItems()
        if not selected_items:
            self._show_message(QMessageBox.Icon.Information, "No Selection", "Please select shots to view trajectory.")
            return
        
        shot_ids = set()
        for item in selected_items:
            row = item.row()
            shot_id_item = self.shots_table.item(row, 0)
            if shot_id_item:
                shot_id = shot_id_item.data(Qt.ItemDataRole.UserRole)
                if shot_id:
                    shot_ids.add(shot_id)
        
        if not shot_ids:
            self._show_message(QMessageBox.Icon.Warning, "Error", "No valid shots selected.")
            return
        
        try:
            with Session(self.session_manager.engine) as session:
                shots = session.query(ShotModel).filter(ShotModel.id.in_(shot_ids)).all()
                
                if not shots:
                    self._show_message(QMessageBox.Icon.Warning, "Error", "No shots found.")
                    return
                
                dialog = Trajectory3DDialog(shots, self)
                dialog.exec()
        except Exception as e:
            logger.error("Error opening 3D trajectory: %s", e, exc_info=True)
            self._show_message(QMessageBox.Icon.Critical, "Error", f"Failed to open 3D trajectory: {str(e)}")
    
    def _review_shot(self, shot_id: int) -> None:
        """Open review window for shot."""
        from app.widgets.shot_review_window import ShotReviewWindow
        
        shot_ids = self._current_shot_ids()
        if not shot_ids:
            self._show_message(QMessageBox.Icon.Information, "No Shots", "There are no shots to review.")
            return
        if shot_id not in shot_ids:
            shot_ids.append(shot_id)
        current_index = shot_ids.index(shot_id)
        
        review_dialog = QDialog(self)
        review_dialog.setWindowTitle(f"Shot Review - #{shot_id}")
        review_dialog.setMinimumSize(1200, 700)
        review_dialog.resize(1400, 800)
        review_dialog.setSizeGripEnabled(True)
        review_dialog.setWindowFlags(review_dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        review_dialog.setStyleSheet(get_current_theme())
        review_layout = QVBoxLayout(review_dialog)
        review_layout.setContentsMargins(SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM, SPACING.MEDIUM)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(SPACING.MEDIUM)
        
        prev_btn = QPushButton("Previous")
        next_btn = QPushButton("Next")
        nav_label = QLabel("")
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        nav_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.BODY}px;")
        
        nav_layout.addWidget(prev_btn)
        nav_layout.addStretch(1)
        nav_layout.addWidget(nav_label)
        nav_layout.addStretch(1)
        nav_layout.addWidget(next_btn)
        review_layout.addLayout(nav_layout)
        
        review_widget: ShotReviewWindow | None = None
        shot_index = current_index
        
        def update_nav_state() -> None:
            nav_label.setText(f"Shot {shot_index + 1} / {len(shot_ids)}")
            prev_btn.setEnabled(shot_index > 0)
            next_btn.setEnabled(shot_index < len(shot_ids) - 1)
        
        def load_shot_at(index: int, silent: bool = False) -> bool:
            nonlocal review_widget, shot_index
            result = self._get_shot_info(shot_ids[index])
            if result is None:
                if not silent:
                    self._show_message(QMessageBox.Icon.Warning, "Error", f"Shot #{shot_ids[index]} not found.")
                return False
            (dtl_path, face_path), shot_data = result
            if not dtl_path and not face_path:
                if not silent:
                    self._show_message(
                        QMessageBox.Icon.Information,
                        "No Video",
                        f"Shot #{shot_ids[index]} has no video files.\n\n"
                        f"Club Speed: {shot_data.get('ClubSpeed') or '--'}\n"
                        f"Ball Speed: {shot_data.get('BallSpeed') or '--'}\n"
                        f"Spin: {shot_data.get('TotalSpin') or '--'}",
                    )
                return False
            
            new_widget = ShotReviewWindow(dtl_path, face_path, shot_data, review_dialog, shot_id=shot_ids[index], session_manager=self.session_manager)
            if review_widget:
                review_layout.removeWidget(review_widget)
                review_widget.close()
                review_widget.deleteLater()
            review_layout.addWidget(new_widget, 1)
            review_widget = new_widget
            shot_index = index
            update_nav_state()
            
            # Track recent shot view
            try:
                from core.recent_shots import RecentShotsTracker
                from pathlib import Path
                from sqlalchemy.orm import Session
                cache_file = Path("data/recent_shots.json")
                tracker = RecentShotsTracker(cache_file)
                with Session(self.session_manager.engine) as db_session:
                    shot = db_session.get(ShotModel, shot_ids[index])
                    if shot:
                        tracker.add_shot(shot.id, shot.session_id, shot_data)
            except Exception as e:
                logger.debug("Error tracking recent shot: %s", e)
            
            return True
        
        def load_initial(index: int) -> bool:
            order = list(range(index, len(shot_ids))) + list(range(index - 1, -1, -1))
            for idx in order:
                if load_shot_at(idx, silent=(idx != index)):
                    return True
            self._show_message(
                QMessageBox.Icon.Information,
                "No Video",
                "None of the shots in this session have associated video files.",
            )
            return False
        
        def navigate(step: int) -> None:
            idx = shot_index + step
            while 0 <= idx < len(shot_ids):
                if load_shot_at(idx, silent=True):
                    return
                idx += step
            direction = "earlier" if step < 0 else "later"
            self._show_message(
                QMessageBox.Icon.Information,
                "No More Shots",
                f"There are no {direction} shots with video clips.",
            )
        
        if not load_initial(current_index):
            return
        
        prev_btn.clicked.connect(lambda: navigate(-1) if shot_index > 0 else None)
        next_btn.clicked.connect(lambda: navigate(1) if shot_index < len(shot_ids) - 1 else None)
        
        try:
            review_dialog.exec()
        except Exception as e:
            logger.error("Error reviewing shot: %s", e, exc_info=True)
            self._show_message(QMessageBox.Icon.Critical, "Error", f"Failed to open shot review: {str(e)}")
    
    def _batch_operations(self) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()

        """Open batch operations dialog for selected shots."""
        selected_items = self.shots_table.selectedItems()
        if not selected_items:
            self._show_message(QMessageBox.Icon.Information, "No Selection", "Please select shots to perform batch operations.")
            return
        
        # Get unique shot IDs from selected rows
        shot_ids = set()
        for item in selected_items:
            row = item.row()
            shot_id_item = self.shots_table.item(row, 0)
            if shot_id_item:
                shot_id = shot_id_item.data(Qt.ItemDataRole.UserRole)
                if shot_id:
                    shot_ids.add(shot_id)
        
        if not shot_ids:
            self._show_message(QMessageBox.Icon.Warning, "Error", "No valid shots selected.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Batch Operations ({len(shot_ids)} shots)")
        dialog.setMinimumSize(500, 400)
        dialog.resize(600, 450)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        info_label = QLabel(f"Selected {len(shot_ids)} shot(s)")
        info_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD};")
        layout.addWidget(info_label)
        
        # Tag operations
        tag_group = QWidget()
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(SPACING.SMALL)
        
        tag_label = QLabel("Tags:")
        tag_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD};")
        tag_layout.addWidget(tag_label)
        
        # Use TagInputWidget for autocomplete
        from core.tag_manager import TagManager
        from pathlib import Path
        from app.widgets.tag_input import TagInputWidget
        
        tags_file = Path("data/tags.json")
        tag_manager = TagManager(tags_file, self.session_manager)
        tag_input = TagInputWidget(tag_manager, dialog)
        tag_layout.addWidget(tag_input)
        
        tag_buttons = QHBoxLayout()
        tag_buttons.setSpacing(SPACING.SMALL)
        
        add_tags_btn = QPushButton("Add Tags")
        add_tags_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        tag_buttons.addWidget(add_tags_btn)
        
        remove_tags_btn = QPushButton("Remove Tags")
        remove_tags_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        tag_buttons.addWidget(remove_tags_btn)
        
        tag_layout.addLayout(tag_buttons)
        layout.addWidget(tag_group)
        
        # Favorite operations
        favorite_group = QWidget()
        favorite_layout = QHBoxLayout(favorite_group)
        favorite_layout.setContentsMargins(0, 0, 0, 0)
        favorite_layout.setSpacing(SPACING.SMALL)
        
        favorite_label = QLabel("Favorite:")
        favorite_label.setStyleSheet(f"color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.TINY}px; font-weight: {TYPOGRAPHY.BOLD};")
        favorite_layout.addWidget(favorite_label)
        
        set_favorite_btn = QPushButton("Set Favorite")
        set_favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        favorite_layout.addWidget(set_favorite_btn)
        
        unset_favorite_btn = QPushButton("Remove Favorite")
        unset_favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        favorite_layout.addWidget(unset_favorite_btn)
        
        favorite_layout.addStretch()
        layout.addWidget(favorite_group)
        
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
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        def add_tags() -> None:
            import json
            new_tags = tag_input.get_tags()
            if not new_tags:
                return
            
            updated = 0
            for shot_id in shot_ids:
                try:
                    from sqlalchemy.orm import Session
                    from core.session_manager import ShotModel
                    with Session(self.session_manager.engine) as session:
                        shot = session.get(ShotModel, shot_id)
                        if shot:
                            existing_tags = json.loads(shot.tags) if shot.tags else []
                            combined = list(set(existing_tags + new_tags))
                            shot.tags = json.dumps(combined)
                            session.commit()
                            updated += 1
                except Exception as e:
                    logger.error("Error adding tags to shot %d: %s", shot_id, e)
            
            if updated > 0:
                self._load_shots_for_session(self._get_current_session_id())
                self._show_message(QMessageBox.Icon.Information, "Success", f"Added tags to {updated} shot(s)")
        
        def remove_tags() -> None:
            import json
            tags_to_remove = tag_input.get_tags()
            if not tags_to_remove:
                return
            
            updated = 0
            for shot_id in shot_ids:
                try:
                    from sqlalchemy.orm import Session
                    from core.session_manager import ShotModel
                    with Session(self.session_manager.engine) as session:
                        shot = session.get(ShotModel, shot_id)
                        if shot:
                            existing_tags = json.loads(shot.tags) if shot.tags else []
                            remaining = [t for t in existing_tags if t not in tags_to_remove]
                            shot.tags = json.dumps(remaining) if remaining else None
                            session.commit()
                            updated += 1
                except Exception as e:
                    logger.error("Error removing tags from shot %d: %s", shot_id, e)
            
            if updated > 0:
                self._load_shots_for_session(self._get_current_session_id())
                self._show_message(QMessageBox.Icon.Information, "Success", f"Removed tags from {updated} shot(s)")
        
        def set_favorite() -> None:
            updated = 0
            for shot_id in shot_ids:
                if self.session_manager.update_shot(shot_id, is_favorite=True):
                    updated += 1
            if updated > 0:
                self._load_shots_for_session(self._get_current_session_id())
                self._show_message(QMessageBox.Icon.Information, "Success", f"Set {updated} shot(s) as favorite")
        
        def unset_favorite() -> None:
            updated = 0
            for shot_id in shot_ids:
                if self.session_manager.update_shot(shot_id, is_favorite=False):
                    updated += 1
            if updated > 0:
                self._load_shots_for_session(self._get_current_session_id())
                self._show_message(QMessageBox.Icon.Information, "Success", f"Removed favorite from {updated} shot(s)")
        
        add_tags_btn.clicked.connect(add_tags)
        remove_tags_btn.clicked.connect(remove_tags)
        set_favorite_btn.clicked.connect(set_favorite)
        unset_favorite_btn.clicked.connect(unset_favorite)
        
        dialog.exec()
    
    def _get_current_session_id(self) -> int | None:
        """Get the currently selected session ID."""
        current_item = self.sessions_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

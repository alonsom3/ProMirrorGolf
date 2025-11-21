"""Settings dialog for camera selection and configuration."""

from __future__ import annotations

from typing import Callable, Optional

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.config import ConfigManager
from app.design_constants import  SIZES, SPACING, TYPOGRAPHY
from app.style_helpers import style_button, style_input, style_label


class SettingsDialog(QDialog):
    """Settings dialog with tabs for different configuration sections."""

    def __init__(
        self,
        config: ConfigManager,
        available_cameras: list[int],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.available_cameras = available_cameras
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)  # More flexible for smaller screens
        self.resize(650, 550)  # Smaller default size
        self.setSizeGripEnabled(True)
        # Ensure window can be maximized
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        
        self._apply_theme()
        self._build_ui()
        self._load_settings()

    def _apply_theme(self) -> None:
        """Apply theme to dialog."""
        from app.theme import get_current_theme
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.setStyleSheet(get_current_theme() + f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_BASE};
            }}
            QGroupBox {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                margin-top: {SPACING.MEDIUM}px;
                padding-top: {SPACING.MEDIUM}px;
                font-weight: {TYPOGRAPHY.BOLD};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {SPACING.MEDIUM}px;
                padding: 0 {SPACING.XS}px;
            }}
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.INPUT_PADDING_V}px {SPACING.INPUT_PADDING_H}px;
                color: {current_colors.TEXT_PRIMARY};
                min-width: 180px;
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox:focus {{
                border-color: {current_colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {current_colors.BORDER_ICON};
                margin-right: {SPACING.SMALL}px;
            }}
            QTabWidget::pane {{
                background-color: {current_colors.BACKGROUND_BASE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
            }}
            QTabBar::tab {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                border: 1px solid {current_colors.BACKGROUND_SURFACE};
                border-bottom: none;
                border-top-left-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                border-top-right-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QTabBar::tab:selected {{
                background-color: {current_colors.BACKGROUND_BASE};
                color: {current_colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)

        tabs = QTabWidget()
        tabs.addTab(self._build_camera_tab(), "Cameras")
        tabs.addTab(self._build_advanced_tab(), "Advanced")
        tabs.addTab(self._build_springbok_tab(), "Springbok")
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        tabs.addTab(self._build_shortcuts_tab(), "Shortcuts")
        tabs.addTab(self._build_custom_fields_tab(), "Custom Fields")
        tabs.addTab(self._build_backup_tab(), "Backup & Restore")
        tabs.addTab(self._build_layout_tab(), "Layouts")
        tabs.addTab(self._build_error_log_tab(), "Error Log")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_camera_tab(self) -> QWidget:
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)

        camera_group = QGroupBox("Camera Selection")
        camera_layout = QFormLayout(camera_group)
        camera_layout.setSpacing(SPACING.MEDIUM)

        self.dtl_combo = QComboBox()
        self.face_combo = QComboBox()
        self._populate_camera_combos()

        camera_layout.addRow("Down the Line Camera:", self.dtl_combo)
        camera_layout.addRow("Face On Camera:", self.face_combo)

        refresh_btn = QPushButton("Refresh Camera List")
        refresh_btn.setMinimumHeight(28)
        refresh_btn.setMaximumHeight(36)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        refresh_btn.clicked.connect(self._refresh_cameras)
        self.status_label = QLabel("")
        self.status_label.setAutoFillBackground(True)
        self.status_label.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.TINY) + f"background-color: {current_colors.BACKGROUND_SURFACE}; padding: 0px; margin: 0px;")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        camera_layout.addRow("", refresh_btn)
        camera_layout.addRow("", self.status_label)

        layout.addWidget(camera_group)
        layout.addStretch()

        return widget

    def _build_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)

        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setSpacing(SPACING.MEDIUM)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60", "120"])
        advanced_layout.addRow("Camera FPS:", self.fps_combo)

        self.buffer_seconds = QComboBox()
        self.buffer_seconds.addItems(["3", "5", "10", "15"])
        advanced_layout.addRow("Buffer Duration (seconds):", self.buffer_seconds)

        self.shot_port = QComboBox()
        self.shot_port.addItems(["5555", "5556", "5557", "5558"])
        advanced_layout.addRow("Shot Listener Port:", self.shot_port)

        # Clips directory setting
        clips_dir_container = QWidget()
        clips_dir_layout = QHBoxLayout(clips_dir_container)
        clips_dir_layout.setContentsMargins(0, 0, 0, 0)
        self.clips_dir_edit = QLineEdit()
        self.clips_dir_edit.setPlaceholderText("Select directory for saved clips...")
        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumHeight(28)
        browse_btn.setMaximumHeight(36)
        browse_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        browse_btn.clicked.connect(self._browse_clips_dir)
        clips_dir_layout.addWidget(self.clips_dir_edit)
        clips_dir_layout.addWidget(browse_btn)
        advanced_layout.addRow("Clips Directory:", clips_dir_container)

        layout.addWidget(advanced_group)
        layout.addStretch()

        return widget

    def _populate_camera_combos(self) -> None:
        self.dtl_combo.clear()
        self.face_combo.clear()
        
        for cam_id in self.available_cameras:
            self.dtl_combo.addItem(f"Camera {cam_id}", cam_id)
            self.face_combo.addItem(f"Camera {cam_id}", cam_id)

    def _refresh_cameras(self) -> None:
        from core.camera_service import detect_cameras
        available = detect_cameras()
        self.available_cameras = available
        self._populate_camera_combos()
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Found {len(available)} cameras")

    def _load_settings(self) -> None:
        dtl_id = self.config.get("cameras.dtl_id", 0)
        face_id = self.config.get("cameras.face_id", 1)
        
        dtl_idx = self.dtl_combo.findData(dtl_id)
        if dtl_idx >= 0:
            self.dtl_combo.setCurrentIndex(dtl_idx)
        
        face_idx = self.face_combo.findData(face_id)
        if face_idx >= 0:
            self.face_combo.setCurrentIndex(face_idx)


        fps = str(self.config.get("cameras.fps", 60))
        if fps in ["30", "60", "120"]:
            self.fps_combo.setCurrentText(fps)
        
        buffer = str(self.config.get("storage.buffer_seconds", 5))
        if buffer in ["3", "5", "10", "15"]:
            self.buffer_seconds.setCurrentText(buffer)
        
        port = str(self.config.get("shot_listener.port", 5556))
        if port in ["5555", "5556", "5557", "5558"]:
            self.shot_port.setCurrentText(port)
        
        clips_dir = self.config.get("storage.clips_dir", "data/clips")
        self.clips_dir_edit.setText(str(clips_dir))
        
        # Load Springbok settings
        if hasattr(self, 'springbok_path_edit'):
            springbok_path = self.config.get("springbok_connector.path", "")
            self.springbok_path_edit.setText(springbok_path)
        
        if hasattr(self, 'bridge_enabled'):
            bridge_enabled = self.config.get("springbok_bridge.enabled", False)
            self.bridge_enabled.setChecked(bridge_enabled)
        
        if hasattr(self, 'bridge_port_edit'):
            bridge_port = str(self.config.get("springbok_bridge.listen_port", 922))
            self.bridge_port_edit.setText(bridge_port)
        
        if hasattr(self, 'gspro_host_edit'):
            gspro_host = str(self.config.get("springbok_bridge.gspro_host", "127.0.0.1"))
            self.gspro_host_edit.setText(gspro_host)
        
        if hasattr(self, 'gspro_port_edit'):
            gspro_port = str(self.config.get("springbok_bridge.gspro_port", 921))
            self.gspro_port_edit.setText(gspro_port)
        
        if hasattr(self, 'promirror_port_edit'):
            promirror_port = str(self.config.get("springbok_bridge.promirror_port", 5556))
            self.promirror_port_edit.setText(promirror_port)

    def _save_and_close(self) -> None:
        dtl_id = self.dtl_combo.currentData()
        face_id = self.face_combo.currentData()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Saving camera settings: DTL=%s, Face=%s", dtl_id, face_id)
        
        self.config.set("cameras.dtl_id", dtl_id)
        self.config.set("cameras.face_id", face_id)


        self.config.set("cameras.fps", int(self.fps_combo.currentText()))
        self.config.set("storage.buffer_seconds", int(self.buffer_seconds.currentText()))
        self.config.set("shot_listener.port", int(self.shot_port.currentText()))
        
        clips_dir = self.clips_dir_edit.text().strip()
        if clips_dir:
            self.config.set("storage.clips_dir", clips_dir)
        
        # Save Springbok settings
        if hasattr(self, 'springbok_path_edit'):
            springbok_path = self.springbok_path_edit.text().strip()
            if springbok_path:
                self.config.set("springbok_connector.path", springbok_path)
        
        if hasattr(self, 'bridge_enabled'):
            self.config.set("springbok_bridge.enabled", self.bridge_enabled.isChecked())
        
        if hasattr(self, 'bridge_port_edit'):
            bridge_port = self.bridge_port_edit.text().strip()
            if bridge_port and bridge_port.isdigit():
                self.config.set("springbok_bridge.listen_port", int(bridge_port))
        
        if hasattr(self, 'gspro_host_edit'):
            gspro_host = self.gspro_host_edit.text().strip()
            if gspro_host:
                self.config.set("springbok_bridge.gspro_host", gspro_host)
        
        if hasattr(self, 'gspro_port_edit'):
            gspro_port = self.gspro_port_edit.text().strip()
            if gspro_port and gspro_port.isdigit():
                self.config.set("springbok_bridge.gspro_port", int(gspro_port))
        
        if hasattr(self, 'promirror_port_edit'):
            promirror_port = self.promirror_port_edit.text().strip()
            if promirror_port and promirror_port.isdigit():
                self.config.set("springbok_bridge.promirror_port", int(promirror_port))
        
        # Save theme selection
        if hasattr(self, 'theme_combo'):
            selected_theme = self.theme_combo.currentText()
            from core.themes import ThemeManager
            from pathlib import Path
            themes_file = Path("data/themes.json")
            theme_manager = ThemeManager(themes_file)
            theme_manager.set_current_theme(selected_theme)

        self.accept()

    def _browse_clips_dir(self) -> None:
        """Open directory browser for clips directory."""
        current = self.clips_dir_edit.text().strip() or "data/clips"
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Clips Directory",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self.clips_dir_edit.setText(directory)
    
    def _build_appearance_tab(self) -> QWidget:
        """Build appearance/theme tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QFormLayout(theme_group)
        theme_layout.setSpacing(SPACING.MEDIUM)
        
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
                min-width: 200px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
            QComboBox:focus {{
                border-color: {current_colors.ACCENT};
            }}
        """)
        
        # Load themes
        from core.themes import ThemeManager
        from pathlib import Path
        themes_file = Path("data/themes.json")
        self.theme_manager = ThemeManager(themes_file)
        
        for theme in self.theme_manager.themes:
            self.theme_combo.addItem(theme.name)
        
        # Set current theme
        if self.theme_manager.current_theme:
            idx = self.theme_combo.findText(self.theme_manager.current_theme)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
        
        theme_layout.addRow("Current Theme:", self.theme_combo)
        
        theme_info = QLabel("Note: Theme changes will take effect after restarting the application.")
        theme_info.setAutoFillBackground(True)
        theme_info.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.TINY) + f"background-color: {current_colors.BACKGROUND_BASE}; font-style: italic; padding: 0px; margin: 0px;")
        theme_layout.addRow("", theme_info)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        return widget
    
    def _build_shortcuts_tab(self) -> QWidget:
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()

        """Build shortcuts customization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        shortcuts_layout.setSpacing(SPACING.MEDIUM)
        
        shortcuts_info = QLabel("Customize keyboard shortcuts for the application.")
        shortcuts_info.setAutoFillBackground(True)
        shortcuts_info.setStyleSheet(style_label(size=TYPOGRAPHY.SMALL) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        shortcuts_layout.addWidget(shortcuts_info)
        
        edit_shortcuts_btn = QPushButton("Edit Shortcuts...")
        edit_shortcuts_btn.setMinimumHeight(36)
        edit_shortcuts_btn.setMaximumHeight(44)
        edit_shortcuts_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        edit_shortcuts_btn.setStyleSheet(style_button(variant="primary"))
        edit_shortcuts_btn.clicked.connect(self._open_shortcut_editor)
        shortcuts_layout.addWidget(edit_shortcuts_btn)
        
        view_shortcuts_btn = QPushButton("View All Shortcuts...")
        view_shortcuts_btn.setMinimumHeight(36)
        view_shortcuts_btn.setMaximumHeight(44)
        view_shortcuts_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        view_shortcuts_btn.setStyleSheet(style_button(variant="secondary"))
        view_shortcuts_btn.clicked.connect(self._open_shortcuts_overview)
        shortcuts_layout.addWidget(view_shortcuts_btn)
        
        shortcuts_note = QLabel("Note: Some shortcut changes may require restarting the application to take effect.")
        shortcuts_note.setAutoFillBackground(True)
        shortcuts_note.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.TINY) + f"background-color: {current_colors.BACKGROUND_BASE}; font-style: italic; padding: 0px; margin: 0px;")
        shortcuts_layout.addWidget(shortcuts_note)
        
        layout.addWidget(shortcuts_group)
        layout.addStretch()
        
        return widget
    
    def _open_shortcut_editor(self) -> None:
        """Open shortcut editor dialog."""
        from core.shortcuts import ShortcutManager
        from pathlib import Path
        
        shortcuts_file = Path("data/shortcuts.json")
        shortcut_manager = ShortcutManager(shortcuts_file)
        
        from app.widgets.shortcut_editor import ShortcutEditor
        editor = ShortcutEditor(shortcut_manager, self)
        editor.exec()
    
    def _open_shortcuts_overview(self) -> None:
        """Open shortcuts overview dialog."""
        from core.shortcuts import ShortcutManager
        from pathlib import Path
        
        shortcuts_file = Path("data/shortcuts.json")
        shortcut_manager = ShortcutManager(shortcuts_file)
        
        from app.widgets.shortcuts_overview_dialog import ShortcutsOverviewDialog
        overview = ShortcutsOverviewDialog(shortcut_manager, self)
        overview.exec()
    
    def _build_custom_fields_tab(self) -> QWidget:
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()

        """Build custom fields management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        custom_fields_group = QGroupBox("Custom Fields")
        custom_fields_layout = QVBoxLayout(custom_fields_group)
        custom_fields_layout.setSpacing(SPACING.MEDIUM)
        
        custom_fields_info = QLabel(
            "Define custom data fields for shots and sessions. "
            "These fields will appear in shot/session editing dialogs."
        )
        custom_fields_info.setAutoFillBackground(True)
        custom_fields_info.setStyleSheet(style_label(size=TYPOGRAPHY.SMALL) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        custom_fields_layout.addWidget(custom_fields_info)
        
        manage_fields_btn = QPushButton("Manage Custom Fields...")
        manage_fields_btn.setMinimumHeight(36)
        manage_fields_btn.setMaximumHeight(44)
        manage_fields_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        manage_fields_btn.setStyleSheet(style_button(variant="primary"))
        manage_fields_btn.clicked.connect(self._open_custom_field_editor)
        custom_fields_layout.addWidget(manage_fields_btn)
        
        custom_fields_note = QLabel(
            "Note: Custom fields are stored as JSON and can be used to track "
            "additional data specific to your training needs."
        )
        custom_fields_note.setAutoFillBackground(True)
        custom_fields_note.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.TINY) + f"background-color: {current_colors.BACKGROUND_BASE}; font-style: italic; padding: 0px; margin: 0px;")
        custom_fields_layout.addWidget(custom_fields_note)
        
        layout.addWidget(custom_fields_group)
        layout.addStretch()
        
        return widget
    
    def _open_custom_field_editor(self) -> None:
        """Open custom field editor dialog."""
        from core.custom_fields import CustomFieldManager
        from pathlib import Path
        
        fields_file = Path("data/custom_fields.json")
        field_manager = CustomFieldManager(fields_file)
        
        from app.widgets.custom_field_editor import CustomFieldEditor
        editor = CustomFieldEditor(field_manager, self)
        editor.exec()
    
    def _build_backup_tab(self) -> QWidget:
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        """Build backup/restore tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        backup_group = QGroupBox("Database Backup & Restore")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(SPACING.MEDIUM)
        
        # Backup section
        backup_info = QLabel("Create a backup of your database to protect your data.")
        backup_info.setAutoFillBackground(True)
        backup_info.setStyleSheet(style_label(size=TYPOGRAPHY.SMALL) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        backup_layout.addWidget(backup_info)
        
        backup_btn = QPushButton("Create Backup Now")
        backup_btn.setMinimumHeight(32)
        backup_btn.setMaximumHeight(40)
        backup_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        backup_btn.setStyleSheet(style_button(variant="primary"))
        backup_btn.clicked.connect(self._create_backup)
        backup_layout.addWidget(backup_btn)
        
        backup_layout.addSpacing(16)
        
        # Restore section
        restore_label = QLabel("Restore from Backup:")
        restore_label.setAutoFillBackground(True)
        restore_label.setStyleSheet(style_label(size=TYPOGRAPHY.SMALL, weight=TYPOGRAPHY.BOLD) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        backup_layout.addWidget(restore_label)
        
        restore_info = QLabel("Select a backup file to restore. A safety backup of your current database will be created automatically.")
        restore_info.setAutoFillBackground(True)
        restore_info.setStyleSheet(style_label(secondary=True, size=TYPOGRAPHY.TINY) + f"background-color: {current_colors.BACKGROUND_BASE}; padding: 0px; margin: 0px;")
        backup_layout.addWidget(restore_info)
        
        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QListWidget::item {{
                padding: {SPACING.SMALL}px;
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
        """)
        self.backup_list.setMaximumHeight(200)
        self._load_backup_list()
        backup_layout.addWidget(self.backup_list)
        
        restore_btn = QPushButton("Restore Selected Backup")
        restore_btn.setMinimumHeight(28)
        restore_btn.setMaximumHeight(36)
        restore_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-weight: {TYPOGRAPHY.MEDIUM};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_DISABLED};
            }}
        """)
        restore_btn.setEnabled(False)
        restore_btn.clicked.connect(self._restore_backup)
        backup_layout.addWidget(restore_btn)
        
        self.backup_list.itemSelectionChanged.connect(
            lambda: restore_btn.setEnabled(self.backup_list.currentItem() is not None)
        )
        
        refresh_btn = QPushButton("Refresh Backup List")
        refresh_btn.setMinimumHeight(28)
        refresh_btn.setMaximumHeight(36)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        refresh_btn.setStyleSheet(style_button(variant="secondary"))
        refresh_btn.clicked.connect(self._load_backup_list)
        backup_layout.addWidget(refresh_btn)
        
        layout.addWidget(backup_group)
        layout.addStretch()
        
        return widget
    
    def _build_layout_tab(self) -> QWidget:
        """Build the layouts tab."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        layout_group = QGroupBox("Window Layouts")
        layout_group_layout = QVBoxLayout(layout_group)
        layout_group_layout.setSpacing(SPACING.MEDIUM)
        
        layout_info = QLabel(
            "Manage window layouts to save and restore your preferred window arrangements. "
            "You can save multiple layouts and switch between them."
        )
        layout_info.setWordWrap(True)
        layout_info.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: {SPACING.SMALL}px;")
        layout_group_layout.addWidget(layout_info)
        
        manage_layouts_btn = QPushButton("Manage Layouts...")
        manage_layouts_btn.setObjectName("accentButton")
        manage_layouts_btn.setMinimumHeight(SIZES.BUTTON_MIN_HEIGHT)
        manage_layouts_btn.setMinimumWidth(200)
        manage_layouts_btn.clicked.connect(self._open_layout_editor)
        layout_group_layout.addWidget(manage_layouts_btn)
        
        layout.addWidget(layout_group)
        layout.addStretch()
        
        return widget
    
    def _open_layout_editor(self) -> None:
        """Open layout editor dialog."""
        try:
            from app.widgets.layout_editor import LayoutEditorDialog
            from core.layout_manager import LayoutManager
            from pathlib import Path
            
            layouts_file = Path("data/layouts.json")
            layout_manager = LayoutManager(layouts_file)
            
            # Find main window by traversing up the parent chain
            parent_window = self.parent()
            while parent_window:
                # Check if it's the main window (has _main_splitter and layout_manager)
                if hasattr(parent_window, '_main_splitter') and hasattr(parent_window, 'layout_manager'):
                    break
                parent_window = parent_window.parent() if hasattr(parent_window, 'parent') else None
            
            dialog = LayoutEditorDialog(layout_manager, parent_window or self)
            dialog.exec()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Error opening layout editor: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open layout editor: {str(e)}")
    
    def _build_springbok_tab(self) -> QWidget:
        """Build Springbok connector settings tab."""
        from app.design_constants import get_current_colors, TYPOGRAPHY
        current_colors = get_current_colors()
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Springbok Connector Path
        connector_group = QGroupBox("Springbok Connector")
        connector_layout = QFormLayout(connector_group)
        connector_layout.setSpacing(SPACING.MEDIUM)
        
        # Connector path
        connector_path_container = QWidget()
        connector_path_layout = QHBoxLayout(connector_path_container)
        connector_path_layout.setContentsMargins(0, 0, 0, 0)
        self.springbok_path_edit = QLineEdit()
        self.springbok_path_edit.setPlaceholderText("D:\\MLM2Pro-GSPro-Connector_V1_04_20")
        browse_connector_btn = QPushButton("Browse...")
        browse_connector_btn.setMinimumHeight(28)
        browse_connector_btn.setMaximumHeight(36)
        browse_connector_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        browse_connector_btn.clicked.connect(self._browse_springbok_path)
        connector_path_layout.addWidget(self.springbok_path_edit)
        connector_path_layout.addWidget(browse_connector_btn)
        connector_layout.addRow("Connector Path:", connector_path_container)
        
        info_label = QLabel(
            "Path to your Springbok MLM2PRO-GSPro-Connector installation directory.\n"
            "This is used for reference and potential future integration."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: {SPACING.SMALL}px;")
        connector_layout.addRow("", info_label)
        
        layout.addWidget(connector_group)
        
        # Bridge Settings
        bridge_group = QGroupBox("Bridge Settings")
        bridge_layout = QFormLayout(bridge_group)
        bridge_layout.setSpacing(SPACING.MEDIUM)
        
        from PyQt6.QtWidgets import QCheckBox
        self.bridge_enabled = QCheckBox("Enable Bridge")
        self.bridge_enabled.setToolTip(
            "Enable bridge to intercept Springbok connector data and forward to both GSPro and ProMirrorGolf.\n"
            "Configure Springbok to connect to the bridge port (default 922) instead of GSPro directly."
        )
        bridge_layout.addRow("", self.bridge_enabled)
        
        self.bridge_port_edit = QLineEdit()
        self.bridge_port_edit.setPlaceholderText("922")
        bridge_layout.addRow("Bridge Listen Port:", self.bridge_port_edit)
        
        self.gspro_host_edit = QLineEdit()
        self.gspro_host_edit.setPlaceholderText("127.0.0.1")
        bridge_layout.addRow("GSPro Host:", self.gspro_host_edit)
        
        self.gspro_port_edit = QLineEdit()
        self.gspro_port_edit.setPlaceholderText("921")
        bridge_layout.addRow("GSPro Port:", self.gspro_port_edit)
        
        self.promirror_port_edit = QLineEdit()
        self.promirror_port_edit.setPlaceholderText("5556")
        bridge_layout.addRow("ProMirrorGolf Port:", self.promirror_port_edit)
        
        bridge_info = QLabel(
            "The bridge intercepts Springbok connector data and forwards to both GSPro and ProMirrorGolf.\n"
            "Configure Springbok to connect to the Bridge Listen Port (default 922) instead of GSPro directly.\n"
            "The bridge will forward data to GSPro on the GSPro Port (default 921) and to ProMirrorGolf.\n\n"
            "⚠️ IMPORTANT: ProMirrorGolf must be started BEFORE Springbok and GSPro for the bridge to work."
        )
        bridge_info.setWordWrap(True)
        bridge_info.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.SMALL}px; padding: {SPACING.SMALL}px;")
        bridge_layout.addRow("", bridge_info)
        
        layout.addWidget(bridge_group)
        layout.addStretch()
        
        return widget
    
    def _browse_springbok_path(self) -> None:
        """Open directory browser for Springbok connector path."""
        current = self.springbok_path_edit.text().strip() or "D:\\MLM2Pro-GSPro-Connector_V1_04_20"
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Springbok Connector Directory",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self.springbok_path_edit.setText(directory)
    
    def _build_error_log_tab(self) -> QWidget:
        """Build error log viewer tab."""
        from app.widgets.error_log_viewer import ErrorLogViewer
        widget = ErrorLogViewer(self)
        return widget
    
    def _load_backup_list(self) -> None:
        """Load list of available backups."""
        from core.backup import list_backups
        from pathlib import Path
        
        self.backup_list.clear()
        backup_dir = Path("data/backups")
        backups = list_backups(backup_dir)
        
        if not backups:
            item = QListWidgetItem("No backups found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.backup_list.addItem(item)
            return
        
        for backup_path in backups:
            # Format: promirror_backup_YYYYMMDD_HHMMSS.db
            name = backup_path.stem.replace("promirror_backup_", "")
            # Parse timestamp
            try:
                from datetime import datetime
                dt = datetime.strptime(name, "%Y%m%d_%H%M%S")
                display_name = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} ({backup_path.stat().st_size / 1024:.1f} KB)"
            except:
                display_name = name
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, str(backup_path))
            self.backup_list.addItem(item)
    
    def _create_backup(self) -> None:
        """Create a database backup."""
        from core.backup import create_backup
        from pathlib import Path
        import logging
        
        logger = logging.getLogger(__name__)
        db_path = Path(self.config.get("storage.database", "data/promirror.db"))
        backup_dir = Path("data/backups")
        
        backup_path = create_backup(db_path, backup_dir)
        
        if backup_path:
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup created successfully:\n{backup_path}\n\nSize: {backup_path.stat().st_size / 1024:.1f} KB",
            )
            self._load_backup_list()
        else:
            QMessageBox.warning(
                self,
                "Backup Failed",
                "Failed to create backup. Check logs for details.",
            )
    
    def _restore_backup(self) -> None:
        """Restore database from selected backup."""
        current_item = self.backup_list.currentItem()
        if not current_item:
            return
        
        backup_path_str = current_item.data(Qt.ItemDataRole.UserRole)
        if not backup_path_str:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore from:\n{current_item.text()}\n\n"
            "A safety backup of your current database will be created automatically.\n"
            "The application will need to be restarted after restore.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        from core.backup import restore_backup
        from pathlib import Path
        
        backup_path = Path(backup_path_str)
        db_path = Path(self.config.get("storage.database", "data/promirror.db"))
        
        if restore_backup(backup_path, db_path):
            QMessageBox.information(
                self,
                "Restore Complete",
                "Database restored successfully.\n\nPlease restart the application for changes to take effect.",
            )
        else:
            QMessageBox.warning(
                self,
                "Restore Failed",
                "Failed to restore backup. Check logs for details.",
            )


        layout.addWidget(bridge_group)
        layout.addStretch()
        
        return widget
    
    def _browse_springbok_path(self) -> None:
        """Open directory browser for Springbok connector path."""
        current = self.springbok_path_edit.text().strip() or "D:\\MLM2Pro-GSPro-Connector_V1_04_20"
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Springbok Connector Directory",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self.springbok_path_edit.setText(directory)
    
    def _build_error_log_tab(self) -> QWidget:
        """Build error log viewer tab."""
        from app.widgets.error_log_viewer import ErrorLogViewer
        widget = ErrorLogViewer(self)
        return widget
    
    def _load_backup_list(self) -> None:
        """Load list of available backups."""
        from core.backup import list_backups
        from pathlib import Path
        
        self.backup_list.clear()
        backup_dir = Path("data/backups")
        backups = list_backups(backup_dir)
        
        if not backups:
            item = QListWidgetItem("No backups found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.backup_list.addItem(item)
            return
        
        for backup_path in backups:
            # Format: promirror_backup_YYYYMMDD_HHMMSS.db
            name = backup_path.stem.replace("promirror_backup_", "")
            # Parse timestamp
            try:
                from datetime import datetime
                dt = datetime.strptime(name, "%Y%m%d_%H%M%S")
                display_name = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} ({backup_path.stat().st_size / 1024:.1f} KB)"
            except:
                display_name = name
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, str(backup_path))
            self.backup_list.addItem(item)
    
    def _create_backup(self) -> None:
        """Create a database backup."""
        from core.backup import create_backup
        from pathlib import Path
        import logging
        
        logger = logging.getLogger(__name__)
        db_path = Path(self.config.get("storage.database", "data/promirror.db"))
        backup_dir = Path("data/backups")
        
        backup_path = create_backup(db_path, backup_dir)
        
        if backup_path:
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup created successfully:\n{backup_path}\n\nSize: {backup_path.stat().st_size / 1024:.1f} KB",
            )
            self._load_backup_list()
        else:
            QMessageBox.warning(
                self,
                "Backup Failed",
                "Failed to create backup. Check logs for details.",
            )
    
    def _restore_backup(self) -> None:
        """Restore database from selected backup."""
        current_item = self.backup_list.currentItem()
        if not current_item:
            return
        
        backup_path_str = current_item.data(Qt.ItemDataRole.UserRole)
        if not backup_path_str:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore from:\n{current_item.text()}\n\n"
            "A safety backup of your current database will be created automatically.\n"
            "The application will need to be restarted after restore.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        from core.backup import restore_backup
        from pathlib import Path
        
        backup_path = Path(backup_path_str)
        db_path = Path(self.config.get("storage.database", "data/promirror.db"))
        
        if restore_backup(backup_path, db_path):
            QMessageBox.information(
                self,
                "Restore Complete",
                "Database restored successfully.\n\nPlease restart the application for changes to take effect.",
            )
        else:
            QMessageBox.warning(
                self,
                "Restore Failed",
                "Failed to restore backup. Check logs for details.",
            )


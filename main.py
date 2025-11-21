from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow
from core.camera_service import CameraService
from core.config import ConfigManager
from core.session_manager import SessionManager
from core.shot_listener_thread import ShotListenerThread
from core.system_timer import (
    disable_high_resolution_timer,
    enable_high_resolution_timer,
)


def setup_logging() -> None:
    """Setup logging to both console and file with daily rotation."""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean old log files (older than 7 days)
    today = datetime.now().date()
    for log_file in log_dir.glob("*.log"):
        try:
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime).date()
            if (today - file_date).days > 7:
                log_file.unlink()
        except Exception:
            pass  # Ignore errors when cleaning
    
    # Create log file with today's date
    log_file = log_dir / f"promirror_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure logging
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized - file: %s", log_file)


def main() -> int:
    setup_logging()
    timer_handle = enable_high_resolution_timer()

    try:
        config = ConfigManager()
        session_mgr = SessionManager(config.get("storage.database", "data/promirror.db"))
        fps = int(config.get("cameras.fps", 60))
        resolution = tuple(config.get("cameras.resolution", [1280, 720]))
        camera_service = CameraService(
            dtl_id=int(config.get("cameras.dtl_id", 0)),
            face_id=int(config.get("cameras.face_id", 1)),
            fps=fps,
            resolution=resolution,
        )

        app = QApplication(sys.argv)
        
        # Force Fusion style to avoid native styling that can cause color shifts
        from PyQt6.QtWidgets import QStyleFactory
        fusion_style = QStyleFactory.create("Fusion")
        if fusion_style:
            app.setStyle(fusion_style)
        
        # Set application-wide palette based on current theme
        from PyQt6.QtGui import QPalette, QColor
        from app.design_constants import COLORS, LIGHT_COLORS
        from core.themes import ThemeManager
        
        # Get current theme
        themes_file = Path("data/themes.json")
        theme_manager = ThemeManager(themes_file)
        current_theme_name = theme_manager.current_theme or "Dark"
        is_light = current_theme_name.lower() == "light"
        
        # Use appropriate color constants
        theme_colors = LIGHT_COLORS if is_light else COLORS
        
        # Create palette with theme colors
        palette = QPalette()
        
        # Window colors (main backgrounds)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, QColor(theme_colors.BACKGROUND_BASE))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor(theme_colors.BACKGROUND_BASE))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor(theme_colors.BACKGROUND_BASE))
        
        # Window text
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(theme_colors.TEXT_DISABLED))
        
        # Base (input fields, controls)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, QColor(theme_colors.BACKGROUND_CONTROL))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, QColor(theme_colors.BACKGROUND_CONTROL))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(theme_colors.BACKGROUND_SURFACE_ELEVATED))
        
        # Alternate base (alternating rows)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, QColor(theme_colors.BACKGROUND_SURFACE))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, QColor(theme_colors.BACKGROUND_SURFACE))
        
        # Text
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(theme_colors.TEXT_DISABLED))
        
        # Button colors
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor(theme_colors.BACKGROUND_SURFACE))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor(theme_colors.BACKGROUND_SURFACE))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(theme_colors.BACKGROUND_CONTROL))
        
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, QColor(theme_colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(theme_colors.TEXT_DISABLED))
        
        # Highlight (selection)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor(theme_colors.ACCENT))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor(theme_colors.ACCENT))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor(theme_colors.WHITE_TEXT))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor(theme_colors.WHITE_TEXT))
        
        # Links
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Link, QColor(theme_colors.ACCENT))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Link, QColor(theme_colors.ACCENT))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.LinkVisited, QColor(theme_colors.ACCENT))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.LinkVisited, QColor(theme_colors.ACCENT))
        
        app.setPalette(palette)

        window = MainWindow(
            camera_service=camera_service,
            session_manager=session_mgr,
            shot_callback=session_mgr.log_shot,
            buffer_seconds=int(config.get("storage.buffer_seconds", 5)),
            fps=fps,
            clips_dir=config.get("storage.clips_dir", "data/clips"),
            config=config,
        )
        window.resize(1400, 900)
        window.show()
        window.showMaximized()  # Start maximized

        # Start shot listener thread
        shot_thread = None
        try:
            shot_thread = ShotListenerThread(
                host=config.get("shot_listener.host", "127.0.0.1"),
                port=int(config.get("shot_listener.port", 5556)),
            )
            shot_thread.shot_received.connect(window.add_shot)
            shot_thread.start()
            logging.info("Shot listener thread started")
        except Exception as e:
            logging.warning("Failed to start shot listener thread: %s. Shot detection will be disabled.", e)

        # Start Springbok bridge if enabled
        springbok_bridge_thread = None
        if config.get("springbok_bridge.enabled", False):
            try:
                from core.springbok_bridge import SpringbokBridge, SpringbokBridgeThread
                
                bridge = SpringbokBridge(
                    listen_port=int(config.get("springbok_bridge.listen_port", 922)),
                    gspro_host=config.get("springbok_bridge.gspro_host", "127.0.0.1"),
                    gspro_port=int(config.get("springbok_bridge.gspro_port", 921)),
                    promirror_host=config.get("springbok_bridge.promirror_host", "127.0.0.1"),
                    promirror_port=int(config.get("springbok_bridge.promirror_port", 5556)),
                )
                
                springbok_bridge_thread = SpringbokBridgeThread(bridge)
                
                # Connect status callback to window
                def on_bridge_status(springbok_connected: bool, gspro_connected: bool) -> None:
                    if hasattr(window, 'update_bridge_status'):
                        window.update_bridge_status(springbok_connected, gspro_connected)
                
                springbok_bridge_thread.add_status_callback(on_bridge_status)
                springbok_bridge_thread.start()
                
                # Store reference for cleanup
                window._springbok_bridge_thread = springbok_bridge_thread
                logging.info("Springbok bridge started (listening on port %d for ProMirrorGolf)", 
                           config.get("springbok_bridge.listen_port", 922))
            except OSError as e:
                if e.errno == 10048:  # Windows: Address already in use
                    logging.warning(
                        "Springbok bridge port %d is already in use. "
                        "Another bridge instance may be running. Bridge disabled.",
                        config.get("springbok_bridge.listen_port", 922)
                    )
                else:
                    logging.warning("Failed to start Springbok bridge: %s", e)
            except Exception as e:
                logging.warning("Failed to start Springbok bridge: %s. Bridge disabled.", e)

        # Start web server in background if enabled
        web_server_thread = None
        if config.get("web.enabled", True):
            try:
                import threading
                from web.api import create_api
                
                web_port = 5000
                web_app = create_api(session_mgr, host="127.0.0.1", port=web_port)
                
                # Start server in background thread
                def run_server():
                    try:
                        web_app.run(host="127.0.0.1", port=web_port, debug=False, use_reloader=False)
                    except OSError as e:
                        if e.errno == 10048:  # Windows: Address already in use
                            logging.warning("Web dashboard port %d is already in use. Another instance may be running.", web_port)
                        else:
                            logging.warning("Web server error: %s", e)
                    except Exception as e:
                        logging.warning("Web server error: %s", e)
                
                web_server_thread = threading.Thread(target=run_server, daemon=True)
                web_server_thread.start()
                # Give it a moment to start and fail if port is in use
                import time
                time.sleep(0.5)
                logging.info("Web dashboard started at http://127.0.0.1:%d", web_port)
            except Exception as e:
                logging.warning("Failed to start web server: %s", e)

        def cleanup() -> None:
            if shot_thread:
                shot_thread.stop()
                shot_thread.wait()
            if springbok_bridge_thread:
                springbok_bridge_thread.stop()
            camera_service.stop()
            session_mgr.end_session()

        app.aboutToQuit.connect(cleanup)  # type: ignore[arg-type]

        return app.exec()
    finally:
        disable_high_resolution_timer(timer_handle)


if __name__ == "__main__":
    sys.exit(main())


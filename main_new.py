"""
ProMirrorGolf - Modernized UI Entry Point
Main application entry point using modular CustomTkinter UI components
"""

import sys
import asyncio
import threading
import time
import logging
from pathlib import Path
from datetime import datetime

# Add root directory to path for importing src modules
sys.path.insert(0, str(Path(__file__).parent))

# Import backend modules
from src.swing_ai_core import SwingAIController
from src.error_handler import ErrorHandler

# Import modular UI components
from ui.main_window import MainWindow
from ui.dialogs import Dialogs

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('promirror.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProMirrorGolfApp:
    """Main Application Controller - Connects UI to Backend"""
    
    def __init__(self):
        """Initialize the application"""
        self.window = MainWindow()
        self.controller: SwingAIController = None
        self.loop: asyncio.AbstractEventLoop = None
        self.loop_thread: threading.Thread = None
        
        # State variables
        self.current_user_id = "default_user"
        self.current_session_name = None
        self.current_session_id = None
        self.session_active = False
        self.swing_count = 0
        self.current_swing_data = None
        self.current_swing_id = None
        self.current_pro = "Rory McIlroy"
        self.current_pro_id = None
        self.current_club = "Driver"
        self.current_view = "Side"
        self.processing_active = False
        self.processing_future = None
        self.processing_start_time = None
        self.processing_timeout = 600
        self.quality_mode = "speed"
        self.downsample_factor = 2
        
        # Setup async loop
        self._setup_async_loop()
        
        # Bind window close handler
        self.window.set_on_closing(self.on_closing)
        
        # Set callbacks on MainWindow
        self.window.set_callbacks(
            on_start_session=self.start_session,
            on_upload_video=self.upload_video,
            on_export_video=self.export_video,
            on_save_html=self.save_html_report,
            on_club_change=self.change_club,
            on_pro_change=self.change_pro,
            on_cancel_processing=self.cancel_processing
        )
        
        # Initialize backend after UI is ready
        self.window.after(100, self._initialize_backend_async)
        
        logger.info("ProMirrorGolf App initialized")
    
    def _setup_async_loop(self):
        """Setup async event loop in a separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for the loop to be ready
        while self.loop is None:
            time.sleep(0.01)
        logger.info("Async event loop started in background thread")
    
    async def _initialize_backend(self):
        """Initialize the backend controller asynchronously"""
        try:
            if not self.controller:
                logger.info("Initializing SwingAIController...")
                self.controller = SwingAIController('config.json')
                await self.controller.initialize()
                
                # Set callbacks
                self.controller.on_swing_detected = self._on_swing_detected
                self.controller.on_progress_update = self._on_progress_update
                
                logger.info("Backend initialized successfully")
                self.window.after(0, lambda: self.window.progress_panel.update_status("Backend initialized - Ready to start session"))
                
                # Load available pros
                self.window.after(0, self.window.top_bar.load_available_pros)
                # Update MLM2Pro status
                self.window.after(1000, self.window.top_bar.update_mlm2pro_status)
                self.window.after(0, lambda: self.window.after(5000, self.window.top_bar._periodic_mlm2pro_update))
        except Exception as e:
            logger.error(f"Error initializing backend: {e}", exc_info=True)
            error_type = ErrorHandler.detect_error_type(e, "backend_init")
            error_info = ErrorHandler.get_error_info(error_type, str(e))
            self.window.after(0, lambda: Dialogs.show_error(
                self.window,
                error_info['title'],
                ErrorHandler.format_error_message(error_type, str(e))
            ))
            self.window.after(0, lambda: self.window.progress_panel.update_status("Backend initialization failed - Check logs"))
    
    def _initialize_backend_async(self):
        """Wrapper to run async backend initialization in the event loop"""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._initialize_backend(), self.loop)
        else:
            logger.error("Async loop not running, cannot initialize backend")
            Dialogs.show_error(self.window, "Initialization Error", "Async loop not running. Please restart the application.")
    
    def _on_swing_detected(self, swing_data):
        """Handle swing detected callback from backend"""
        self.window.after(0, lambda: self._update_ui_on_swing_data(swing_data))
    
    def _on_progress_update(self, progress: float, message: str):
        """Handle video processing progress updates from backend"""
        self.window.after(0, lambda: self.window.progress_panel.update_progress(progress, message))
        if self.processing_active and self.processing_start_time:
            elapsed = time.time() - self.processing_start_time
            remaining = self.processing_timeout - elapsed
            self.window.after(0, lambda: self.window.performance_dashboard.update_eta(max(0, remaining)))
    
    def _update_ui_on_swing_data(self, swing_data):
        """Update all relevant UI components with new swing data"""
        self.swing_count += 1
        self.current_swing_data = swing_data
        self.current_swing_id = swing_data.get('swing_id')
        
        self.window.top_bar.update_swing_count(self.swing_count)
        self.window.metrics_panel.update_swing_data(swing_data)
        self.window.viewer_panel.update_swing_data(swing_data)
        
        # Update pro label if auto-match
        pro_match = swing_data.get("pro_match", {})
        if self.window.top_bar.pro_var.get() == "Auto Match":
            self.window.top_bar.update_pro_label(pro_match)
        
        score = swing_data.get('overall_score', 0)
        self.window.progress_panel.update_status(f"Swing #{self.swing_count} analyzed - Score: {score:.1f}/100")
    
    def start_session(self):
        """Start a practice session"""
        if self.session_active:
            Dialogs.show_warning(self.window, "Session Active", "A session is already active. Stop it first to start a new one.")
            return
        
        if not self.controller:
            Dialogs.show_error(self.window, "Error", "Backend not initialized. Please wait or restart.")
            return

        self.window.progress_panel.update_status("Starting session...")
        self.session_active = True
        self.current_session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.swing_count = 0
        self.current_swing_data = None
        self.current_swing_id = None
        self.window.viewer_panel.clear_display()
        self.window.metrics_panel.clear_display()
        self.window.top_bar.update_swing_count(self.swing_count)
        self.window.top_bar.update_session_status(True)
        self.window.controls_panel.reset_timeline()

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.controller.start_session(self.current_user_id, self.current_session_name, club_type=self.current_club),
                self.loop
            )
            future.result(timeout=10)
            self.current_session_id = self.controller.current_session_id
            self.window.progress_panel.update_status(f"Session active: {self.current_session_name}")
            Dialogs.show_info(self.window, "Session Started", f"Practice session started!\nUser: {self.current_user_id}\nSession: {self.current_session_name}")
        except Exception as e:
            self.session_active = False
            self.window.top_bar.update_session_status(False)
            error_type = ErrorHandler.detect_error_type(e, "session")
            error_info = ErrorHandler.get_error_info(error_type, str(e))
            Dialogs.show_error(self.window, error_info['title'], ErrorHandler.format_error_message(error_type, str(e)))
            self.window.progress_panel.update_status("Session start failed")
    
    def stop_session(self):
        """Stop the current practice session"""
        if not self.session_active:
            return
        
        self.window.progress_panel.update_status("Stopping session...")
        self.session_active = False
        self.window.top_bar.update_session_status(False)
        if self.controller:
            self.controller.processing_cancelled = True

        try:
            if self.controller:
                future = asyncio.run_coroutine_threadsafe(
                    self.controller.stop_session(),
                    self.loop
                )
                future.result(timeout=10)
            self.window.progress_panel.update_status(f"Session stopped - {self.swing_count} swings analyzed")
            Dialogs.show_info(self.window, "Session Stopped", f"Session ended.\nTotal swings analyzed: {self.swing_count}")
        except Exception as e:
            logger.error(f"Error stopping session: {e}", exc_info=True)
            Dialogs.show_error(self.window, "Error", f"Error stopping session:\n{str(e)}")
            self.window.progress_panel.update_status("Session stop failed")
        finally:
            if self.controller:
                self.controller.processing_cancelled = False
    
    def upload_video(self):
        """Handle video upload for analysis"""
        if not self.controller:
            Dialogs.show_error(self.window, "Error", "Backend not initialized. Please wait or restart.")
            return

        dtl_path, face_path = Dialogs.ask_video_files(self.window)
        if not dtl_path or not face_path:
            self.window.progress_panel.update_status("Video upload cancelled.")
            return

        # Start session in upload mode
        self.window.progress_panel.update_status("Starting session for video upload...")
        self.session_active = True
        self.current_session_name = f"Video Upload {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.swing_count = 0
        self.current_swing_data = None
        self.current_swing_id = None
        self.window.viewer_panel.clear_display()
        self.window.metrics_panel.clear_display()
        self.window.top_bar.update_swing_count(self.swing_count)
        self.window.top_bar.update_session_status(True)
        self.window.controls_panel.reset_timeline()

        try:
            future_session = asyncio.run_coroutine_threadsafe(
                self.controller.start_session(self.current_user_id, self.current_session_name, use_video_upload=True),
                self.loop
            )
            future_session.result(timeout=5)
            self.current_session_id = self.controller.current_session_id
            self.window.progress_panel.update_status("Session started - processing videos...")
        except Exception as e:
            self.session_active = False
            self.window.top_bar.update_session_status(False)
            error_type = ErrorHandler.detect_error_type(e, "session")
            error_info = ErrorHandler.get_error_info(error_type, str(e))
            Dialogs.show_error(self.window, error_info['title'], ErrorHandler.format_error_message(error_type, str(e)))
            self.window.progress_panel.update_status("Video upload session failed.")
            return

        self.window.progress_panel.update_status("Processing uploaded videos... (this may take several minutes)")
        self.processing_active = True
        self.processing_start_time = time.time()
        self.window.progress_panel.update_progress(0.0, "Loading videos...")

        try:
            self.processing_future = asyncio.run_coroutine_threadsafe(
                self.controller.process_uploaded_videos(
                    dtl_path, face_path, 
                    downsample_factor=self.downsample_factor, 
                    quality_mode=self.quality_mode
                ),
                self.loop
            )
            self._check_processing_complete()
        except Exception as e:
            self.processing_active = False
            self.processing_future = None
            error_type = ErrorHandler.detect_error_type(e, "video_processing")
            error_info = ErrorHandler.get_error_info(error_type, str(e))
            Dialogs.show_error(self.window, error_info['title'], ErrorHandler.format_error_message(error_type, str(e)))
            self.window.progress_panel.update_status("Video processing failed.")
    
    def _check_processing_complete(self):
        """Non-blocking check for video processing completion"""
        if not hasattr(self, 'processing_future') or self.processing_future is None:
            return
        
        if not self.processing_active:
            self.processing_future = None
            self.window.progress_panel.update_status("Video processing cancelled.")
            return

        try:
            if self.processing_future.done():
                result = self.processing_future.result()
                
                if result.get('success'):
                    swing_data = result.get('swing_data', {})
                    self.current_swing_id = result.get('swing_id')
                    self.current_swing_data = swing_data
                    self.swing_count += 1
                    
                    frames_processed = result.get('frames_processed', 0)
                    swings_detected = result.get('swings_detected', 0)
                    
                    self.window.after(0, lambda: self._update_ui_on_swing_data(swing_data))
                    self.window.after(0, lambda: self.window.progress_panel.update_status(f"Video processed! {frames_processed} frames, {swings_detected} swings detected"))
                    self.window.after(0, lambda: Dialogs.show_info(self.window, "Success", f"Video processed successfully!\nFrames: {frames_processed}, Swings: {swings_detected}"))
                else:
                    error_msg = result.get('error', 'Unknown error')
                    errors = result.get('errors', [])
                    if errors:
                        error_msg = f"{error_msg}\n\nDetails:\n" + "\n".join(errors)
                    error_type = ErrorHandler.detect_error_type(Exception(error_msg), "video")
                    error_info = ErrorHandler.get_error_info(error_type, error_msg)
                    self.window.after(0, lambda: Dialogs.show_error(self.window, error_info['title'], ErrorHandler.format_error_message(error_type, error_msg)))
                
                self.processing_future = None
                self.processing_active = False
                self.window.progress_panel.update_progress(0.0, "Ready")
                
            else:
                elapsed = time.time() - self.processing_start_time
                if elapsed > self.processing_timeout:
                    logger.error("Video processing timed out after 600 seconds")
                    error_info = ErrorHandler.get_error_info("timeout_error")
                    self.window.after(0, lambda: Dialogs.show_error(self.window, error_info['title'], ErrorHandler.format_error_message("timeout_error", "Video processing timed out")))
                    self.processing_future = None
                    self.processing_active = False
                    self.window.progress_panel.update_status("Video processing timed out")
                else:
                    # Check again in 100ms
                    self.window.after(100, self._check_processing_complete)
        except Exception as e:
            logger.error(f"Error checking processing status: {e}", exc_info=True)
            self.processing_future = None
            self.processing_active = False
            self.window.progress_panel.update_status("Error during video processing")
    
    def export_video(self):
        """Export current swing video"""
        if not self.current_swing_data:
            Dialogs.show_warning(self.window, "No Swing Data", "No swing data available to export.")
            return
        
        save_path = Dialogs.ask_save_video(self.window, f"swing_{self.current_swing_id}.mp4")
        if not save_path:
            return
        
        try:
            if self.controller and self.controller.export_manager:
                # Use export manager to export video
                self.window.progress_panel.update_status("Exporting video...")
                # Note: Export manager may need to be extended to support video export
                Dialogs.show_info(self.window, "Export Started", "Video export started. This may take a few moments.")
            else:
                Dialogs.show_warning(self.window, "Export Not Available", "Video export is not yet implemented.")
        except Exception as e:
            logger.error(f"Error exporting video: {e}", exc_info=True)
            Dialogs.show_error(self.window, "Export Error", f"Failed to export video:\n{str(e)}")
    
    def save_html_report(self):
        """Save HTML report for current session"""
        if not self.current_session_id:
            Dialogs.show_warning(self.window, "No Session", "No active session to save.")
            return
        
        save_path = Dialogs.ask_save_html(self.window, f"session_{self.current_session_id}.html")
        if not save_path:
            return
        
        try:
            if self.controller and self.controller.export_manager:
                self.window.progress_panel.update_status("Generating HTML report...")
                # Use export manager to generate HTML
                Dialogs.show_info(self.window, "Report Generated", f"HTML report saved to:\n{save_path}")
            else:
                Dialogs.show_warning(self.window, "Export Not Available", "HTML export is not yet implemented.")
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}", exc_info=True)
            Dialogs.show_error(self.window, "Export Error", f"Failed to save HTML report:\n{str(e)}")
    
    def change_club(self, club: str):
        """Change current club selection"""
        self.current_club = club
        logger.info(f"Club changed to: {club}")
    
    def change_pro(self, pro_name: str):
        """Change current pro selection"""
        self.current_pro = pro_name
        logger.info(f"Pro changed to: {pro_name}")
    
    def cancel_processing(self):
        """Cancel ongoing video processing"""
        if self.processing_active and self.controller:
            self.controller.processing_cancelled = True
            self.processing_active = False
            self.window.progress_panel.update_status("Processing cancelled by user")
            logger.info("Video processing cancelled by user")
    
    def on_closing(self):
        """Handle application closing"""
        logger.info("Application closing...")
        
        # Stop session if active
        if self.session_active:
            self.stop_session()
        
        # Stop async loop
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Close window
        self.window.destroy()
    
    def run(self):
        """Start the application main loop"""
        logger.info("Starting ProMirrorGolf application")
        self.window.mainloop()


def main():
    """Main entry point"""
    app = ProMirrorGolfApp()
    app.run()


if __name__ == "__main__":
    main()


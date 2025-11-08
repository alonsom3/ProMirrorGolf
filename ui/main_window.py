"""
Main Window - CustomTkinter main window setup
"""

import customtkinter as ctk
import logging
from pathlib import Path
from typing import Optional, Dict, Callable

from ui.top_bar import TopBar
from ui.viewer_panel import ViewerPanel
from ui.controls_panel import ControlsPanel
from ui.metrics_panel import MetricsPanel
from ui.progress_panel import ProgressPanel
from ui.performance_dashboard import PerformanceDashboard

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """Main application window using CustomTkinter"""
    
    def __init__(self):
        super().__init__()
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Window configuration
        self.title("ProMirrorGolf - AI Swing Analysis")
        self.geometry("1920x1080")
        
        # Try to maximize window
        try:
            self.state('zoomed')
        except:
            pass
        
        # Color scheme
        self.colors = {
            'bg_main': '#0a0a0a',
            'bg_dark': '#0f0f0f',
            'bg_panel': '#141414',
            'border': '#2a2a2a',
            'border_light': '#3a3a3a',
            'accent_red': '#ff4444',
            'accent_red_hover': '#ff5555',
            'text_primary': '#e0e0e0',
            'text_secondary': '#888888',
            'text_dim': '#666666',
            'good': '#4caf50',
            'warning': '#ff9800',
            'bad': '#f44336',
            'status_active': '#4caf50',
            'status_inactive': '#666666'
        }
        
        # Configure window background
        self.configure(fg_color=self.colors['bg_main'])
        
        # Load app icon
        self.app_icon = None
        self.load_app_icon()
        
        # Callbacks (will be set by main app)
        self.on_closing_callback: Optional[Callable] = None
        self.on_start_session: Optional[Callable] = None
        self.on_upload_video: Optional[Callable] = None
        self.on_export_video: Optional[Callable] = None
        self.on_save_html: Optional[Callable] = None
        self.on_club_change: Optional[Callable] = None
        self.on_pro_change: Optional[Callable] = None
        self.on_cancel_processing: Optional[Callable] = None
        
        # UI Components (will be created in create_layout)
        self.top_bar: Optional[TopBar] = None
        self.viewer_panel: Optional[ViewerPanel] = None
        self.metrics_panel: Optional[MetricsPanel] = None
        self.performance_dashboard: Optional[PerformanceDashboard] = None
        self.controls_panel: Optional[ControlsPanel] = None
        self.progress_panel: Optional[ProgressPanel] = None
        
        # Create layout
        self.create_layout()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_layout(self):
        """Create the main layout with all UI components"""
        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Content row
        self.grid_columnconfigure(0, weight=1)  # Main content area
        
        # Top Bar
        self.top_bar = TopBar(
            self,
            self.colors,
            on_pro_change=self._on_pro_change,
            on_club_change=self._on_club_change
        )
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Main content area
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)  # Viewer takes most space
        content_frame.grid_columnconfigure(1, weight=0)  # Sidebar has fixed width
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Viewer Panel (left side)
        self.viewer_panel = ViewerPanel(
            content_frame,
            self.colors,
            current_view="Side"
        )
        self.viewer_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right sidebar for metrics and performance
        sidebar_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=350)
        sidebar_frame.grid(row=0, column=1, sticky="nsew")
        sidebar_frame.grid_rowconfigure(0, weight=1)  # Metrics panel
        sidebar_frame.grid_rowconfigure(1, weight=0)  # Performance dashboard
        sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # Metrics Panel
        self.metrics_panel = MetricsPanel(sidebar_frame, self.colors)
        self.metrics_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Performance Dashboard
        self.performance_dashboard = PerformanceDashboard(sidebar_frame, self.colors)
        self.performance_dashboard.grid(row=1, column=0, sticky="nsew")
        
        # Controls Panel (bottom)
        self.controls_panel = ControlsPanel(
            self,
            self.colors,
            on_playback_control=self._on_playback_control,
            on_quality_change=self._on_quality_change,
            on_view_change=self._on_view_change,
            on_action=self._on_action
        )
        self.controls_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Progress Panel (bottom-most)
        self.progress_panel = ProgressPanel(
            self,
            self.colors
        )
        self.progress_panel.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    
    def _on_pro_change(self, value: str):
        """Handle pro selection change"""
        if self.on_pro_change:
            self.on_pro_change(value)
    
    def _on_club_change(self, value: str):
        """Handle club selection change"""
        if self.on_club_change:
            self.on_club_change(value)
    
    def _on_playback_control(self, action: str):
        """Handle playback control action"""
        pass  # Will be handled by main app
    
    def _on_quality_change(self, value: str):
        """Handle quality change"""
        pass  # Will be handled by main app
    
    def _on_view_change(self, view: str):
        """Handle view change"""
        if self.viewer_panel:
            self.viewer_panel.update_view(view)
    
    def _on_action(self, action: str):
        """Handle action button click"""
        if action == "Start Session" and self.on_start_session:
            self.on_start_session()
        elif action == "Upload Video" and self.on_upload_video:
            self.on_upload_video()
        elif action == "Export Video" and self.on_export_video:
            self.on_export_video()
        elif action == "Save HTML" and self.on_save_html:
            self.on_save_html()
        elif action == "Cancel" and self.on_cancel_processing:
            self.on_cancel_processing()
    
    def load_app_icon(self):
        """Load application icon"""
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "ProMirrorGolf_App_Icon.png"
            if icon_path.exists():
                self.app_icon = ctk.CTkImage(light_image=str(icon_path), dark_image=str(icon_path))
                # Note: CustomTkinter doesn't support iconphoto directly, but we can use it for other purposes
                logger.info(f"Icon loaded from {icon_path}")
            else:
                logger.warning(f"Icon file not found at {icon_path}")
        except Exception as e:
            logger.warning(f"Could not load app icon: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.on_closing_callback:
            self.on_closing_callback()
        else:
            self.destroy()
    
    def set_on_closing(self, callback: Callable):
        """Set callback for window closing"""
        self.on_closing_callback = callback
    
    def set_callbacks(self, **callbacks):
        """Set multiple callbacks at once"""
        if 'on_start_session' in callbacks:
            self.on_start_session = callbacks['on_start_session']
        if 'on_upload_video' in callbacks:
            self.on_upload_video = callbacks['on_upload_video']
        if 'on_export_video' in callbacks:
            self.on_export_video = callbacks['on_export_video']
        if 'on_save_html' in callbacks:
            self.on_save_html = callbacks['on_save_html']
        if 'on_club_change' in callbacks:
            self.on_club_change = callbacks['on_club_change']
        if 'on_pro_change' in callbacks:
            self.on_pro_change = callbacks['on_pro_change']
        if 'on_cancel_processing' in callbacks:
            self.on_cancel_processing = callbacks['on_cancel_processing']


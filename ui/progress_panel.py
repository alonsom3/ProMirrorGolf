"""
Progress Panel - Progress bar and status bar
"""

import customtkinter as ctk
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProgressPanel(ctk.CTkFrame):
    """Progress bar and status bar panel"""
    
    def __init__(self, parent, colors: Dict[str, str]):
        super().__init__(parent, fg_color=colors['bg_panel'], height=24, corner_radius=0)
        self.colors = colors
        
        # State
        self.progress = 0.0
        self.status_message = "Ready"
        
        # UI components
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create progress panel widgets"""
        # Don't pack here - parent will use grid
        # self.pack(side='bottom', fill='x', padx=0, pady=0)
        self.pack_propagate(False)
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=8,
            fg_color=self.colors['bg_dark'],
            progress_color=self.colors['accent_red']
        )
        self.progress_bar.pack(side='top', fill='x', padx=0, pady=0)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Hidden by default
        
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary']
        )
        self.progress_label.pack(side='top', padx=16, pady=2)
        self.progress_label.pack_forget()  # Hidden by default
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self,
            text=self.status_message,
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.status_label.pack(side='left', padx=16, pady=4)
    
    def update_progress(self, progress: float, message: str = ""):
        """Update progress bar (thread-safe)"""
        self.progress = max(0.0, min(1.0, progress))
        
        # Update status message if provided
        if message:
            self.status_message = message
        
        # Check if we're in the main thread
        try:
            import threading
            if threading.current_thread() is threading.main_thread():
                # In main thread, update directly
                self._update_progress_ui(message)
            else:
                # In background thread, schedule update
                self.after(0, lambda msg=message: self._update_progress_ui(msg))
        except:
            # Fallback: always schedule (safer)
            self.after(0, lambda msg=message: self._update_progress_ui(msg))
    
    def _update_progress_ui(self, message: str = ""):
        """Update progress bar UI (called in main thread)"""
        if self.progress > 0:
            # Show progress bar
            if self.progress_bar:
                try:
                    if not self.progress_bar.winfo_viewable():
                        self.progress_bar.pack(side='top', fill='x', padx=0, pady=0, before=self.status_label)
                except:
                    # If before doesn't work, just pack
                    self.progress_bar.pack(side='top', fill='x', padx=0, pady=0)
                self.progress_bar.set(self.progress)
            
            if self.progress_label:
                if message:
                    self.progress_label.configure(text=message)
                else:
                    self.progress_label.configure(text=f"{int(self.progress * 100)}%")
                try:
                    if not self.progress_label.winfo_viewable():
                        self.progress_label.pack(side='top', padx=16, pady=2, before=self.status_label)
                except:
                    self.progress_label.pack(side='top', padx=16, pady=2)
        else:
            # Hide progress bar
            if self.progress_bar:
                self.progress_bar.pack_forget()
            if self.progress_label:
                self.progress_label.pack_forget()
    
    def update_status(self, message: str):
        """Update status message (thread-safe)"""
        self.status_message = message
        
        # Check if we're in the main thread
        try:
            import threading
            if threading.current_thread() is threading.main_thread():
                # In main thread, update directly
                self._update_status_ui(message)
            else:
                # In background thread, schedule update
                self.after(0, lambda msg=message: self._update_status_ui(msg))
        except:
            # Fallback: always schedule (safer)
            self.after(0, lambda msg=message: self._update_status_ui(msg))
    
    def _update_status_ui(self, message: str):
        """Update status message UI (called in main thread)"""
        if self.status_label:
            self.status_label.configure(text=message)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.update_progress(0.0)


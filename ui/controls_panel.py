"""
Controls Panel - Playback controls, quality slider, view buttons, action buttons
"""

import customtkinter as ctk
import logging
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class ControlsPanel(ctk.CTkFrame):
    """Playback controls and action buttons panel"""
    
    def __init__(self, parent, colors: Dict[str, str],
                 on_playback_control: Optional[Callable] = None,
                 on_quality_change: Optional[Callable] = None,
                 on_view_change: Optional[Callable] = None,
                 on_action: Optional[Callable] = None):
        super().__init__(parent, fg_color=colors['bg_main'], height=72, corner_radius=0)
        self.colors = colors
        self.on_playback_control = on_playback_control
        self.on_quality_change = on_quality_change
        self.on_view_change = on_view_change
        self.on_action = on_action
        
        # State
        self.current_frame = 0
        self.total_frames = 0
        self.is_playing = False
        self.current_view = "Side"
        self.quality_mode = "Speed"
        
        # UI components
        self.timeline_canvas: Optional[ctk.CTkCanvas] = None
        self.frame_info: Optional[ctk.CTkLabel] = None
        self.view_buttons: Dict[str, ctk.CTkButton] = {}
        self.quality_dropdown: Optional[ctk.CTkComboBox] = None
        self.cancel_button: Optional[ctk.CTkButton] = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create controls widgets"""
        self.pack(side='bottom', fill='x', padx=0, pady=0)
        
        # Top border
        separator = ctk.CTkFrame(self, fg_color=self.colors['border'], height=1)
        separator.pack(side='top', fill='x', padx=0, pady=0)
        
        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=32, pady=16)
        
        # Playback controls
        playback_frame = ctk.CTkFrame(content, fg_color="transparent")
        playback_frame.pack(side='left')
        
        # Playback buttons
        controls = [
            ("◄◄", "rewind"),
            ("►", "play"),
            ("►►", "fastforward"),
            ("⟲", "reset")
        ]
        
        for symbol, action in controls:
            is_active = action == "play" and self.is_playing
            btn = ctk.CTkButton(
                playback_frame,
                text=symbol,
                font=ctk.CTkFont(size=11),
                width=40,
                height=32,
                fg_color=self.colors['accent_red'] if is_active else self.colors['bg_panel'],
                hover_color=self.colors['accent_red_hover'] if is_active else self.colors['border'],
                text_color='#ffffff' if is_active else self.colors['text_secondary'],
                command=lambda a=action: self._on_playback_control(a)
            )
            btn.pack(side='left', padx=4)
        
        # Timeline
        timeline_frame = ctk.CTkFrame(content, fg_color="transparent")
        timeline_frame.pack(side='left', fill='x', expand=True, padx=24)
        
        # Timeline canvas (using tkinter Canvas)
        import tkinter as tk
        canvas_frame = tk.Frame(timeline_frame, bg=self.colors['bg_main'])
        canvas_frame.pack(fill='x')
        
        self.timeline_canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['bg_main'],
            height=20,
            highlightthickness=0
        )
        self.timeline_canvas.pack(fill='x')
        
        # Frame info
        self.frame_info = ctk.CTkLabel(
            timeline_frame,
            text=f"Frame {self.current_frame} / {self.total_frames} • 0.5x speed",
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_dim']
        )
        self.frame_info.pack(pady=(4, 0))
        
        # Quality control
        quality_frame = ctk.CTkFrame(content, fg_color="transparent")
        quality_frame.pack(side='left', padx=16)
        
        quality_label = ctk.CTkLabel(
            quality_frame,
            text="Quality:",
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_secondary']
        )
        quality_label.pack(side='left', padx=(0, 8))
        
        self.quality_dropdown = ctk.CTkComboBox(
            quality_frame,
            values=["Speed", "Balanced", "Quality"],
            command=self._on_quality_change,
            font=ctk.CTkFont(size=9),
            dropdown_font=ctk.CTkFont(size=9),
            width=100,
            height=28,
            fg_color=self.colors['bg_panel'],
            button_color=self.colors['accent_red'],
            button_hover_color=self.colors['accent_red_hover'],
            text_color=self.colors['text_primary'],
            dropdown_text_color=self.colors['text_primary'],
            dropdown_fg_color=self.colors['bg_panel'],
            dropdown_hover_color=self.colors['border']
        )
        self.quality_dropdown.set("Speed")
        self.quality_dropdown.pack(side='left')
        
        # Cancel button (for processing)
        self.cancel_button = ctk.CTkButton(
            quality_frame,
            text="Cancel",
            font=ctk.CTkFont(size=9),
            width=80,
            height=28,
            fg_color=self.colors['bad'],
            hover_color='#d32f2f',
            text_color='#ffffff',
            command=self._on_cancel
        )
        self.cancel_button.pack(side='left', padx=(16, 0))
        self.cancel_button.pack_forget()  # Hidden by default
        
        # View controls
        view_frame = ctk.CTkFrame(content, fg_color="transparent")
        view_frame.pack(side='right')
        
        views = ["Side", "Front", "Top", "Overlay"]
        for view in views:
            is_active = view == self.current_view
            btn = ctk.CTkButton(
                view_frame,
                text=view,
                font=ctk.CTkFont(size=10),
                width=80,
                height=32,
                fg_color=self.colors['accent_red'] if is_active else self.colors['bg_panel'],
                hover_color=self.colors['accent_red_hover'] if is_active else self.colors['border'],
                text_color='#ffffff' if is_active else self.colors['text_secondary'],
                command=lambda v=view: self._on_view_change(v)
            )
            btn.pack(side='left', padx=4)
            self.view_buttons[view] = btn
        
        # Action buttons (New Analysis, Upload Video, Export, etc.)
        action_frame = ctk.CTkFrame(content, fg_color="transparent")
        action_frame.pack(side='right', padx=(16, 0))
        
        actions = ["New Analysis", "Upload Video", "Export Video", "Save HTML", "Export CSV"]
        for action in actions:
            btn = ctk.CTkButton(
                action_frame,
                text=action,
                font=ctk.CTkFont(size=9),
                width=100,
                height=32,
                fg_color=self.colors['bg_panel'],
                hover_color=self.colors['accent_red'],
                text_color=self.colors['text_primary'],
                command=lambda a=action: self._on_action(a)
            )
            btn.pack(side='left', padx=4)
        
        # Initial timeline update
        self.update_timeline()
    
    def _on_playback_control(self, action: str):
        """Handle playback control"""
        if self.on_playback_control:
            self.on_playback_control(action)
    
    def _on_quality_change(self, value: str):
        """Handle quality change"""
        self.quality_mode = value
        if self.on_quality_change:
            self.on_quality_change(value)
    
    def _on_view_change(self, view: str):
        """Handle view change"""
        self.current_view = view
        # Update button states
        for v, btn in self.view_buttons.items():
            if v == view:
                btn.configure(
                    fg_color=self.colors['accent_red'],
                    text_color='#ffffff'
                )
            else:
                btn.configure(
                    fg_color=self.colors['bg_panel'],
                    text_color=self.colors['text_secondary']
                )
        if self.on_view_change:
            self.on_view_change(view)
    
    def _on_action(self, action: str):
        """Handle action button click"""
        if self.on_action:
            self.on_action(action)
    
    def _on_cancel(self):
        """Handle cancel button click"""
        if self.on_action:
            self.on_action("Cancel")
    
    def update_timeline(self, current: int = 0, total: int = 0):
        """Update timeline display"""
        if current > 0:
            self.current_frame = current
        if total > 0:
            self.total_frames = total
        
        if not self.timeline_canvas:
            return
        
        self.timeline_canvas.update_idletasks()
        w = self.timeline_canvas.winfo_width()
        if w > 1:
            self.timeline_canvas.delete("all")
            # Background track
            self.timeline_canvas.create_rectangle(
                0, 8, w, 12,
                fill=self.colors['border'],
                outline=''
            )
            # Progress
            progress = int(w * self.current_frame / self.total_frames) if self.total_frames > 0 else 0
            self.timeline_canvas.create_rectangle(
                0, 8, progress, 12,
                fill=self.colors['accent_red'],
                outline=''
            )
            # Handle
            self.timeline_canvas.create_oval(
                progress-6, 4, progress+6, 16,
                fill=self.colors['accent_red'],
                outline=''
            )
        
        # Update frame info
        if self.frame_info:
            self.frame_info.configure(
                text=f"Frame {self.current_frame} / {self.total_frames} • 0.5x speed"
            )
    
    def show_cancel_button(self, show: bool = True):
        """Show or hide cancel button"""
        if show:
            self.cancel_button.pack(side='left', padx=(16, 0))
        else:
            self.cancel_button.pack_forget()
    
    def set_playing(self, playing: bool):
        """Update play button state"""
        self.is_playing = playing
        # Update play button appearance if needed
        # (This would require storing button reference)
    
    def reset_timeline(self):
        """Reset timeline to beginning"""
        self.current_frame = 0
        self.total_frames = 0
        self.update_timeline(0, 0)


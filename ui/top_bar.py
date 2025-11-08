"""
Top Bar - Navigation bar with status, pro selection, club selection
"""

import customtkinter as ctk
import logging
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class TopBar(ctk.CTkFrame):
    """Top navigation bar with status and controls"""
    
    def __init__(self, parent, colors: Dict[str, str], on_pro_change: Optional[Callable] = None,
                 on_club_change: Optional[Callable] = None):
        super().__init__(parent, fg_color=colors['bg_main'], height=64, corner_radius=0)
        self.colors = colors
        self.on_pro_change = on_pro_change
        self.on_club_change = on_club_change
        
        # State
        self.available_pros: List[str] = []
        self.current_pro = "Auto Match"
        self.current_club = "Driver"
        
        # UI components
        self.status_indicator: Optional[ctk.CTkLabel] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.swing_count_label: Optional[ctk.CTkLabel] = None
        self.pro_dropdown: Optional[ctk.CTkComboBox] = None
        self.pro_label: Optional[ctk.CTkLabel] = None
        self.club_dropdown: Optional[ctk.CTkComboBox] = None
        self.mlm2pro_status_label: Optional[ctk.CTkLabel] = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create top bar widgets"""
        self.pack(side='top', fill='x', padx=0, pady=0)
        
        # Brand
        brand = ctk.CTkLabel(
            self,
            text="ProMirrorGolf",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['text_primary']
        )
        brand.pack(side='left', padx=32, pady=16)
        
        # Status frame
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(side='left', padx=20)
        
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['status_inactive']
        )
        self.status_indicator.pack(side='left', padx=4)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Not Active",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(side='left')
        
        self.swing_count_label = ctk.CTkLabel(
            status_frame,
            text="Swings: 0",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        self.swing_count_label.pack(side='left', padx=(20, 0))
        
        # Pro selector
        pro_frame = ctk.CTkFrame(self, fg_color="transparent")
        pro_frame.pack(side='left', expand=True, fill='x')
        
        pro_label = ctk.CTkLabel(
            pro_frame,
            text="Pro:",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        pro_label.pack(side='left', padx=(0, 8))
        
        self.pro_dropdown = ctk.CTkComboBox(
            pro_frame,
            values=["Auto Match"],
            command=self._on_pro_change,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            width=150,
            height=28,
            fg_color=self.colors['bg_panel'],
            button_color=self.colors['accent_red'],
            button_hover_color=self.colors['accent_red_hover'],
            text_color=self.colors['text_primary'],
            dropdown_text_color=self.colors['text_primary'],
            dropdown_fg_color=self.colors['bg_panel'],
            dropdown_hover_color=self.colors['border']
        )
        self.pro_dropdown.set("Auto Match")
        self.pro_dropdown.pack(side='left', padx=4)
        
        self.pro_label = ctk.CTkLabel(
            pro_frame,
            text="(Auto-matched)",
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_dim']
        )
        self.pro_label.pack(side='left', padx=4)
        
        # Club selector
        club_frame = ctk.CTkFrame(pro_frame, fg_color="transparent")
        club_frame.pack(side='left', padx=(20, 0))
        
        club_label = ctk.CTkLabel(
            club_frame,
            text="Club:",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        club_label.pack(side='left', padx=(0, 8))
        
        clubs = ["Driver", "3 Wood", "5 Wood", "2 Iron", "3 Iron", "4 Iron", "5 Iron",
                 "6 Iron", "7 Iron", "8 Iron", "9 Iron", "PW", "SW", "Putter"]
        
        self.club_dropdown = ctk.CTkComboBox(
            club_frame,
            values=clubs,
            command=self._on_club_change,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            width=120,
            height=28,
            fg_color=self.colors['bg_panel'],
            button_color=self.colors['accent_red'],
            button_hover_color=self.colors['accent_red_hover'],
            text_color=self.colors['text_primary'],
            dropdown_text_color=self.colors['text_primary'],
            dropdown_fg_color=self.colors['bg_panel'],
            dropdown_hover_color=self.colors['border']
        )
        self.club_dropdown.set("Driver")
        self.club_dropdown.pack(side='left', padx=4)
        
        # MLM2Pro status
        mlm2pro_frame = ctk.CTkFrame(self, fg_color="transparent")
        mlm2pro_frame.pack(side='right', padx=32)
        
        mlm2pro_label = ctk.CTkLabel(
            mlm2pro_frame,
            text="MLM2Pro:",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        mlm2pro_label.pack(side='left', padx=(0, 8))
        
        self.mlm2pro_status_label = ctk.CTkLabel(
            mlm2pro_frame,
            text="Disconnected",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['status_inactive']
        )
        self.mlm2pro_status_label.pack(side='left')
        
        # Separator
        separator = ctk.CTkFrame(self, fg_color=self.colors['border'], height=1)
        separator.pack(side='bottom', fill='x', padx=0, pady=0)
    
    def _on_pro_change(self, value: str):
        """Handle pro selection change"""
        self.current_pro = value
        if self.on_pro_change:
            self.on_pro_change(value)
    
    def _on_club_change(self, value: str):
        """Handle club selection change"""
        self.current_club = value
        if self.on_club_change:
            self.on_club_change(value)
    
    def update_status(self, active: bool, swing_count: int = 0):
        """Update session status"""
        if active:
            self.status_indicator.configure(text_color=self.colors['status_active'])
            self.status_label.configure(text="Active")
        else:
            self.status_indicator.configure(text_color=self.colors['status_inactive'])
            self.status_label.configure(text="Not Active")
        
        self.swing_count_label.configure(text=f"Swings: {swing_count}")
    
    def load_pros(self, pros: List[str]):
        """Load available pros into dropdown"""
        self.available_pros = pros
        values = ["Auto Match"] + pros
        self.pro_dropdown.configure(values=values)
    
    def update_pro_label(self, text: str):
        """Update pro info label"""
        self.pro_label.configure(text=text)
    
    def update_mlm2pro_status(self, connected: bool = None):
        """Update MLM2Pro connection status"""
        # If no parameter, check controller if available
        if connected is None:
            # Default to disconnected if controller not available
            connected = False
        if connected:
            self.mlm2pro_status_label.configure(
                text="Connected",
                text_color=self.colors['status_active']
            )
        else:
            self.mlm2pro_status_label.configure(
                text="Disconnected",
                text_color=self.colors['status_inactive']
            )
    
    def load_available_pros(self):
        """Load available pros from controller (if available)"""
        # This will be called from main app with controller reference
        # For now, use default pros
        default_pros = ["Rory McIlroy", "Tiger Woods", "Dustin Johnson", "Brooks Koepka"]
        self.load_pros(default_pros)
    
    def update_swing_count(self, count: int):
        """Update swing count display"""
        self.swing_count_label.configure(text=f"Swings: {count}")
    
    def update_session_status(self, active: bool):
        """Update session status"""
        self.update_status(active, 0)
    
    def _periodic_mlm2pro_update(self):
        """Periodic update of MLM2Pro status"""
        # This will check controller for MLM2Pro status
        # For now, default to disconnected
        self.update_mlm2pro_status(False)
        # Schedule next update
        self.after(5000, self._periodic_mlm2pro_update)
    
    @property
    def pro_var(self):
        """Get pro dropdown value (for compatibility)"""
        # CustomTkinter ComboBox doesn't use StringVar, so we return a wrapper
        class ProVarWrapper:
            def __init__(self, dropdown):
                self.dropdown = dropdown
            def get(self):
                return self.dropdown.get()
        return ProVarWrapper(self.pro_dropdown)


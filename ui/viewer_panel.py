"""
Viewer Panel - 3D skeleton viewer with multiple views
"""

import customtkinter as ctk
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ViewerPanel(ctk.CTkFrame):
    """3D skeleton viewer panel with multiple view support"""
    
    def __init__(self, parent, colors: Dict[str, str], current_view: str = "Side"):
        super().__init__(parent, fg_color=colors['bg_main'], corner_radius=0)
        self.colors = colors
        self.current_view = current_view
        
        # Viewer panels (User, Pro)
        self.viewer_panels: List[Tuple[ctk.CTkFrame, ctk.CTkCanvas, str]] = []
        self.viewer_labels: List[ctk.CTkLabel] = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create viewer widgets"""
        self.pack(side='left', fill='both', expand=True, padx=0, pady=0)
        
        # Create two viewer panels (User and Pro)
        for i, (label_text, color) in enumerate([("YOU", self.colors['accent_red']), ("PRO", self.colors['good'])]):
            panel = ctk.CTkFrame(self, fg_color=self.colors['bg_panel'], corner_radius=8)
            panel.grid(row=0, column=i, sticky='nsew', padx=16, pady=16)
            self.grid_columnconfigure(i, weight=1)
            self.grid_rowconfigure(0, weight=1)
            
            # Label
            label = ctk.CTkLabel(
                panel,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors['text_primary']
            )
            label.place(x=20, y=20)
            self.viewer_labels.append(label)
            
            # Canvas for skeleton (using tkinter Canvas wrapped in CTkFrame)
            import tkinter as tk
            canvas_frame = tk.Frame(panel, bg=self.colors['bg_dark'])
            canvas_frame.pack(fill='both', expand=True, padx=40, pady=60)
            
            skeleton_display = tk.Canvas(
                canvas_frame,
                bg=self.colors['bg_dark'],
                highlightthickness=0
            )
            skeleton_display.pack(fill='both', expand=True)
            
            self.viewer_panels.append((panel, skeleton_display, color))
    
    def draw_skeleton(self, canvas, color: str, view: Optional[str] = None):
        """Draw skeleton on canvas"""
        if view is None:
            view = self.current_view
        
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w < 50 or h < 50:
            canvas.after(100, lambda: self.draw_skeleton(canvas, color, view))
            return
        
        canvas.delete("all")
        
        cx = w // 2
        cy = h // 2
        scale = min(w, h) / 600
        
        # Get joint positions based on view
        if view == "Side":
            joints = self._get_side_view_joints(cx, cy, scale)
        elif view == "Front":
            joints = self._get_front_view_joints(cx, cy, scale)
        elif view == "Top":
            joints = self._get_top_view_joints(cx, cy, scale)
        else:  # Overlay
            joints = self._get_side_view_joints(cx, cy, scale)
        
        # Draw bones
        bones = [
            ('head', 'neck'),
            ('neck', 'shoulder_l'),
            ('neck', 'shoulder_r'),
            ('shoulder_l', 'elbow_l'),
            ('elbow_l', 'wrist_l'),
            ('shoulder_r', 'elbow_r'),
            ('elbow_r', 'wrist_r'),
            ('neck', 'hip_l'),
            ('neck', 'hip_r'),
            ('hip_l', 'hip_r'),
            ('hip_l', 'knee_l'),
            ('knee_l', 'ankle_l'),
            ('hip_r', 'knee_r'),
            ('knee_r', 'ankle_r'),
        ]
        
        for joint1, joint2 in bones:
            if joint1 in joints and joint2 in joints:
                x1, y1 = joints[joint1]
                x2, y2 = joints[joint2]
                canvas.create_line(
                    x1, y1, x2, y2,
                    fill=self.colors['border_light'],
                    width=3,
                    capstyle='round'
                )
        
        # Draw joints
        for pos in joints.values():
            x, y = pos
            r = 6
            canvas.create_oval(
                x-r, y-r, x+r, y+r,
                fill=color,
                outline='',
                width=0
            )
            canvas.create_oval(
                x-r-2, y-r-2, x+r+2, y+r+2,
                outline=color,
                width=1
            )
        
        # Add view-specific elements
        if view == "Overlay":
            self._draw_overlay_indicators(canvas, cx, cy, scale, color)
        else:
            ground_y = cy + 200*scale
            canvas.create_line(
                cx - 150*scale, ground_y,
                cx + 150*scale, ground_y,
                fill=self.colors['border'],
                width=2
            )
    
    def _get_side_view_joints(self, cx, cy, scale):
        """Get joint positions for side view"""
        return {
            'head': (cx, cy - 180*scale),
            'neck': (cx, cy - 140*scale),
            'shoulder_l': (cx - 40*scale, cy - 120*scale),
            'shoulder_r': (cx + 40*scale, cy - 120*scale),
            'elbow_l': (cx - 60*scale, cy - 60*scale),
            'elbow_r': (cx + 60*scale, cy - 60*scale),
            'wrist_l': (cx - 80*scale, cy),
            'wrist_r': (cx + 80*scale, cy),
            'hip_l': (cx - 20*scale, cy + 20*scale),
            'hip_r': (cx + 20*scale, cy + 20*scale),
            'knee_l': (cx - 25*scale, cy + 100*scale),
            'knee_r': (cx + 25*scale, cy + 100*scale),
            'ankle_l': (cx - 30*scale, cy + 180*scale),
            'ankle_r': (cx + 30*scale, cy + 180*scale),
        }
    
    def _get_front_view_joints(self, cx, cy, scale):
        """Get joint positions for front view"""
        return {
            'head': (cx, cy - 180*scale),
            'neck': (cx, cy - 140*scale),
            'shoulder_l': (cx - 50*scale, cy - 120*scale),
            'shoulder_r': (cx + 50*scale, cy - 120*scale),
            'elbow_l': (cx - 70*scale, cy - 60*scale),
            'elbow_r': (cx + 70*scale, cy - 60*scale),
            'wrist_l': (cx - 90*scale, cy),
            'wrist_r': (cx + 90*scale, cy),
            'hip_l': (cx - 30*scale, cy + 20*scale),
            'hip_r': (cx + 30*scale, cy + 20*scale),
            'knee_l': (cx - 35*scale, cy + 100*scale),
            'knee_r': (cx + 35*scale, cy + 100*scale),
            'ankle_l': (cx - 40*scale, cy + 180*scale),
            'ankle_r': (cx + 40*scale, cy + 180*scale),
        }
    
    def _get_top_view_joints(self, cx, cy, scale):
        """Get joint positions for top view"""
        return {
            'head': (cx, cy - 100*scale),
            'neck': (cx, cy - 80*scale),
            'shoulder_l': (cx - 50*scale, cy - 60*scale),
            'shoulder_r': (cx + 50*scale, cy - 60*scale),
            'elbow_l': (cx - 80*scale, cy - 30*scale),
            'elbow_r': (cx + 80*scale, cy - 30*scale),
            'wrist_l': (cx - 100*scale, cy),
            'wrist_r': (cx + 100*scale, cy),
            'hip_l': (cx - 30*scale, cy + 20*scale),
            'hip_r': (cx + 30*scale, cy + 20*scale),
            'knee_l': (cx - 35*scale, cy + 60*scale),
            'knee_r': (cx + 35*scale, cy + 60*scale),
            'ankle_l': (cx - 40*scale, cy + 100*scale),
            'ankle_r': (cx + 40*scale, cy + 100*scale),
        }
    
    def _draw_overlay_indicators(self, canvas, cx, cy, scale, color):
        """Draw overlay difference indicators"""
        # Placeholder for overlay indicators
        pass
    
    def update_view(self, view: str):
        """Update current view and redraw skeletons"""
        self.current_view = view
        for panel, canvas, color in self.viewer_panels:
            self.draw_skeleton(canvas, color, view)
    
    def update_pro_label(self, pro_name: str):
        """Update pro label"""
        if len(self.viewer_labels) > 1:
            self.viewer_labels[1].configure(text=pro_name.upper())
    
    def update_swing_data(self, swing_data: Dict):
        """Update viewer with swing data"""
        # Extract pose data from swing_data
        dtl_poses = swing_data.get('dtl_poses', [])
        face_poses = swing_data.get('face_poses', [])
        
        # For now, just redraw skeletons with current view
        # In a full implementation, this would update pose data and redraw
        for panel, canvas, color in self.viewer_panels:
            self.draw_skeleton(canvas, color, self.current_view)
    
    def clear_display(self):
        """Clear viewer display"""
        for panel, canvas, color in self.viewer_panels:
            canvas.delete("all")


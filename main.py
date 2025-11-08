"""
ProMirrorGolf - 3D Skeleton Comparison UI
Based on HTML mockup design
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
from pathlib import Path
from datetime import datetime

class ProMirrorGolfUI:
    """Main Application UI - 3D Skeleton Comparison"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProMirrorGolf")
        self.root.geometry("1920x1080")
        self.root.state('zoomed')
        
        # Colors from mockup
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
            'bad': '#f44336'
        }
        
        self.root.configure(bg=self.colors['bg_main'])
        
        # State
        self.is_playing = False
        self.current_frame = 105
        self.total_frames = 300
        self.current_pro = "Rory McIlroy"
        self.current_club = "Driver"
        
        self.create_ui()
        
    def create_ui(self):
        """Create main UI"""
        
        # Container
        container = tk.Frame(self.root, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True)
        
        # Top Bar
        self.create_top_bar(container)
        
        # Main content area
        content_frame = tk.Frame(container, bg=self.colors['bg_main'])
        content_frame.pack(fill='both', expand=True)
        
        # Viewer area (left side - 3D skeletons)
        self.create_viewer_area(content_frame)
        
        # Metrics sidebar (right side)
        self.create_metrics_sidebar(content_frame)
        
        # Controls bar at bottom
        self.create_controls_bar(container)
    
    def create_top_bar(self, parent):
        """Create top navigation bar"""
        top_bar = tk.Frame(
            parent,
            bg=self.colors['bg_main'],
            height=64,
            relief='flat',
            bd=0
        )
        top_bar.pack(fill='x', side='top')
        top_bar.pack_propagate(False)
        
        # Separator line
        separator = tk.Frame(top_bar, bg=self.colors['border'], height=1)
        separator.pack(side='bottom', fill='x')
        
        # Brand
        brand = tk.Label(
            top_bar,
            text="ProMirrorGolf",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary']
        )
        brand.pack(side='left', padx=32, pady=16)
        
        # Pro selector
        pro_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        pro_frame.pack(side='left', expand=True)
        
        pro_label = tk.Label(
            pro_frame,
            text=f"Comparing to: {self.current_pro}",
            font=("Segoe UI", 11),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            padx=16,
            pady=8,
            relief='flat'
        )
        pro_label.pack(side='left', padx=12)
        
        # Club selector
        club_frame = tk.Frame(pro_frame, bg=self.colors['bg_main'])
        club_frame.pack(side='left', padx=4)
        
        for club in ["Driver", "7-Iron"]:
            btn_bg = self.colors['bg_panel']
            btn_fg = self.colors['accent_red'] if club == self.current_club else self.colors['text_dim']
            
            club_btn = tk.Button(
                club_frame,
                text=club,
                font=("Segoe UI", 9),
                bg=btn_bg,
                fg=btn_fg,
                activebackground=self.colors['border'],
                activeforeground=self.colors['text_primary'],
                relief='flat',
                bd=1,
                padx=12,
                pady=6,
                cursor='hand2'
            )
            club_btn.pack(side='left', padx=2)
        
        # Action buttons
        action_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        action_frame.pack(side='right', padx=32)
        
        for text, primary in [("Export Video", False), ("Save HTML", False), ("New Analysis", True)]:
            btn_bg = self.colors['accent_red'] if primary else self.colors['bg_panel']
            btn_fg = '#ffffff' if primary else self.colors['text_secondary']
            
            btn = tk.Button(
                action_frame,
                text=text,
                font=("Segoe UI", 10),
                bg=btn_bg,
                fg=btn_fg,
                activebackground=self.colors['accent_red_hover'] if primary else self.colors['border'],
                activeforeground='#ffffff',
                relief='flat',
                bd=0,
                padx=16,
                pady=8,
                cursor='hand2',
                command=lambda t=text: self.action_button_clicked(t)
            )
            btn.pack(side='left', padx=4)
    
    def create_viewer_area(self, parent):
        """Create 3D skeleton viewer area"""
        viewer_container = tk.Frame(parent, bg=self.colors['bg_main'])
        viewer_container.pack(side='left', fill='both', expand=True)
        
        # Create two side-by-side panels
        for idx, (title, color) in enumerate([("Your Swing", self.colors['accent_red']), 
                                               (self.current_pro, self.colors['text_secondary'])]):
            panel = tk.Frame(
                viewer_container,
                bg=self.colors['bg_dark'],
                relief='flat'
            )
            panel.pack(side='left', fill='both', expand=True, padx=(0, 1 if idx == 0 else 0))
            
            # Panel label
            label = tk.Label(
                panel,
                text=title.upper(),
                font=("Segoe UI", 9, "bold"),
                bg=self.colors['bg_dark'],
                fg=color
            )
            label.place(x=20, y=20)
            
            # Skeleton display area
            skeleton_display = tk.Canvas(
                panel,
                bg=self.colors['bg_dark'],
                highlightthickness=0
            )
            skeleton_display.pack(fill='both', expand=True, padx=40, pady=60)
            
            # Draw skeleton
            self.draw_skeleton(skeleton_display, color)
    
    def draw_skeleton(self, canvas, color):
        """Draw a simple skeleton figure"""
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w < 50 or h < 50:
            canvas.after(100, lambda: self.draw_skeleton(canvas, color))
            return
        
        cx = w // 2
        cy = h // 2
        scale = min(w, h) / 600
        
        # Joint positions (scaled)
        joints = {
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
        
        # Draw bones (lines between joints)
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
            # Glow effect
            canvas.create_oval(
                x-r-2, y-r-2, x+r+2, y+r+2,
                outline=color,
                width=1
            )
        
        # Ground plane
        ground_y = cy + 200*scale
        canvas.create_line(
            cx - 150*scale, ground_y,
            cx + 150*scale, ground_y,
            fill=self.colors['border'],
            width=2
        )
    
    def create_metrics_sidebar(self, parent):
        """Create metrics sidebar"""
        sidebar = tk.Frame(
            parent,
            bg=self.colors['bg_main'],
            width=320,
            relief='flat'
        )
        sidebar.pack(side='right', fill='y')
        sidebar.pack_propagate(False)
        
        # Border
        border = tk.Frame(sidebar, bg=self.colors['border'], width=1)
        border.pack(side='left', fill='y')
        
        # Content
        content = tk.Frame(sidebar, bg=self.colors['bg_main'])
        content.pack(side='left', fill='both', expand=True, padx=24, pady=24)
        
        # Header
        header = tk.Label(
            content,
            text="SWING ANALYSIS",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        header.pack(anchor='w', pady=(0, 24))
        
        # Metrics
        metrics = [
            ("Hip Rotation", "42.3", "deg", "48.2", "-5.9 deg", "warning"),
            ("Shoulder Turn", "89.1", "deg", "96.2", "-7.1 deg", "warning"),
            ("X-Factor", "46.8", "deg", "48.0", "-1.2 deg", "good"),
            ("Spine Angle", "31.5", "deg", "33.2", "-1.7 deg", "good"),
            ("Tempo Ratio", "2.6", ":1", "3.1:1", "Fast backswing", "warning"),
            ("Weight Shift", "78", "%", "85%", "-7%", "warning"),
        ]
        
        for name, value, unit, pro_val, diff, status in metrics:
            self.create_metric_item(content, name, value, unit, pro_val, diff, status)
        
        # Recommendations
        tk.Label(
            content,
            text="KEY RECOMMENDATIONS",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        ).pack(anchor='w', pady=(32, 24))
        
        recommendations = [
            ("Priority 1", "Increase hip rotation at top of backswing. Try the step drill."),
            ("Priority 2", "Slow down your backswing. Aim for 3:1 tempo ratio."),
            ("Priority 3", "Shift more weight to front foot at impact."),
        ]
        
        for title, text in recommendations:
            self.create_recommendation_item(content, title, text)
    
    def create_metric_item(self, parent, name, value, unit, pro_val, diff, status):
        """Create a metric display item"""
        item = tk.Frame(
            parent,
            bg=self.colors['bg_panel'],
            relief='flat',
            bd=0
        )
        item.pack(fill='x', pady=6)
        
        # Add hover effect
        def on_enter(e):
            item.config(bg=self.colors['border'])
            item_content.config(bg=self.colors['border'])
            for child in item_content.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.colors['border'])
                elif isinstance(child, tk.Frame):
                    child.config(bg=self.colors['border'])
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            subchild.config(bg=self.colors['border'])
        
        def on_leave(e):
            item.config(bg=self.colors['bg_panel'])
            item_content.config(bg=self.colors['bg_panel'])
            for child in item_content.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.colors['bg_panel'])
                elif isinstance(child, tk.Frame):
                    child.config(bg=self.colors['bg_panel'])
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            subchild.config(bg=self.colors['bg_panel'])
        
        item.bind('<Enter>', on_enter)
        item.bind('<Leave>', on_leave)
        
        # Content
        item_content = tk.Frame(item, bg=self.colors['bg_panel'])
        item_content.pack(fill='both', padx=16, pady=16)
        
        # Name
        tk.Label(
            item_content,
            text=name.upper(),
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_dim']
        ).pack(anchor='w')
        
        # Value
        value_frame = tk.Frame(item_content, bg=self.colors['bg_panel'])
        value_frame.pack(anchor='w', pady=(8, 4))
        
        tk.Label(
            value_frame,
            text=value,
            font=("Segoe UI", 24),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_primary']
        ).pack(side='left')
        
        tk.Label(
            value_frame,
            text=unit,
            font=("Segoe UI", 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_dim']
        ).pack(side='left', padx=(4, 0))
        
        # Comparison
        comp_frame = tk.Frame(item_content, bg=self.colors['bg_panel'])
        comp_frame.pack(anchor='w')
        
        tk.Label(
            comp_frame,
            text=f"Pro: {pro_val}",
            font=("Segoe UI", 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary']
        ).pack(side='left')
        
        # Diff badge
        diff_color = {
            'good': self.colors['good'],
            'warning': self.colors['warning'],
            'bad': self.colors['bad']
        }.get(status, self.colors['text_dim'])
        
        diff_label = tk.Label(
            comp_frame,
            text=diff,
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=diff_color,
            padx=8,
            pady=2
        )
        diff_label.pack(side='left', padx=(8, 0))
    
    def create_recommendation_item(self, parent, title, text):
        """Create a recommendation item"""
        item = tk.Frame(
            parent,
            bg=self.colors['bg_panel'],
            relief='flat'
        )
        item.pack(fill='x', pady=6)
        
        content = tk.Frame(item, bg=self.colors['bg_panel'])
        content.pack(fill='both', padx=16, pady=16)
        
        tk.Label(
            content,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_dim']
        ).pack(anchor='w')
        
        tk.Label(
            content,
            text=text,
            font=("Segoe UI", 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_primary'],
            wraplength=250,
            justify='left'
        ).pack(anchor='w', pady=(8, 0))
    
    def create_controls_bar(self, parent):
        """Create playback controls bar"""
        controls_bar = tk.Frame(
            parent,
            bg=self.colors['bg_main'],
            height=72,
            relief='flat'
        )
        controls_bar.pack(side='bottom', fill='x')
        controls_bar.pack_propagate(False)
        
        # Top border
        tk.Frame(controls_bar, bg=self.colors['border'], height=1).pack(side='top', fill='x')
        
        # Content
        content = tk.Frame(controls_bar, bg=self.colors['bg_main'])
        content.pack(fill='both', expand=True, padx=32, pady=16)
        
        # Playback controls
        playback_frame = tk.Frame(content, bg=self.colors['bg_main'])
        playback_frame.pack(side='left')
        
        for symbol in ["◄◄", "►", "►►", "⟲"]:
            is_active = symbol == "►"
            btn = tk.Button(
                playback_frame,
                text=symbol,
                font=("Segoe UI", 11),
                bg=self.colors['accent_red'] if is_active else self.colors['bg_panel'],
                fg='#ffffff' if is_active else self.colors['text_secondary'],
                activebackground=self.colors['accent_red_hover'],
                activeforeground='#ffffff',
                width=3,
                height=1,
                relief='flat',
                bd=0,
                cursor='hand2',
                command=lambda s=symbol: self.playback_control(s)
            )
            btn.pack(side='left', padx=4)
        
        # Timeline
        timeline_frame = tk.Frame(content, bg=self.colors['bg_main'])
        timeline_frame.pack(side='left', fill='x', expand=True, padx=24)
        
        # Timeline track
        track = tk.Canvas(
            timeline_frame,
            bg=self.colors['bg_main'],
            height=20,
            highlightthickness=0
        )
        track.pack(fill='x')
        
        # Draw timeline
        track.update_idletasks()
        w = track.winfo_width()
        if w > 1:
            # Background track
            track.create_rectangle(
                0, 8, w, 12,
                fill=self.colors['border'],
                outline=''
            )
            
            # Progress
            progress = int(w * self.current_frame / self.total_frames)
            track.create_rectangle(
                0, 8, progress, 12,
                fill=self.colors['accent_red'],
                outline=''
            )
            
            # Handle
            track.create_oval(
                progress-6, 4, progress+6, 16,
                fill=self.colors['accent_red'],
                outline=''
            )
        
        # Frame info
        info = tk.Label(
            timeline_frame,
            text=f"Frame {self.current_frame} / {self.total_frames} • 0.5x speed",
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_dim']
        )
        info.pack(pady=(4, 0))
        
        # View controls
        view_frame = tk.Frame(content, bg=self.colors['bg_main'])
        view_frame.pack(side='right')
        
        for view in ["Side", "Front", "Top", "Overlay"]:
            is_active = view == "Side"
            btn = tk.Button(
                view_frame,
                text=view,
                font=("Segoe UI", 10),
                bg=self.colors['bg_panel'],
                fg=self.colors['accent_red'] if is_active else self.colors['text_secondary'],
                activebackground=self.colors['border'],
                activeforeground=self.colors['text_primary'],
                relief='flat',
                bd=0,
                padx=16,
                pady=6,
                cursor='hand2',
                command=lambda v=view: self.change_view(v)
            )
            btn.pack(side='left', padx=4)
    
    def action_button_clicked(self, action):
        """Handle action button clicks"""
        messagebox.showinfo("Action", f"{action} - Coming soon!")
    
    def playback_control(self, control):
        """Handle playback controls"""
        print(f"Playback: {control}")
    
    def change_view(self, view):
        """Change camera view"""
        print(f"View changed to: {view}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ProMirrorGolfUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
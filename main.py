"""
ProMirrorGolf - 3D Skeleton Comparison UI
Main application entry point with full backend integration
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import asyncio
import threading
import logging
from pathlib import Path
from datetime import datetime
import json
import webbrowser
import numpy as np
from typing import Dict

# Add root directory to path for importing src modules
sys.path.insert(0, str(Path(__file__).parent))

# Import backend modules
from src.swing_ai_core import SwingAIController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('promirror.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProMirrorGolfUI:
    """Main Application UI - 3D Skeleton Comparison with Live Backend Integration"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProMirrorGolf - AI Swing Analysis")
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
            'bad': '#f44336',
            'status_active': '#4caf50',
            'status_inactive': '#666666'
        }
        
        self.root.configure(bg=self.colors['bg_main'])
        
        # Load and set app icon
        self.app_icon = None
        self.load_app_icon()
        
        # State
        self.current_frame = 0
        self.total_frames = 0
        self.is_playing = False
        self.playback_speed = 1.0
        self.video_frames = []  # Store frames for playback
        self.current_pro = "Rory McIlroy"
        self.current_pro_id = None  # Store selected pro ID
        self.current_club = "Driver"
        self.current_view = "Side"  # Current view: Side, Front, Top, Overlay
        
        # Video processing state
        self.processing_progress = 0.0
        self.processing_active = False
        
        # Backend integration
        self.controller = None
        self.session_active = False
        self.current_user_id = "default_user"
        self.current_session_name = None
        self.current_session_id = None
        self.swing_count = 0
        self.current_swing_data = None
        self.current_swing_id = None
        self.metrics_data = {}  # Will store actual metrics from backend
        self.session_swings = []  # Store swing data for timeline
        
        # Available pros and clubs
        self.available_pros = []  # Will be populated from database
        self.available_clubs = ["Driver", "3-Wood", "5-Wood", "3-Iron", "4-Iron", "5-Iron", 
                               "6-Iron", "7-Iron", "8-Iron", "9-Iron", "PW", "SW", "LW", "Putter"]
        
        # Async event loop for backend
        self.loop = None
        self.loop_thread = None
        self.setup_async_loop()
        
        # Recommendations storage
        self.recommendations = []
        
        # UI widgets that need updates
        self.status_label = None
        self.swing_count_label = None
        self.pro_label = None
        
        self.create_ui()
        
        # Initialize backend on startup
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.initialize_backend(),
                self.loop
            )
    
    def load_app_icon(self):
        """Load the ProMirrorGolf app icon and set it as window icon"""
        try:
            icon_path = Path(__file__).parent / "assets" / "icons" / "ProMirrorGolf_App_Icon.png"
            
            if icon_path.exists():
                # Load icon using PhotoImage (keep reference to prevent garbage collection)
                self.app_icon = tk.PhotoImage(file=str(icon_path))
                
                # Set window icon (title bar icon)
                # Note: On Windows, we need to use iconbitmap for .ico, but PhotoImage works for .png
                # For cross-platform, we'll use iconphoto which works with PhotoImage
                try:
                    self.root.iconphoto(True, self.app_icon)
                except Exception as e:
                    logger.warning(f"Could not set window icon: {e}")
                    # Fallback: try iconbitmap if available
                    try:
                        # Try to use .ico if available
                        ico_path = icon_path.with_suffix('.ico')
                        if ico_path.exists():
                            self.root.iconbitmap(str(ico_path))
                    except:
                        pass
                
                logger.info(f"App icon loaded successfully from {icon_path}")
            else:
                logger.warning(f"Icon file not found at {icon_path}")
        except Exception as e:
            logger.error(f"Error loading app icon: {e}", exc_info=True)
    
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
        
        # Status bar at bottom
        self.create_status_bar(container)
        
        # Controls bar at bottom
        self.create_controls_bar(container)
    
    def create_top_bar(self, parent):
        """Create top navigation bar with status indicator"""
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
        
        # Status indicator
        status_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        status_frame.pack(side='left', padx=20)
        
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 12),
            bg=self.colors['bg_main'],
            fg=self.colors['status_inactive']
        )
        self.status_indicator.pack(side='left', padx=4)
        
        self.status_label = tk.Label(
            status_frame,
            text="Not Active",
            font=("Segoe UI", 10),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(side='left')
        
        # Swing count
        self.swing_count_label = tk.Label(
            status_frame,
            text="Swings: 0",
            font=("Segoe UI", 10),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.swing_count_label.pack(side='left', padx=(20, 0))
        
        # Pro selector
        pro_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        pro_frame.pack(side='left', expand=True)
        
        tk.Label(
            pro_frame,
            text="Pro:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        ).pack(side='left', padx=(0, 8))
        
        # Pro dropdown
        self.pro_var = tk.StringVar(value="Auto Match")
        self.pro_dropdown = tk.OptionMenu(
            pro_frame,
            self.pro_var,
            "Auto Match",
            command=self.change_pro
        )
        self.pro_dropdown.config(
            font=("Segoe UI", 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['border'],
            activeforeground=self.colors['text_primary'],
            relief='flat',
            bd=0,
            padx=12,
            pady=6,
            cursor='hand2'
        )
        self.pro_dropdown.pack(side='left', padx=4)
        
        # Pro info label
        self.pro_label = tk.Label(
            pro_frame,
            text="(Auto-matched)",
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_dim'],
            padx=8
        )
        self.pro_label.pack(side='left', padx=4)
        
        # Club selector
        club_frame = tk.Frame(pro_frame, bg=self.colors['bg_main'])
        club_frame.pack(side='left', padx=(20, 0))
        
        tk.Label(
            club_frame,
            text="Club:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        ).pack(side='left', padx=(0, 8))
        
        # Club dropdown
        self.club_var = tk.StringVar(value=self.current_club)
        self.club_dropdown = tk.OptionMenu(
            club_frame,
            self.club_var,
            *self.available_clubs,
            command=self.change_club
        )
        self.club_dropdown.config(
            font=("Segoe UI", 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['border'],
            activeforeground=self.colors['text_primary'],
            relief='flat',
            bd=0,
            padx=12,
            pady=6,
            cursor='hand2'
        )
        self.club_dropdown.pack(side='left', padx=4)
        
        # MLM2Pro status indicator
        mlm2pro_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        mlm2pro_frame.pack(side='right', padx=20)
        
        self.mlm2pro_status_indicator = tk.Label(
            mlm2pro_frame,
            text="●",
            font=("Segoe UI", 10),
            bg=self.colors['bg_main'],
            fg=self.colors['status_inactive']
        )
        self.mlm2pro_status_indicator.pack(side='left', padx=4)
        
        self.mlm2pro_status_label = tk.Label(
            mlm2pro_frame,
            text="MLM2Pro: --",
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_dim']
        )
        self.mlm2pro_status_label.pack(side='left')
        
        # Action buttons
        action_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
        action_frame.pack(side='right', padx=32)
        
        for text, primary in [("Upload Video", False), ("Export Video", False), ("Save HTML", False), ("New Analysis", True)]:
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
        self.viewer_panels = []
        self.viewer_labels = []  # Store labels for dynamic updates
        
        for idx, (title, color) in enumerate([("Your Swing", self.colors['accent_red']), 
                                               (self.current_pro, self.colors['text_secondary'])]):
            panel = tk.Frame(
                viewer_container,
                bg=self.colors['bg_dark'],
                relief='flat'
            )
            panel.pack(side='left', fill='both', expand=True, padx=(0, 1 if idx == 0 else 0))
            
            # Panel label (stored for dynamic updates)
            label = tk.Label(
                panel,
                text=title.upper(),
                font=("Segoe UI", 9, "bold"),
                bg=self.colors['bg_dark'],
                fg=color
            )
            label.place(x=20, y=20)
            self.viewer_labels.append(label)
            
            # Skeleton display area
            skeleton_display = tk.Canvas(
                panel,
                bg=self.colors['bg_dark'],
                highlightthickness=0
            )
            skeleton_display.pack(fill='both', expand=True, padx=40, pady=60)
            
            # Store canvas reference
            self.viewer_panels.append((panel, skeleton_display, color))
            
            # Draw skeleton
            self.draw_skeleton(skeleton_display, color)
    
    def draw_skeleton(self, canvas, color):
        """Draw a simple skeleton figure - adapts to current view"""
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w < 50 or h < 50:
            canvas.after(100, lambda: self.draw_skeleton(canvas, color))
            return
        
        # Clear canvas
        canvas.delete("all")
        
        cx = w // 2
        cy = h // 2
        scale = min(w, h) / 600
        
        # Adjust joint positions based on view
        if self.current_view == "Side":
            # Side view (DTL) - default
            joints = self._get_side_view_joints(cx, cy, scale)
        elif self.current_view == "Front":
            # Front view (Face-on)
            joints = self._get_front_view_joints(cx, cy, scale)
        elif self.current_view == "Top":
            # Top view (bird's eye)
            joints = self._get_top_view_joints(cx, cy, scale)
        else:  # Overlay
            # Overlay view - same as side but with additional indicators
            joints = self._get_side_view_joints(cx, cy, scale)
        
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
            # Glow effect
            canvas.create_oval(
                x-r-2, y-r-2, x+r+2, y+r+2,
                outline=color,
                width=1
            )
        
        # Add view-specific elements
        if self.current_view == "Overlay":
            # Add angle indicators for overlay view
            self._draw_overlay_indicators(canvas, cx, cy, scale, color)
        else:
            # Ground plane for side/front views
            ground_y = cy + 200*scale
            canvas.create_line(
                cx - 150*scale, ground_y,
                cx + 150*scale, ground_y,
                fill=self.colors['border'],
                width=2
            )
    
    def _get_side_view_joints(self, cx, cy, scale):
        """Get joint positions for side view (DTL)"""
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
        """Get joint positions for front view (Face-on)"""
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
        """Get joint positions for top view (Bird's eye)"""
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
    
    def _draw_overlay_differences(self, canvas, cx, cy, scale, color):
        """Draw overlay differences between user and pro swings"""
        if not self.current_swing_data:
            return
        
        # Get user and pro metrics
        user_metrics = self.current_swing_data.get('metrics', {})
        pro_match = self.current_swing_data.get('pro_match', {})
        
        if not user_metrics or not pro_match:
            return
        
        # Get pro metrics from database if available
        pro_id = pro_match.get('pro_id')
        pro_metrics = {}
        
        if pro_id and self.controller and self.controller.style_matcher:
            try:
                pro_swing = self.controller.style_matcher.pro_db.get_pro_swing(pro_id)
                if pro_swing:
                    pro_metrics = pro_swing.get('metrics', {})
            except:
                pass
        
        # Draw difference indicators
        differences = []
        key_metrics = ['hip_rotation_top', 'shoulder_rotation_top', 'x_factor', 'spine_angle_address']
        
        for metric in key_metrics:
            user_val = user_metrics.get(metric, 0)
            pro_val = pro_metrics.get(metric, 0)
            
            if pro_val != 0:
                diff = user_val - pro_val
                differences.append({
                    'metric': metric,
                    'diff': diff
                })
        
        # Draw visual indicators
        y_offset = -100 * scale
        for i, diff_info in enumerate(differences[:4]):  # Show top 4 differences
            diff = diff_info['diff']
            metric_name = diff_info['metric'].replace('_', ' ').title()
            
            # Color based on difference magnitude
            if abs(diff) < 5:
                diff_color = self.colors['good']
            elif abs(diff) < 15:
                diff_color = self.colors['warning']
            else:
                diff_color = self.colors['bad']
            
            # Draw indicator line
            line_length = min(100 * scale, abs(diff) * 2 * scale)
            direction = 1 if diff > 0 else -1
            
            x_start = cx
            x_end = cx + (line_length * direction)
            
            canvas.create_line(
                x_start, cy + y_offset,
                x_end, cy + y_offset,
                fill=diff_color,
                width=3,
                arrow='last' if abs(diff) > 5 else None
            )
            
            # Draw label
            canvas.create_text(
                cx + (line_length * direction) + (20 * direction),
                cy + y_offset,
                text=f"{metric_name}: {diff:+.1f}°",
                fill=diff_color,
                font=("Segoe UI", 8),
                anchor='w' if direction > 0 else 'e'
            )
            
            y_offset += 30 * scale
    
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
        
        # Metrics container (will be updated dynamically)
        self.metrics_container = tk.Frame(content, bg=self.colors['bg_main'])
        self.metrics_container.pack(fill='both', expand=True)
        
        # Initial metrics display
        self.update_metrics_display()
        
        # Recommendations container
        tk.Label(
            content,
            text="KEY RECOMMENDATIONS",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        ).pack(anchor='w', pady=(32, 24))
        
        self.recommendations_container = tk.Frame(content, bg=self.colors['bg_main'])
        self.recommendations_container.pack(fill='both', expand=True)
        
        # Initial recommendations
        self.update_recommendations_display()
    
    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        status_bar = tk.Frame(
            parent,
            bg=self.colors['bg_panel'],
            height=24,
            relief='flat'
        )
        status_bar.pack(side='bottom', fill='x')
        status_bar.pack_propagate(False)
        
        # Status message
        self.status_message = tk.Label(
            status_bar,
            text="Ready - Click 'New Analysis' to start a session",
            font=("Segoe UI", 9),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.status_message.pack(side='left', padx=16, pady=4)
    
    def update_metrics_display(self):
        """Update metrics display with current data from backend"""
        # Clear existing metrics
        for widget in self.metrics_container.winfo_children():
            widget.destroy()
        
        # If we have real metrics data, use it; otherwise show placeholder
        if self.metrics_data:
            metrics_list = []
            for name, data in self.metrics_data.items():
                value = data.get('value', 'N/A')
                unit = data.get('unit', '')
                pro_val = data.get('pro', 'N/A')
                diff = data.get('diff', 'N/A')
                status = data.get('status', 'warning')
                metrics_list.append((name, str(value), unit, str(pro_val), str(diff), status))
        else:
            # Default placeholder metrics
            metrics_list = [
                ("Hip Rotation", "N/A", "deg", "N/A", "No data", "warning"),
                ("Shoulder Turn", "N/A", "deg", "N/A", "No data", "warning"),
                ("X-Factor", "N/A", "deg", "N/A", "No data", "warning"),
                ("Spine Angle", "N/A", "deg", "N/A", "No data", "warning"),
                ("Tempo Ratio", "N/A", ":1", "N/A", "No data", "warning"),
                ("Weight Shift", "N/A", "%", "N/A", "No data", "warning"),
            ]
        
        for name, value, unit, pro_val, diff, status in metrics_list:
            self.create_metric_item(self.metrics_container, name, value, unit, pro_val, diff, status)
    
    def update_recommendations_display(self):
        """Update recommendations display"""
        # Clear existing recommendations
        for widget in self.recommendations_container.winfo_children():
            widget.destroy()
        
        # Display current recommendations
        if not self.recommendations:
            self.recommendations = [
                ("Info", "Start a session and hit some balls to get personalized recommendations."),
            ]
        
        for title, text in self.recommendations:
            self.create_recommendation_item(self.recommendations_container, title, text)
    
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
        self.timeline_canvas = tk.Canvas(
            timeline_frame,
            bg=self.colors['bg_main'],
            height=20,
            highlightthickness=0
        )
        self.timeline_canvas.pack(fill='x')
        
        # Draw timeline
        self.update_timeline()
        
        # Frame info
        self.frame_info = tk.Label(
            timeline_frame,
            text=f"Frame {self.current_frame} / {self.total_frames} • 0.5x speed",
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_dim']
        )
        self.frame_info.pack(pady=(4, 0))
        
        # View controls
        view_frame = tk.Frame(content, bg=self.colors['bg_main'])
        view_frame.pack(side='right')
        
        # Store view buttons for state management
        self.view_buttons = {}
        
        for view in ["Side", "Front", "Top", "Overlay"]:
            is_active = view == self.current_view
            btn = tk.Button(
                view_frame,
                text=view,
                font=("Segoe UI", 10),
                bg=self.colors['accent_red'] if is_active else self.colors['bg_panel'],
                fg='#ffffff' if is_active else self.colors['text_secondary'],
                activebackground=self.colors['accent_red_hover'] if is_active else self.colors['border'],
                activeforeground='#ffffff',
                relief='flat',
                bd=0,
                padx=16,
                pady=6,
                cursor='hand2',
                command=lambda v=view: self.change_view(v)
            )
            btn.pack(side='left', padx=4)
            self.view_buttons[view] = btn
    
    def update_timeline(self):
        """Update timeline display for video playback"""
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
    
    def update_timeline_with_swings(self):
        """Update timeline to show swing markers"""
        self.timeline_canvas.update_idletasks()
        w = self.timeline_canvas.winfo_width()
        if w > 1 and self.swing_count > 0:
            # Draw swing markers on timeline
            for i, swing in enumerate(self.session_swings):
                if i < 20:  # Limit to 20 swings for display
                    x_pos = int(w * (i + 1) / max(20, self.swing_count))
                    score = swing.get('overall_score', 0)
                    
                    # Color based on score
                    if score >= 80:
                        color = self.colors['good']
                    elif score >= 60:
                        color = self.colors['warning']
                    else:
                        color = self.colors['bad']
                    
                    # Draw marker
                    self.timeline_canvas.create_oval(
                        x_pos-4, 6, x_pos+4, 14,
                        fill=color,
                        outline='',
                        tags='swing_marker'
                    )
    
    def action_button_clicked(self, action):
        """Handle action button clicks with full backend integration"""
        if action == "New Analysis":
            self.start_session()
        elif action == "Upload Video":
            self.upload_video()
        elif action == "Export Video":
            self.export_video()
        elif action == "Save HTML":
            self.save_html_report()
        else:
            messagebox.showinfo("Action", f"{action} - Coming soon!")
    
    def upload_video(self):
        """Upload and process dual videos (DTL + Face)"""
        if not self.controller:
            messagebox.showerror("Error", "Backend not initialized. Please wait for initialization to complete.")
            return
        
        # Ask for DTL video
        dtl_path = filedialog.askopenfilename(
            title="Select Down-the-Line (DTL) Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("MP4 files", "*.mp4"),
                ("All files", "*.*")
            ]
        )
        
        if not dtl_path:
            return
        
        # Ask for Face-on video
        face_path = filedialog.askopenfilename(
            title="Select Face-on Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("MP4 files", "*.mp4"),
                ("All files", "*.*")
            ]
        )
        
        if not face_path:
            return
        
        # Validate videos
        from src.video_processor import VideoProcessor
        processor = VideoProcessor()
        dtl_validation = processor.validate_video_format(dtl_path)
        face_validation = processor.validate_video_format(face_path)
        
        if not dtl_validation['valid']:
            messagebox.showerror("Invalid Video", f"DTL video validation failed:\n{', '.join(dtl_validation['errors'])}")
            return
        
        if not face_validation['valid']:
            messagebox.showerror("Invalid Video", f"Face video validation failed:\n{', '.join(face_validation['errors'])}")
            return
        
        # Start session in upload mode if not already active
        if not self.session_active:
            self.update_status("Starting session for video upload...")
            if self.loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.controller.start_session(self.current_user_id, "Video Upload Session", use_video_upload=True),
                    self.loop
                )
                try:
                    future.result(timeout=5)
                    self.session_active = True
                    self.update_status("Session started - processing videos...")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start session: {e}")
                    return
        
        # Process videos with increased timeout for long videos
        self.update_status("Processing uploaded videos... (this may take several minutes)")
        self.processing_active = True
        self.update_progress_bar(0.0, "Loading videos...")
        
        if self.loop:
            # Use 600 second timeout (10 minutes) for processing long videos
            # Processing happens in background thread, UI remains responsive
            future = asyncio.run_coroutine_threadsafe(
                self.controller.process_uploaded_videos(dtl_path, face_path, downsample_factor=1),
                self.loop
            )
            try:
                result = future.result(timeout=600)  # 600 second timeout for processing (10 minutes)
                if result.get('success'):
                    swing_data = result.get('swing_data', {})
                    self.current_swing_id = result.get('swing_id')
                    self.current_swing_data = swing_data
                    self.swing_count += 1
                    
                    frames_processed = result.get('frames_processed', 0)
                    swings_detected = result.get('swings_detected', 0)
                    
                    # Update UI with results (thread-safe)
                    def update_ui():
                        self.update_ui_with_swing_data(swing_data)
                        self.update_status(f"Video processed! {frames_processed} frames, {swings_detected} swings detected")
                    
                    self.root.after(0, update_ui)
                    
                    messagebox.showinfo(
                        "Success", 
                        f"Video processed successfully!\n\n"
                        f"Frames processed: {frames_processed}\n"
                        f"Swings detected: {swings_detected}\n"
                        f"Swing analyzed and saved."
                    )
                else:
                    error_msg = result.get('error', 'Unknown error')
                    errors = result.get('errors', [])
                    if errors:
                        error_msg = f"{error_msg}\n\nDetails:\n" + "\n".join(errors)
                    error_msg_final = error_msg  # Capture for lambda
                    self.root.after(0, lambda: messagebox.showerror("Processing Error", f"Failed to process videos:\n{error_msg_final}"))
            except asyncio.TimeoutError:
                logger.error("Video processing timed out after 600 seconds")
                self.root.after(0, lambda: messagebox.showerror(
                    "Timeout Error",
                    "Video processing timed out after 10 minutes.\n\n"
                    "This may occur with very long videos. Try:\n"
                    "- Using shorter video clips\n"
                    "- Ensuring videos are properly formatted\n"
                    "- Checking system resources"
                ))
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing videos: {error_msg}", exc_info=True)
                self.root.after(0, lambda err=error_msg: messagebox.showerror("Error", f"Failed to process videos:\n{err}"))
    
    def export_video(self):
        """Export current swing video"""
        if not self.current_swing_data or not self.current_swing_id:
            messagebox.showwarning(
                "No Data", 
                "No swing data available to export.\n\nStart a session and capture some swings first."
            )
            return
        
        if not self.controller or not self.controller.db:
            messagebox.showerror("Error", "Backend not initialized. Please restart the application.")
            return
        
        try:
            # Get swing from database
            swing = self.controller.db.get_swing(self.current_swing_id)
            if not swing:
                messagebox.showerror("Error", "Swing data not found in database.")
                return
            
            # Get video paths
            video_dtl = swing.get('video_dtl_path', '')
            video_face = swing.get('video_face_path', '')
            
            if not video_dtl and not video_face:
                messagebox.showinfo(
                    "No Videos", 
                    "This swing does not have associated video files.\n\n"
                    "Videos are captured during active sessions."
                )
                return
            
            # Ask user where to save
            output_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
                title="Export Swing Video"
            )
            
            if output_path:
                # For now, copy the DTL video if available
                # In a full implementation, this would merge both views
                if video_dtl and Path(video_dtl).exists():
                    import shutil
                    shutil.copy2(video_dtl, output_path)
                    messagebox.showinfo("Success", f"Video exported to:\n{output_path}")
                    self.update_status(f"Video exported: {Path(output_path).name}")
                else:
                    messagebox.showerror("Error", "Video file not found on disk.")
        
        except Exception as e:
            logger.error(f"Error exporting video: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export video:\n{str(e)}")
    
    def save_html_report(self):
        """Save current swing data as HTML report using backend report generator"""
        if not self.current_swing_data or not self.current_swing_id:
            messagebox.showwarning(
                "No Data", 
                "No swing data available to save.\n\nStart a session and capture some swings first."
            )
            return
        
        if not self.controller or not self.controller.report_generator:
            messagebox.showerror("Error", "Backend not initialized. Please restart the application.")
            return
        
        try:
            # Get swing from database
            swing = self.controller.db.get_swing(self.current_swing_id)
            if not swing:
                messagebox.showerror("Error", "Swing data not found in database.")
                return
            
            # Get pro match data
            pro_match_id = swing.get('pro_match_id', '')
            pro_match = {}
            if pro_match_id and self.controller.style_matcher:
                from src.database import ProSwingDatabase
                pro_db_path = self.controller.config.get("database", {}).get("pro_db_path", "./data/pro_swings.db")
                pro_db = ProSwingDatabase(pro_db_path)
                pro_swing = pro_db.get_pro_swing(pro_match_id)
                if pro_swing:
                    pro_match = {
                        'golfer_name': pro_swing.get('golfer_name', 'Unknown'),
                        'metrics': pro_swing.get('metrics', {})
                    }
            
            # Ask user where to save
            output_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                title="Save HTML Report"
            )
            
            if output_path:
                # Use backend report generator if available, otherwise use simple HTML
                try:
                    # Try to use backend report generator (async)
                    future = asyncio.run_coroutine_threadsafe(
                        self.controller.report_generator.create_report(
                            swing_id=self.current_swing_id,
                            user_videos={'dtl': swing.get('video_dtl_path', ''), 'face': swing.get('video_face_path', '')},
                            pro_match=pro_match,
                            swing_metrics=swing.get('metrics', {}),
                            flaw_analysis=swing.get('flaw_analysis', {}),
                            shot_data=swing.get('shot_data', {}),
                            pose_data={}
                        ),
                        self.loop
                    )
                    report_data = future.result(timeout=30)
                    report_path = report_data.get('html_path', '')
                    
                    if report_path and Path(report_path).exists():
                        # Copy to user's chosen location
                        import shutil
                        shutil.copy2(report_path, output_path)
                        self.update_status(f"HTML report saved: {Path(output_path).name}")
                    else:
                        # Fall back to simple HTML
                        html_content = self.generate_html_report(swing, pro_match)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        self.update_status(f"HTML report saved: {Path(output_path).name}")
                except Exception as e:
                    logger.warning(f"Backend report generator failed, using simple HTML: {e}")
                    # Fall back to simple HTML
                    html_content = self.generate_html_report(swing, pro_match)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.update_status(f"HTML report saved: {Path(output_path).name}")
                
                if messagebox.askyesno("Open Report", "Open the report in your browser?"):
                    webbrowser.open(f"file://{Path(output_path).absolute()}")
        
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}", exc_info=True)
            messagebox.showerror("Save Error", f"Failed to save HTML report:\n{str(e)}")
    
    def generate_html_report(self, swing, pro_match=None):
        """Generate HTML report from swing data"""
        metrics = swing.get('metrics', {})
        shot_data = swing.get('shot_data', {})
        flaw_analysis = swing.get('flaw_analysis', {})
        overall_score = swing.get('overall_score', 0)
        pro_name = pro_match.get('golfer_name', 'Unknown') if pro_match else 'Unknown'
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ProMirrorGolf - Swing Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #0a0a0a; color: #e0e0e0; }}
        .header {{ background: #141414; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ background: #141414; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #0f0f0f; border-radius: 4px; }}
        .score {{ font-size: 48px; color: #ff4444; font-weight: bold; }}
        h1, h2 {{ color: #ff4444; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td, th {{ padding: 10px; text-align: left; border-bottom: 1px solid #2a2a2a; }}
        th {{ background: #0f0f0f; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ProMirrorGolf Swing Analysis Report</h1>
        <p>Session: {swing.get('session_id', 'N/A')} | Swing ID: {swing.get('swing_id', 'N/A')}</p>
        <p>Timestamp: {swing.get('timestamp', 'N/A')}</p>
        <p>Matched Pro: {pro_name}</p>
    </div>
    
    <div class="section">
        <h2>Overall Score</h2>
        <div class="score">{overall_score:.1f}/100</div>
        <p>Flaws Detected: {flaw_analysis.get('flaw_count', 0)}</p>
    </div>
    
    <div class="section">
        <h2>Shot Data</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
"""
        
        for key, value in shot_data.items():
            html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Swing Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
"""
        
        for key, value in metrics.items():
            html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
        
        html += """        </table>
    </div>
"""
        
        if flaw_analysis:
            html += """    <div class="section">
        <h2>Flaw Analysis</h2>
        <pre>"""
            html += json.dumps(flaw_analysis, indent=2)
            html += """        </pre>
    </div>
"""
        
        html += """</body>
</html>"""
        
        return html
    
    def playback_control(self, control):
        """Handle playback controls"""
        # Use ASCII-safe representation for logging to avoid Unicode encoding errors on Windows
        try:
            control_safe = control.encode('ascii', 'replace').decode('ascii')
        except:
            control_safe = repr(control)  # Fallback to repr if encoding fails
        logger.info(f"Playback control: {control_safe}")
        
        if not self.current_swing_data and not self.video_frames:
            self.update_status("No swing data available for playback")
            return
        
        if control == "◄◄":
            # Rewind to start
            self.current_frame = 0
            self.is_playing = False
            self.update_timeline()
            self.update_skeleton_display()
            self.update_status("Rewound to start")
        elif control == "►":
            # Play/Pause toggle
            if self.total_frames > 0:
                self.is_playing = not self.is_playing
                if self.is_playing:
                    self.start_playback()
                    self.update_status("Playing...")
                else:
                    self.update_status("Paused")
            else:
                self.update_status("No video frames available")
        elif control == "►►":
            # Fast forward to end
            self.current_frame = max(0, self.total_frames - 1)
            self.is_playing = False
            self.update_timeline()
            self.update_skeleton_display()
            self.update_status("Fast forwarded to end")
        elif control == "⟲":
            # Reset to current swing start
            self.current_frame = 0
            self.is_playing = False
            self.update_timeline()
            self.update_skeleton_display()
            self.update_status("Reset to swing start")
    
    def frame_step(self, direction):
        """Step forward or backward one frame"""
        if self.total_frames == 0:
            return
        
        self.is_playing = False
        self.current_frame = max(0, min(self.total_frames - 1, self.current_frame + direction))
        self.update_timeline()
        self.update_skeleton_display()
        self.update_status(f"Frame {self.current_frame + 1} / {self.total_frames}")
    
    def start_playback(self):
        """Start video playback animation"""
        if not self.is_playing or self.total_frames == 0:
            return
        
        if self.current_frame >= self.total_frames - 1:
            self.current_frame = 0
            self.is_playing = False
            return
        
        self.current_frame += 1
        self.update_timeline()
        self.update_skeleton_display()
        
        # Schedule next frame (adjust delay for playback speed)
        delay_ms = int(1000 / (30 * self.playback_speed))  # 30 fps base
        self.root.after(delay_ms, self.start_playback)
    
    def update_progress_bar(self, progress: float, message: str = ""):
        """Update progress bar for video processing"""
        if not hasattr(self, 'progress_bar'):
            return
        
        self.processing_progress = max(0.0, min(1.0, progress))
        
        def update():
            self.progress_bar.delete("all")
            w = self.progress_bar.winfo_width()
            if w > 1:
                # Draw background
                self.progress_bar.create_rectangle(
                    0, 0, w, 8,
                    fill=self.colors['bg_dark'],
                    outline=''
                )
                # Draw progress
                progress_width = int(w * self.processing_progress)
                if progress_width > 0:
                    self.progress_bar.create_rectangle(
                        0, 0, progress_width, 8,
                        fill=self.colors['accent_red'],
                        outline=''
                    )
                # Update label
                if message:
                    self.progress_label.config(text=message)
                elif self.processing_progress > 0:
                    self.progress_label.config(text=f"{int(self.processing_progress * 100)}%")
                else:
                    self.progress_label.config(text="")
        
        self.root.after(0, update)
    
    def change_view(self, view):
        """Change camera view - updates skeleton display"""
        logger.info(f"View changed to: {view}")
        self.current_view = view
        
        # Update button states
        for v, btn in self.view_buttons.items():
            if v == view:
                btn.config(
                    bg=self.colors['accent_red'],
                    fg='#ffffff'
                )
            else:
                btn.config(
                    bg=self.colors['bg_panel'],
                    fg=self.colors['text_secondary']
                )
        
        # Update skeleton display based on view
        self.update_skeleton_display()
        self.update_status(f"View: {view}")
    
    def update_skeleton_display(self):
        """Update skeleton display based on current view"""
        # Redraw skeletons in viewer panels
        for panel, canvas, color in self.viewer_panels:
            self.draw_skeleton(canvas, color)
    
    def change_club(self, club):
        """Change club selection - updates pro matching"""
        logger.info(f"Club changed to: {club}")
        self.current_club = club
        
        if self.controller:
            self.controller.current_club = club
        
        # If we have current swing data, re-match with new club
        if self.current_swing_data and self.controller and self.controller.style_matcher:
            metrics = self.current_swing_data.get('metrics', {})
            if metrics:
                # Re-match with new club type
                future = asyncio.run_coroutine_threadsafe(
                    self.controller.style_matcher.find_best_match(metrics, club_type=club),
                    self.loop
                )
                try:
                    pro_match = future.result(timeout=5)
                    self.current_pro = pro_match.get('golfer_name', 'Unknown')
                    self.current_pro_id = pro_match.get('pro_id')
                    
                    # Update pro dropdown if needed
                    if self.pro_var.get() == "Auto Match":
                        self.update_pro_label(pro_match)
                    
                    self.update_status(f"Club: {club} - Re-matched to {self.current_pro}")
                except Exception as e:
                    logger.error(f"Error re-matching with new club: {e}")
                    self.update_status(f"Club: {club} - Pro match will update on next swing")
        else:
            self.update_status(f"Club: {club} - Pro match will update on next swing")
    
    def change_pro(self, pro_selection):
        """Change pro selection - allows manual pro selection"""
        logger.info(f"Pro selection changed to: {pro_selection}")
        
        if pro_selection == "Auto Match":
            # Reset to auto-matching
            self.current_pro_id = None
            self.pro_label.config(text="(Auto-matched)")
            
            # If we have current swing, re-match
            if self.current_swing_data:
                metrics = self.current_swing_data.get('metrics', {})
                if metrics and self.controller and self.controller.style_matcher:
                    future = asyncio.run_coroutine_threadsafe(
                        self.controller.style_matcher.find_best_match(metrics, club_type=self.current_club),
                        self.loop
                    )
                    try:
                        pro_match = future.result(timeout=5)
                        self.current_pro = pro_match.get('golfer_name', 'Unknown')
                        self.current_pro_id = pro_match.get('pro_id')
                        self.update_pro_label(pro_match)
                    except Exception as e:
                        logger.error(f"Error auto-matching: {e}")
            
            self.update_status("Pro: Auto Match (will match on next swing)")
        else:
            # Manual pro selection
            # Parse pro_id from selection (format: "Name - Club")
            pro_id = None
            for pro in self.available_pros:
                display_name = f"{pro['golfer_name']} - {pro['club_type']}"
                if display_name == pro_selection:
                    pro_id = pro['pro_id']
                    self.current_pro = pro['golfer_name']
                    self.current_pro_id = pro_id
                    break
            
            if pro_id:
                # Load pro data
                if self.controller and self.controller.style_matcher:
                    pro_swing = self.controller.style_matcher.pro_db.get_pro_swing(pro_id)
                    if pro_swing:
                        self.update_pro_label({
                            'golfer_name': pro_swing['golfer_name'],
                            'similarity_score': 0,  # Manual selection, no similarity
                            'pro_id': pro_id
                        })
                        self.update_status(f"Pro: {self.current_pro} (manual selection)")
                    else:
                        self.update_status(f"Pro data not found: {pro_id}")
            else:
                self.update_status(f"Pro selection not recognized: {pro_selection}")
    
    def update_pro_label(self, pro_match: Dict):
        """Update pro label with match information"""
        if pro_match:
            golfer_name = pro_match.get('golfer_name', 'Unknown')
            similarity = pro_match.get('similarity_score', 0)
            
            if similarity > 0:
                self.pro_label.config(
                    text=f"({similarity:.1f}% match)",
                    fg=self.colors['text_secondary']
                )
            else:
                self.pro_label.config(
                    text="(manual selection)",
                    fg=self.colors['text_dim']
                )
    
    def load_available_pros(self):
        """Load available pros from database for dropdown"""
        if not self.controller or not self.controller.style_matcher:
            return
        
        try:
            # Get all pros for current club
            pro_swings = self.controller.style_matcher.pro_db.get_all_pro_swings(club_type=self.current_club)
            
            # Also get pros for other clubs
            all_pros = self.controller.style_matcher.pro_db.get_all_pro_swings()
            
            self.available_pros = all_pros
            
            # Update dropdown menu
            menu = self.pro_dropdown['menu']
            menu.delete(0, 'end')
            
            # Add "Auto Match" option
            menu.add_command(
                label="Auto Match",
                command=lambda: self.pro_var.set("Auto Match") or self.change_pro("Auto Match")
            )
            menu.add_separator()
            
            # Group by golfer name
            golfers = {}
            for pro in all_pros:
                name = pro['golfer_name']
                if name not in golfers:
                    golfers[name] = []
                golfers[name].append(pro)
            
            # Add pros grouped by name
            for golfer_name, pros in sorted(golfers.items()):
                for pro in pros:
                    display_name = f"{golfer_name} - {pro['club_type']}"
                    menu.add_command(
                        label=display_name,
                        command=lambda n=display_name: self.pro_var.set(n) or self.change_pro(n)
                    )
            
            logger.info(f"Loaded {len(all_pros)} pros for selection")
            
        except Exception as e:
            logger.error(f"Error loading available pros: {e}", exc_info=True)
    
    def update_mlm2pro_status(self):
        """Update MLM2Pro connection status display"""
        if not self.controller:
            return
        
        try:
            status = self.controller.get_mlm2pro_status()
            connected = status.get('connected', False)
            
            if connected:
                self.mlm2pro_status_indicator.config(fg=self.colors['status_active'])
                pending = status.get('pending_shots', 0)
                self.mlm2pro_status_label.config(
                    text=f"MLM2Pro: Connected ({pending} pending)",
                    fg=self.colors['text_secondary']
                )
            else:
                self.mlm2pro_status_indicator.config(fg=self.colors['status_inactive'])
                status_text = status.get('status', 'disconnected')
                self.mlm2pro_status_label.config(
                    text=f"MLM2Pro: {status_text.title()}",
                    fg=self.colors['text_dim']
                )
        except Exception as e:
            logger.debug(f"Error updating MLM2Pro status: {e}")
    
    def _periodic_mlm2pro_update(self):
        """Periodically update MLM2Pro status"""
        if self.controller:
            self.update_mlm2pro_status()
            self.root.after(5000, self._periodic_mlm2pro_update)  # Update every 5 seconds
    
    def on_video_progress_update(self, progress: float, message: str):
        """Callback for video processing progress updates"""
        self.root.after(0, lambda: self.update_progress_bar(progress, message))
    
    def update_status(self, message):
        """Update status bar message"""
        if self.status_message:
            self.status_message.config(text=message)
    
    def setup_async_loop(self):
        """Setup async event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for loop to be ready
        while self.loop is None:
            import time
            time.sleep(0.01)
    
    async def initialize_backend(self):
        """Initialize the backend controller"""
        try:
            if not self.controller:
                logger.info("Initializing SwingAIController...")
                self.controller = SwingAIController('config.json')
                await self.controller.initialize()
                
                # Set callback for swing detection
                self.controller.on_swing_detected = self.on_swing_detected
                # Add progress callback for video processing
                self.controller.on_progress_update = self.on_video_progress_update
                
                logger.info("Backend initialized successfully")
                self.root.after(0, lambda: self.update_status("Backend initialized - Ready to start session"))
                
                # Load available pros for dropdown
                self.root.after(0, self.load_available_pros)
                # Update MLM2Pro status
                self.root.after(1000, self.update_mlm2pro_status)
                self.root.after(0, lambda: self.root.after(5000, self._periodic_mlm2pro_update))
        except Exception as e:
            logger.error(f"Error initializing backend: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror(
                "Initialization Error",
                f"Failed to initialize backend:\n{str(e)}\n\nCheck the logs for details."
            ))
            self.root.after(0, lambda: self.update_status("Backend initialization failed - Check logs"))
    
    def start_session(self):
        """Start a practice session with full backend integration"""
        if self.session_active:
            messagebox.showwarning("Session Active", "A session is already active. Stop it first to start a new one.")
            return
        
        # Initialize backend if needed
        if not self.controller:
            self.update_status("Initializing backend...")
            future = asyncio.run_coroutine_threadsafe(
                self.initialize_backend(),
                self.loop
            )
            # Wait for initialization (with timeout)
            try:
                future.result(timeout=10)
            except asyncio.TimeoutError:
                messagebox.showerror("Timeout", "Backend initialization timed out. Please check the logs and try again.")
                self.update_status("Backend initialization failed")
                return
            except Exception as e:
                logger.error(f"Error initializing backend: {e}", exc_info=True)
                messagebox.showerror("Initialization Error", f"Failed to initialize backend:\n{str(e)}")
                self.update_status("Backend initialization failed")
                return
        
        if not self.controller:
            messagebox.showerror("Error", "Backend not initialized. Please check the logs and try again.")
            self.update_status("Backend initialization failed")
            return
        
        try:
            # Reset session state
            self.swing_count = 0
            self.session_swings = []
            self.current_swing_data = None
            self.current_swing_id = None
            self.metrics_data = {}
            self.recommendations = []
            
            self.session_active = True
            self.current_session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Update club type in controller
            if hasattr(self.controller, 'current_club'):
                self.controller.current_club = self.current_club
            
            # Start session in async loop
            future = asyncio.run_coroutine_threadsafe(
                self.controller.start_session(self.current_user_id, self.current_session_name),
                self.loop
            )
            
            # Wait for session to start (with timeout)
            try:
                future.result(timeout=10)
                self.current_session_id = self.controller.current_session_id
                
                # Update UI
                self.update_session_status(True)
                self.update_status(f"Session active: {self.current_session_name} - Ready to capture swings")
                
                # Reset metrics and recommendations displays
                self.update_metrics_display()
                self.update_recommendations_display()
                self.update_timeline_with_swings()
                
                logger.info(f"Session started: {self.current_session_name}")
                messagebox.showinfo(
                    "Session Started", 
                    f"Practice session started!\n\n"
                    f"User: {self.current_user_id}\n"
                    f"Session: {self.current_session_name}\n"
                    f"Club: {self.current_club}\n\n"
                    f"Start hitting balls to capture swings!\n"
                    f"The system will automatically detect and analyze each swing."
                )
            except asyncio.TimeoutError:
                messagebox.showerror("Timeout", "Session start timed out. Please check camera connections and try again.")
                self.session_active = False
                self.update_session_status(False)
            except Exception as e:
                logger.error(f"Error starting session: {e}", exc_info=True)
                messagebox.showerror("Session Error", f"Failed to start session:\n{str(e)}\n\nCheck camera connections and config.json")
                self.session_active = False
                self.update_session_status(False)
        
        except Exception as e:
            logger.error(f"Error in start_session: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start session:\n{str(e)}")
            self.session_active = False
            self.update_session_status(False)
            self.update_status("Session start failed")
    
    def stop_session(self):
        """Stop current session safely with timeout handling"""
        if not self.session_active:
            return
        
        logger.info("Stopping session...")
        self.session_active = False  # Set flag first to cancel any ongoing processing
        
        if self.controller:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.controller.stop_session(),
                    self.loop
                )
                # Wait with timeout, but don't crash if it times out
                try:
                    future.result(timeout=10)  # Increased timeout for video processing cleanup
                    logger.info("Session stopped successfully")
                except asyncio.TimeoutError:
                    logger.warning("Session stop timed out, but session flag is set - continuing...")
                    # Session flag is already False, so processing will stop
                
                # Update UI (thread-safe)
                def update_ui():
                    self.update_session_status(False)
                    self.update_status(f"Session stopped - {self.swing_count} swings analyzed")
                
                self.root.after(0, update_ui)
                
                # Show message (thread-safe)
                self.root.after(0, lambda: messagebox.showinfo(
                    "Session Stopped", 
                    f"Session ended.\n\nTotal swings analyzed: {self.swing_count}"
                ))
            except Exception as e:
                logger.error(f"Error stopping session: {e}", exc_info=True)
                # Still update UI even if there was an error
                self.root.after(0, lambda: self.update_session_status(False))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error stopping session:\n{str(e)}"))
    
    def update_session_status(self, active):
        """Update UI to reflect session status"""
        if active:
            if self.status_indicator:
                self.status_indicator.config(fg=self.colors['status_active'])
            if self.status_label:
                self.status_label.config(text="Active", fg=self.colors['status_active'])
        else:
            if self.status_indicator:
                self.status_indicator.config(fg=self.colors['status_inactive'])
            if self.status_label:
                self.status_label.config(text="Not Active", fg=self.colors['text_secondary'])
    
    def on_swing_detected(self, swing_data):
        """Callback when a swing is detected and analyzed"""
        self.swing_count += 1
        self.current_swing_data = swing_data
        
        # Extract swing_id from swing_data if available
        if 'swing_id' in swing_data:
            self.current_swing_id = swing_data['swing_id']
        
        # Store swing data for timeline
        self.session_swings.append({
            'swing_id': swing_data.get('swing_id', ''),
            'overall_score': swing_data.get('overall_score', 0),
            'timestamp': datetime.now().isoformat()
        })
        
        # Update UI on main thread
        self.root.after(0, lambda: self.update_ui_with_swing_data(swing_data))
        
        logger.info(f"Swing #{self.swing_count} detected and analyzed")
    
    def update_ui_with_swing_data(self, swing_data):
        """Update UI with swing analysis data from backend"""
        try:
            # Extract data from swing_data
            shot_data = swing_data.get("shot_data", {})
            overall_score = swing_data.get("overall_score", 0)
            metrics = swing_data.get("metrics", {})
            flaw_analysis = swing_data.get("flaw_analysis", {})
            pro_match = swing_data.get("pro_match", {})
            
            # Update pro match display
            if pro_match and pro_match.get('golfer_name'):
                self.current_pro = pro_match['golfer_name']
                self.current_pro_id = pro_match.get('pro_id')
                similarity_score = pro_match.get('similarity_score', 0)
                
                # Update pro label
                self.update_pro_label(pro_match)
                
                # Update viewer label if auto-match
                if self.pro_var.get() == "Auto Match" and len(self.viewer_labels) > 1:
                    self.viewer_labels[1].config(text=self.current_pro.upper())
                
                # Update pro dropdown if auto-match
                if self.pro_var.get() == "Auto Match":
                    # Keep auto-match selected, just update label
                    pass
            
            # Get pro metrics for comparison
            pro_metrics = {}
            if pro_match and pro_match.get('metrics'):
                pro_metrics = pro_match['metrics']
            
            # Build flaw map for status determination
            flaw_map = {}
            flaws = flaw_analysis.get("flaws", [])
            for flaw in flaws:
                metric_key = flaw.get('metric', '')
                flaw_map[metric_key] = {
                    'severity': flaw.get('severity', 0),
                    'issue': flaw.get('issue', ''),
                    'ideal_min': flaw.get('ideal_min', 0),
                    'ideal_max': flaw.get('ideal_max', 0)
                }
            
            # Update metrics display with real data
            self.metrics_data = {}
            
            # Key metrics to display
            metric_keys = [
                ('hip_rotation_top', 'Hip Rotation'),
                ('shoulder_rotation_top', 'Shoulder Turn'),
                ('x_factor', 'X-Factor'),
                ('spine_angle_address', 'Spine Angle'),
                ('tempo_ratio', 'Tempo Ratio'),
                ('weight_transfer', 'Weight Shift')
            ]
            
            for key, display_name in metric_keys:
                value = metrics.get(key, None)
                if value is None:
                    continue
                
                # Get pro value for comparison
                pro_val = pro_metrics.get(key, None)
                pro_val_str = f"{pro_val:.1f}" if pro_val is not None and isinstance(pro_val, (int, float)) else "N/A"
                
                # Calculate difference
                diff_str = "N/A"
                if pro_val is not None and isinstance(value, (int, float)) and isinstance(pro_val, (int, float)):
                    diff = value - pro_val
                    diff_str = f"{diff:+.1f}"
                
                # Determine status from flaw analysis
                status = "good"
                if key in flaw_map:
                    flaw_info = flaw_map[key]
                    severity = flaw_info.get('severity', 0)
                    if severity >= 0.7:
                        status = "bad"
                    elif severity >= 0.4:
                        status = "warning"
                else:
                    # Check if value is in ideal range (if we have flaw info)
                    if key in flaw_map:
                        ideal_min = flaw_map[key].get('ideal_min', 0)
                        ideal_max = flaw_map[key].get('ideal_max', 0)
                        if ideal_min > 0 or ideal_max > 0:
                            if value < ideal_min or value > ideal_max:
                                status = "warning"
                
                self.metrics_data[display_name] = {
                    'value': f"{value:.1f}" if isinstance(value, (int, float)) else str(value),
                    'unit': self.get_unit_for_metric(key),
                    'pro': pro_val_str,
                    'diff': diff_str,
                    'status': status
                }
            
            # Add shot data metrics if available
            if shot_data:
                club_speed = shot_data.get('ClubSpeed', 0)
                ball_speed = shot_data.get('BallSpeed', 0)
                
                if club_speed:
                    self.metrics_data['Club Speed'] = {
                        'value': f"{club_speed:.1f}",
                        'unit': 'mph',
                        'pro': 'N/A',
                        'diff': 'N/A',
                        'status': 'good'
                    }
                
                if ball_speed:
                    self.metrics_data['Ball Speed'] = {
                        'value': f"{ball_speed:.1f}",
                        'unit': 'mph',
                        'pro': 'N/A',
                        'diff': 'N/A',
                        'status': 'good'
                    }
            
            # If no metrics at all, show placeholder
            if not self.metrics_data:
                self.metrics_data = {
                    "No Data": {
                        'value': 'N/A',
                        'unit': '',
                        'pro': 'N/A',
                        'diff': 'No swing data',
                        'status': 'warning'
                    }
                }
            
            # Update metrics display
            self.update_metrics_display()
            
            # Update recommendations based on analysis
            self.update_recommendations_from_data(swing_data)
            
            # Update swing count
            if self.swing_count_label:
                self.swing_count_label.config(text=f"Swings: {self.swing_count}")
            
            # Update timeline with new swing
            self.update_timeline_with_swings()
            
            # Update status
            self.update_status(f"Swing #{self.swing_count} analyzed - Score: {overall_score:.1f}/100 - Matched: {self.current_pro}")
            
            # Show notification (non-blocking)
            self.root.after(100, lambda: messagebox.showinfo(
                "Swing Analyzed",
                f"Swing #{self.swing_count} analyzed!\n\n"
                f"Overall Score: {overall_score:.1f}/100\n"
                f"Matched Pro: {self.current_pro}\n"
                f"Similarity: {pro_match.get('similarity_score', 0):.1f}%\n"
                f"Flaws Detected: {len(flaws)}\n"
                f"Club Speed: {shot_data.get('ClubSpeed', 0):.1f} mph"
            ))
        
        except Exception as e:
            logger.error(f"Error updating UI with swing data: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("Update Error", f"Error updating UI:\n{str(e)}"))
    
    def get_unit_for_metric(self, metric_key):
        """Get unit for a metric key"""
        units = {
            'hip_rotation_top': 'deg',
            'hip_rotation': 'deg',
            'shoulder_rotation_top': 'deg',
            'shoulder_turn': 'deg',
            'shoulder_rotation': 'deg',
            'x_factor': 'deg',
            'spine_angle_address': 'deg',
            'spine_angle': 'deg',
            'spine_angle_change': 'deg',
            'tempo_ratio': ':1',
            'weight_transfer': '%',
            'weight_shift': '%',
            'club_speed': 'mph',
            'ball_speed': 'mph',
            'backswing_time': 's',
            'downswing_time': 's'
        }
        return units.get(metric_key.lower(), '')
    
    def update_recommendations_from_data(self, swing_data):
        """Update recommendations based on swing analysis data"""
        self.recommendations = []
        
        flaw_analysis = swing_data.get("flaw_analysis", {})
        flaws = flaw_analysis.get("flaws", [])
        
        if flaws:
            # Sort by severity
            sorted_flaws = sorted(flaws, key=lambda x: x.get('severity', 0), reverse=True)
            
            for i, flaw in enumerate(sorted_flaws[:3], 1):
                metric_name = flaw.get('metric', 'Unknown').replace('_', ' ').title()
                recommendation = flaw.get('recommendation', 'No specific recommendation available.')
                self.recommendations.append(
                    (f"Priority {i}", f"{metric_name}: {recommendation}")
                )
        else:
            # Default recommendations if no flaws detected
            self.recommendations = [
                ("Great Job!", "No significant flaws detected. Keep practicing to maintain consistency."),
            ]
        
        self.update_recommendations_display()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ProMirrorGolfUI(root)
    
    # Handle window close
    def on_closing():
        if app.session_active:
            if messagebox.askyesno("Confirm Exit", "Session is active. Stop and exit?"):
                app.stop_session()
                root.after(1000, root.destroy)
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

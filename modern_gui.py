"""
ProMirrorGolf - Modern Windows GUI
Professional golf swing analysis interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import asyncio
import threading
from pathlib import Path
import json
from datetime import datetime
import cv2
from PIL import Image, ImageTk
import logging
import sys

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


class ModernButton(tk.Button):
    """Modern styled button"""
    def __init__(self, parent, text, command, color='#00ff41', **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='#ffffff',
            font=('Arial', 11, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=10,
            **kwargs
        )
        
        self.bind('<Enter>', lambda e: self.config(bg=self._lighten_color(color)))
        self.bind('<Leave>', lambda e: self.config(bg=color))
    
    def _lighten_color(self, color):
        """Lighten a hex color"""
        # Simple lightening - in production use a proper color library
        if color == '#00ff41':
            return '#33ff66'
        elif color == '#ff4444':
            return '#ff6666'
        else:
            return color


class ProMirrorGolfGUI:
    """Main GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("⛳ ProMirrorGolf - AI Swing Analysis")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#0a0a0a')
        
        # State
        self.controller = None
        self.session_active = False
        self.current_user = None
        self.swing_count = 0
        self.camera_previews_active = False
        self.dtl_cap = None
        self.face_cap = None
        
        # Theme
        self.colors = {
            'bg_dark': '#0a0a0a',
            'bg_medium': '#1a1a1a',
            'bg_light': '#2a2a2a',
            'accent': '#00ff41',
            'accent_dim': '#00aa2b',
            'text': '#ffffff',
            'text_dim': '#999999',
            'error': '#ff4444',
            'warning': '#ffaa00',
            'success': '#00ff41'
        }
        
        # Async setup
        self.loop = None
        self.setup_async()
        
        # Build UI
        self.create_ui()
        
        # Load config
        self.load_config()
        
        # Status
        self.update_status("Ready to start", self.colors['success'])
    
    def setup_async(self):
        """Setup async event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
    
    def create_ui(self):
        """Create the main UI"""
        
        # ==== TOP BAR ====
        self.create_top_bar()
        
        # ==== MAIN CONTENT ====
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Camera views
        left_panel = tk.Frame(main_container, bg=self.colors['bg_medium'], width=800)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_camera_panel(left_panel)
        
        # Right panel - Controls and stats
        right_panel = tk.Frame(main_container, bg=self.colors['bg_medium'], width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        self.create_control_panel(right_panel)
        
        # ==== BOTTOM BAR ====
        self.create_bottom_bar()
    
    def create_top_bar(self):
        """Create top navigation bar"""
        top_bar = tk.Frame(self.root, bg=self.colors['bg_light'], height=80)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Logo/Title
        title_frame = tk.Frame(top_bar, bg=self.colors['bg_light'])
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        tk.Label(
            title_frame,
            text="⛳ ProMirrorGolf",
            font=('Arial', 28, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['accent']
        ).pack()
        
        tk.Label(
            title_frame,
            text="AI-Powered Swing Analysis",
            font=('Arial', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dim']
        ).pack()
        
        # Session info
        session_frame = tk.Frame(top_bar, bg=self.colors['bg_light'])
        session_frame.pack(side=tk.RIGHT, padx=30)
        
        self.session_label = tk.Label(
            session_frame,
            text="No Active Session",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dim']
        )
        self.session_label.pack()
        
        self.swing_counter_label = tk.Label(
            session_frame,
            text="0 Swings",
            font=('Arial', 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dim']
        )
        self.swing_counter_label.pack()
    
    def create_camera_panel(self, parent):
        """Create camera preview panel"""
        # Header
        header = tk.Frame(parent, bg=self.colors['bg_medium'])
        header.pack(side=tk.TOP, fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            header,
            text="📹 Live Camera Feeds",
            font=('Arial', 16, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Toggle preview button
        self.preview_btn = ModernButton(
            header,
            text="Start Preview",
            command=self.toggle_camera_preview,
            color=self.colors['accent_dim']
        )
        self.preview_btn.pack(side=tk.RIGHT)
        
        # Camera views container
        cameras_container = tk.Frame(parent, bg=self.colors['bg_dark'])
        cameras_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Down-the-line camera
        dtl_frame = tk.Frame(cameras_container, bg=self.colors['bg_light'])
        dtl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(
            dtl_frame,
            text="Down-the-Line View",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(pady=10)
        
        self.dtl_canvas = tk.Canvas(
            dtl_frame,
            bg='#000000',
            highlightthickness=0
        )
        self.dtl_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Face-on camera
        face_frame = tk.Frame(cameras_container, bg=self.colors['bg_light'])
        face_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(
            face_frame,
            text="Face-On View",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(pady=10)
        
        self.face_canvas = tk.Canvas(
            face_frame,
            bg='#000000',
            highlightthickness=0
        )
        self.face_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_control_panel(self, parent):
        """Create control panel"""
        # Session controls
        session_frame = tk.LabelFrame(
            parent,
            text="Session Control",
            font=('Arial', 14, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=20,
            pady=15
        )
        session_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        
        # User ID
        tk.Label(
            session_frame,
            text="User ID:",
            font=('Arial', 11),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.user_id_entry = tk.Entry(
            session_frame,
            font=('Arial', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            width=20
        )
        self.user_id_entry.grid(row=0, column=1, pady=5, sticky=tk.EW)
        self.user_id_entry.insert(0, "default_user")
        
        # Session name
        tk.Label(
            session_frame,
            text="Session Name:",
            font=('Arial', 11),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.session_name_entry = tk.Entry(
            session_frame,
            font=('Arial', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            width=20
        )
        self.session_name_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)
        self.session_name_entry.insert(0, f"Practice {datetime.now().strftime('%m/%d')}")
        
        # Start/Stop button
        self.session_btn = ModernButton(
            session_frame,
            text="▶ Start Session",
            command=self.toggle_session,
            color=self.colors['accent']
        )
        self.session_btn.grid(row=2, column=0, columnspan=2, pady=15, sticky=tk.EW)
        
        # Stats panel
        stats_frame = tk.LabelFrame(
            parent,
            text="Current Session Stats",
            font=('Arial', 14, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=20,
            pady=15
        )
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        
        self.stats_labels = {}
        stats_items = [
            ("Swings:", "0"),
            ("Avg Score:", "N/A"),
            ("Last Club Speed:", "N/A"),
            ("Last Ball Speed:", "N/A"),
            ("Processing Time:", "N/A")
        ]
        
        for i, (label, default) in enumerate(stats_items):
            tk.Label(
                stats_frame,
                text=label,
                font=('Arial', 10, 'bold'),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_dim']
            ).grid(row=i, column=0, sticky=tk.W, pady=3)
            
            value_label = tk.Label(
                stats_frame,
                text=default,
                font=('Arial', 10),
                bg=self.colors['bg_medium'],
                fg=self.colors['accent']
            )
            value_label.grid(row=i, column=1, sticky=tk.E, pady=3)
            self.stats_labels[label] = value_label
        
        # Activity log
        log_frame = tk.LabelFrame(
            parent,
            text="Activity Log",
            font=('Arial', 14, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=15,
            pady=10
        )
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Courier', 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Quick actions
        actions_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        actions_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=15)
        
        ModernButton(
            actions_frame,
            text="📊 View History",
            command=self.view_history,
            color=self.colors['accent_dim']
        ).pack(side=tk.TOP, fill=tk.X, pady=5)
        
        ModernButton(
            actions_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            color=self.colors['accent_dim']
        ).pack(side=tk.TOP, fill=tk.X, pady=5)
    
    def create_bottom_bar(self):
        """Create bottom status bar"""
        bottom_bar = tk.Frame(self.root, bg=self.colors['bg_light'], height=40)
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)
        bottom_bar.pack_propagate(False)
        
        self.status_label = tk.Label(
            bottom_bar,
            text="Ready",
            font=('Arial', 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dim'],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        
        self.connection_label = tk.Label(
            bottom_bar,
            text="● MLM2PRO: Disconnected",
            font=('Arial', 10),
            bg=self.colors['bg_light'],
            fg=self.colors['error']
        )
        self.connection_label.pack(side=tk.RIGHT, padx=20)
    
    def toggle_camera_preview(self):
        """Toggle camera preview on/off"""
        if not self.camera_previews_active:
            self.start_camera_previews()
        else:
            self.stop_camera_previews()
    
    def start_camera_previews(self):
        """Start showing camera previews"""
        try:
            # Try to open cameras
            self.dtl_cap = cv2.VideoCapture(0)
            self.face_cap = cv2.VideoCapture(1)
            
            if not self.dtl_cap.isOpened() or not self.face_cap.isOpened():
                messagebox.showerror("Camera Error", "Could not open cameras.\nCheck connections and config.json")
                return
            
            self.camera_previews_active = True
            self.preview_btn.config(text="Stop Preview")
            self.update_camera_frames()
            self.log("Camera previews started")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start cameras: {str(e)}")
            logger.error(f"Camera start error: {e}")
    
    def stop_camera_previews(self):
        """Stop camera previews"""
        self.camera_previews_active = False
        self.preview_btn.config(text="Start Preview")
        
        if self.dtl_cap:
            self.dtl_cap.release()
        if self.face_cap:
            self.face_cap.release()
        
        # Clear canvases
        self.dtl_canvas.delete("all")
        self.face_canvas.delete("all")
        
        self.log("Camera previews stopped")
    
    def update_camera_frames(self):
        """Update camera preview frames"""
        if not self.camera_previews_active:
            return
        
        try:
            # Read frames
            ret1, frame1 = self.dtl_cap.read()
            ret2, frame2 = self.face_cap.read()
            
            if ret1:
                self.display_frame(frame1, self.dtl_canvas)
            if ret2:
                self.display_frame(frame2, self.face_canvas)
            
            # Schedule next update
            self.root.after(33, self.update_camera_frames)  # ~30fps
            
        except Exception as e:
            logger.error(f"Camera frame update error: {e}")
            self.stop_camera_previews()
    
    def display_frame(self, frame, canvas):
        """Display a frame on a canvas"""
        # Get canvas size
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Resize frame to fit canvas
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (canvas_width, canvas_height))
        
        # Convert to PhotoImage
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        
        # Display on canvas
        canvas.delete("all")
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        canvas.image = photo  # Keep reference
    
    def toggle_session(self):
        """Toggle session on/off"""
        if not self.session_active:
            self.start_session()
        else:
            self.stop_session()
    
    def start_session(self):
        """Start a new practice session"""
        user_id = self.user_id_entry.get().strip()
        session_name = self.session_name_entry.get().strip()
        
        if not user_id:
            messagebox.showerror("Error", "Please enter a User ID")
            return
        
        # Check if cameras are running
        if not self.camera_previews_active:
            if messagebox.askyesno("Start Cameras?", "Camera previews are not active.\nStart them now?"):
                self.start_camera_previews()
        
        self.session_active = True
        self.current_user = user_id
        self.swing_count = 0
        
        # Update UI
        self.session_btn.config(text="■ Stop Session", bg=self.colors['error'])
        self.session_label.config(
            text=f"Active: {session_name}",
            fg=self.colors['accent']
        )
        self.user_id_entry.config(state='disabled')
        self.session_name_entry.config(state='disabled')
        
        self.log(f"Session started: {user_id} - {session_name}")
        self.update_status("Session active - waiting for shots...", self.colors['accent'])
        
        # Start the controller in async loop
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.run_controller(user_id, session_name),
                self.loop
            )
    
    def stop_session(self):
        """Stop the current session"""
        if not self.session_active:
            return
        
        self.session_active = False
        
        # Update UI
        self.session_btn.config(text="▶ Start Session", bg=self.colors['accent'])
        self.session_label.config(
            text="No Active Session",
            fg=self.colors['text_dim']
        )
        self.user_id_entry.config(state='normal')
        self.session_name_entry.config(state='normal')
        
        self.log(f"Session ended. Total swings: {self.swing_count}")
        self.update_status("Session stopped", self.colors['warning'])
        
        # Show summary
        messagebox.showinfo(
            "Session Complete",
            f"Session finished!\n\nTotal Swings: {self.swing_count}\nUser: {self.current_user}"
        )
    
    async def run_controller(self, user_id, session_name):
        """Run the main controller"""
        try:
            # Import here to avoid issues if not installed yet
            from swing_ai_core import SwingAIController
            
            self.controller = SwingAIController('config.json')
            await self.controller.start_session(user_id, session_name)
            
        except ImportError:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Could not import SwingAIController.\nMake sure all source files are present."
            ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Session error: {str(e)}"
            ))
            logger.error(f"Controller error: {e}", exc_info=True)
    
    def on_swing_detected(self, swing_data):
        """Callback when a swing is detected and analyzed"""
        self.swing_count += 1
        
        # Update UI
        self.swing_counter_label.config(text=f"{self.swing_count} Swings")
        self.stats_labels["Swings:"].config(text=str(self.swing_count))
        
        # Update stats
        if 'shot_data' in swing_data:
            shot = swing_data['shot_data']
            self.stats_labels["Last Club Speed:"].config(
                text=f"{shot.get('ClubSpeed', 0):.1f} mph"
            )
            self.stats_labels["Last Ball Speed:"].config(
                text=f"{shot.get('BallSpeed', 0):.1f} mph"
            )
        
        if 'overall_score' in swing_data:
            self.stats_labels["Avg Score:"].config(
                text=f"{swing_data['overall_score']:.1f}"
            )
        
        self.log(f"Swing #{self.swing_count} analyzed - Score: {swing_data.get('overall_score', 0):.1f}")
    
    def view_history(self):
        """Open session history window"""
        # TODO: Implement history viewer
        messagebox.showinfo("History", "History viewer coming soon!")
    
    def open_settings(self):
        """Open settings window"""
        SettingsWindow(self.root, self)
    
    def load_config(self):
        """Load configuration"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
            self.log("Configuration loaded")
        except FileNotFoundError:
            self.log("Config file not found - using defaults")
            self.config = {}
        except json.JSONDecodeError:
            self.log("Error reading config file")
            self.config = {}
    
    def log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        logger.info(message)
    
    def update_status(self, message, color=None):
        """Update status bar"""
        self.status_label.config(
            text=message,
            fg=color or self.colors['text_dim']
        )


class SettingsWindow:
    """Settings configuration window"""
    
    def __init__(self, parent, main_app):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("600x500")
        self.window.configure(bg=main_app.colors['bg_dark'])
        self.main_app = main_app
        
        # TODO: Implement settings UI
        tk.Label(
            self.window,
            text="Settings",
            font=('Arial', 18, 'bold'),
            bg=main_app.colors['bg_dark'],
            fg=main_app.colors['text']
        ).pack(pady=20)
        
        tk.Label(
            self.window,
            text="Settings panel coming soon!\n\nEdit config.json manually for now.",
            font=('Arial', 11),
            bg=main_app.colors['bg_dark'],
            fg=main_app.colors['text_dim']
        ).pack(pady=20)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ProMirrorGolfGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

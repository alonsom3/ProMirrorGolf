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
        self.default_color = color
        self.bind('<Enter>', lambda e: self.config(bg=self._lighten_color(color)))
        self.bind('<Leave>', lambda e: self.config(bg=color))

    def _lighten_color(self, color):
        """Lighten a hex color"""
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
        self.config = {}
        
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
        self.create_top_bar()
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
        
        # Bottom bar
        self.create_bottom_bar()
        
        # Log panel
        self.create_log_panel(right_panel)
    
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
        header = tk.Frame(parent, bg=self.colors['bg_medium'])
        header.pack(side=tk.TOP, fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            header,
            text="📹 Live Camera Feeds",
            font=('Arial', 16, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        self.preview_btn = ModernButton(
            header,
            text="Start Preview",
            command=self.toggle_camera_preview,
            color=self.colors['accent_dim']
        )
        self.preview_btn.pack(side=tk.RIGHT)
        
        cameras_container = tk.Frame(parent, bg=self.colors['bg_dark'])
        cameras_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
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
        
        self.session_btn = ModernButton(
            session_frame,
            text="▶ Start Session",
            command=self.toggle_session,
            color=self.colors['accent']
        )
        self.session_btn.grid(row=2, column=0, columnspan=2, pady=15, sticky=tk.EW)
    
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
    
    def create_log_panel(self, parent):
        """Create a scrollable log panel"""
        log_frame = tk.LabelFrame(
            parent,
            text="Logs",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=10,
            pady=10
        )
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            state=tk.NORMAL,
            height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def toggle_session(self):
        if not self.session_active:
            self.start_session()
        else:
            self.stop_session()
    
    # ===== Session Methods =====
    def start_session(self):
        """Start a new session"""
        self.session_active = True
        self.swing_count = 0
        self.session_label.config(text=f"Session: {self.session_name_entry.get()}")
        self.swing_counter_label.config(text=f"{self.swing_count} Swings")
        self.session_btn.config(text="■ Stop Session")
        self.log(f"Session '{self.session_name_entry.get()}' started")

    def stop_session(self):
        """Stop the current session"""
        self.session_active = False
        self.session_label.config(text="No Active Session")
        self.session_btn.config(text="▶ Start Session")
        self.log("Session stopped")
    
    # ===== Camera Methods =====
    def toggle_camera_preview(self):
        """Toggle camera preview on/off"""
        if not self.camera_previews_active:
            self.start_camera_previews()
        else:
            self.stop_camera_previews()
    
    def start_camera_previews(self):
        """Start showing camera previews"""
        try:
            dtl_id = self.config.get('cameras', {}).get('dtl_id', 2)
            face_id = self.config.get('cameras', {}).get('face_id', 0)

            self.dtl_cap = cv2.VideoCapture(dtl_id, cv2.CAP_DSHOW)
            self.face_cap = cv2.VideoCapture(face_id, cv2.CAP_DSHOW)

            if not self.dtl_cap.isOpened() or not self.face_cap.isOpened():
                messagebox.showerror(
                    "Camera Error",
                    f"Could not open cameras.\nDTL ID: {dtl_id}\nFace ID: {face_id}\nCheck connections and config.json"
                )
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
        self.dtl_canvas.delete("all")
        self.face_canvas.delete("all")
        self.log("Camera previews stopped")
    
    def update_camera_frames(self):
        """Update camera preview frames"""
        if not self.camera_previews_active:
            return
        try:
            ret1, frame1 = self.dtl_cap.read()
            ret2, frame2 = self.face_cap.read()
            if ret1:
                self.display_frame(frame1, self.dtl_canvas)
            if ret2:
                self.display_frame(frame2, self.face_canvas)
            self.root.after(33, self.update_camera_frames)
        except Exception as e:
            logger.error(f"Camera frame update error: {e}")
            self.stop_camera_previews()
    
    def display_frame(self, frame, canvas):
        """Display a frame on a canvas"""
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (canvas_width, canvas_height))
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        canvas.delete("all")
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        canvas.image = photo
    
    # ===== Config/Logging =====
    def load_config(self):
        """Load configuration"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
            self.log("Configuration loaded")
        except Exception:
            self.config = {}
            self.log("Error loading config - using defaults")
    
    def log(self, message):
        """Log to panel and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        logger.info(message)
    
    def update_status(self, message, color=None):
        self.status_label.config(
            text=message,
            fg=color or self.colors['text_dim']
        )


def main():
    root = tk.Tk()
    app = ProMirrorGolfGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

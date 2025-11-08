"""
ProMirrorGolf - Main Application with Enhanced UI
"""

import asyncio
import json
import logging
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from swing_ai_core import SwingAIController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('promirror.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProMirrorGolfGUI:
    """Enhanced GUI for ProMirrorGolf"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProMirrorGolf - AI Swing Analysis")
        self.root.geometry("800x600")
        
        # Set color scheme - Red theme
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'accent': '#dc143c',  # Crimson red
            'button_bg': '#dc143c',
            'button_fg': '#ffffff',
            'entry_bg': '#2d2d2d',
            'text_bg': '#0d0d0d',
            'success': '#00ff00',
            'warning': '#ffa500',
            'error': '#ff0000'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Application state
        self.app_controller = None
        self.session_active = False
        self.current_user_id = None
        self.swing_count = 0
        
        # Async event loop
        self.loop = None
        self.loop_thread = None
        
        self.create_widgets()
        self.setup_async_loop()
    
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Header Frame
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=80)
        header_frame.pack(fill='x', pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="⛳ ProMirrorGolf",
            font=("Arial", 28, "bold"),
            bg=self.colors['accent'],
            fg=self.colors['fg']
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            header_frame,
            text="AI-Powered Golf Swing Analysis",
            font=("Arial", 12),
            bg=self.colors['accent'],
            fg=self.colors['fg']
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # User Info Section
        user_frame = tk.LabelFrame(
            content_frame,
            text="Session Info",
            font=("Arial", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            relief='groove',
            bd=2
        )
        user_frame.pack(fill='x', pady=(0, 15))
        
        # User ID
        user_id_frame = tk.Frame(user_frame, bg=self.colors['bg'])
        user_id_frame.pack(fill='x', padx=10, pady=8)
        
        tk.Label(
            user_id_frame,
            text="User ID:",
            font=("Arial", 10),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            width=12,
            anchor='w'
        ).pack(side='left')
        
        self.user_id_var = tk.StringVar(value="golfer_1")
        self.user_id_entry = tk.Entry(
            user_id_frame,
            textvariable=self.user_id_var,
            font=("Arial", 10),
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            width=30
        )
        self.user_id_entry.pack(side='left', padx=5)
        
        # Session Name
        session_frame = tk.Frame(user_frame, bg=self.colors['bg'])
        session_frame.pack(fill='x', padx=10, pady=8)
        
        tk.Label(
            session_frame,
            text="Session Name:",
            font=("Arial", 10),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            width=12,
            anchor='w'
        ).pack(side='left')
        
        self.session_name_var = tk.StringVar(value=f"Practice {datetime.now().strftime('%m/%d/%Y')}")
        self.session_name_entry = tk.Entry(
            session_frame,
            textvariable=self.session_name_var,
            font=("Arial", 10),
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            width=30
        )
        self.session_name_entry.pack(side='left', padx=5)
        
        # Control Buttons
        button_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        button_frame.pack(pady=15)
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ START SESSION",
            command=self.toggle_session,
            font=("Arial", 14, "bold"),
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            activebackground='#b00000',
            activeforeground=self.colors['button_fg'],
            width=20,
            height=2,
            relief='raised',
            bd=3,
            cursor='hand2'
        )
        self.start_button.pack(pady=10)
        
        # Status Section
        status_frame = tk.LabelFrame(
            content_frame,
            text="Status",
            font=("Arial", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            relief='groove',
            bd=2
        )
        status_frame.pack(fill='both', expand=True, pady=(15, 0))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Ready to start",
            font=("Arial", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            anchor='w',
            justify='left'
        )
        self.status_label.pack(fill='x', padx=10, pady=10)
        
        # Swing counter
        self.swing_counter_label = tk.Label(
            status_frame,
            text="Swings Analyzed: 0",
            font=("Arial", 10),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w'
        )
        self.swing_counter_label.pack(fill='x', padx=10, pady=5)
        
        # Log display
        log_label = tk.Label(
            status_frame,
            text="Activity Log:",
            font=("Arial", 10, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w'
        )
        log_label.pack(fill='x', padx=10, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            status_frame,
            height=10,
            font=("Consolas", 9),
            bg=self.colors['text_bg'],
            fg='#00ff00',
            insertbackground=self.colors['fg'],
            wrap='word',
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Info footer
        info_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        info_frame.pack(fill='x', pady=(10, 0))
        
        info_text = "💡 Start GSPro and hit balls. Analysis appears automatically after each shot!"
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 9, "italic"),
            bg=self.colors['bg'],
            fg='#888888',
            wraplength=750
        )
        info_label.pack()
    
    def setup_async_loop(self):
        """Setup asyncio event loop in separate thread"""
        
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for loop to be ready
        while self.loop is None:
            pass
        
        self.log_message("System initialized")
    
    def toggle_session(self):
        """Toggle session start/stop"""
        if not self.session_active:
            self.start_session()
        else:
            self.stop_session()
    
    def start_session(self):
        """Start practice session"""
        user_id = self.user_id_var.get().strip()
        session_name = self.session_name_var.get().strip()
        
        if not user_id:
            messagebox.showerror("Error", "Please enter a User ID")
            return
        
        self.current_user_id = user_id
        self.session_active = True
        self.swing_count = 0
        
        # Update UI
        self.start_button.config(
            text="■ STOP SESSION",
            bg='#8b0000',
            activebackground='#dc143c'
        )
        self.status_label.config(
            text="🟢 Session Active - Waiting for shots...",
            fg=self.colors['success']
        )
        self.user_id_entry.config(state='disabled')
        self.session_name_entry.config(state='disabled')
        
        self.log_message(f"Started session: {session_name}")
        self.log_message(f"User: {user_id}")
        self.log_message("Ready to analyze swings!")
        
        # Start session in async loop
        asyncio.run_coroutine_threadsafe(
            self.run_session(user_id, session_name),
            self.loop
        )
    
    def stop_session(self):
        """Stop practice session"""
        self.session_active = False
        
        # Update UI
        self.start_button.config(
            text="▶ START SESSION",
            bg=self.colors['button_bg'],
            activebackground='#b00000'
        )
        self.status_label.config(
            text="⚫ Session Stopped",
            fg=self.colors['warning']
        )
        self.user_id_entry.config(state='normal')
        self.session_name_entry.config(state='normal')
        
        self.log_message(f"Session ended. Total swings: {self.swing_count}")
        
        # Stop in async loop
        if self.app_controller:
            asyncio.run_coroutine_threadsafe(
                self.app_controller.stop_session(),
                self.loop
            )
    
    async def run_session(self, user_id: str, session_name: str):
        """Run the swing analysis session"""
        try:
            # Initialize controller if needed
            if not self.app_controller:
                self.log_message("Initializing AI system...")
                from config_and_main import SwingAIApplication
                app = SwingAIApplication()
                await app.initialize()
                self.app_controller = app.controller
                self.log_message("AI system ready!")
            
            # Start session
            await self.app_controller.start_session(user_id, session_name)
            
        except Exception as e:
            error_msg = f"Session error: {str(e)}"
            self.log_message(f"ERROR: {error_msg}", level='error')
            logger.error(error_msg, exc_info=True)
            
            # Update UI on main thread
            self.root.after(0, lambda: messagebox.showerror("Session Error", error_msg))
            self.root.after(0, self.stop_session)
    
    def on_swing_analyzed(self, swing_data: dict):
        """Callback when a swing is analyzed"""
        self.swing_count += 1
        
        self.root.after(0, lambda: self.swing_counter_label.config(
            text=f"Swings Analyzed: {self.swing_count}"
        ))
        
        score = swing_data.get('overall_score', 0)
        self.log_message(f"Swing #{self.swing_count} analyzed - Score: {score:.1f}/100")
    
    def log_message(self, message: str, level: str = 'info'):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on level
        if level == 'error':
            color = self.colors['error']
        elif level == 'warning':
            color = self.colors['warning']
        elif level == 'success':
            color = self.colors['success']
        else:
            color = '#00ff00'
        
        def update_log():
            self.log_text.config(state='normal')
            self.log_text.insert('end', f"[{timestamp}] {message}\n", level)
            self.log_text.tag_config(level, foreground=color)
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        
        self.root.after(0, update_log)
    
    def on_closing(self):
        """Handle window close"""
        if self.session_active:
            if messagebox.askyesno("Confirm Exit", "Session is active. Stop and exit?"):
                self.stop_session()
                self.root.after(1000, self.cleanup_and_exit)
        else:
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Cleanup and exit"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()


def main():
    """Main entry point"""
    
    print("="*60)
    print("ProMirrorGolf - AI Swing Analysis")
    print("="*60)
    print()
    
    # Create and run GUI
    root = tk.Tk()
    app = ProMirrorGolfGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
"""
Dialogs Module - File dialogs and message boxes
Compatible with both tkinter and CustomTkinter
"""

try:
    import customtkinter as ctk
    from customtkinter import filedialog
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

import tkinter as tk
from tkinter import messagebox, filedialog as tk_filedialog
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class Dialogs:
    """Utility class for file dialogs and message boxes"""
    
    @staticmethod
    def ask_video_files(parent) -> Tuple[Optional[str], Optional[str]]:
        """
        Ask user to select DTL and Face video files
        
        Returns:
            Tuple of (dtl_path, face_path) or (None, None) if cancelled
        """
        # Use tkinter filedialog (works with both tkinter and CustomTkinter)
        dtl_path = tk_filedialog.askopenfilename(
            parent=parent,
            title="Select DTL (Down-the-Line) Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        
        if not dtl_path:
            return None, None
        
        face_path = tk_filedialog.askopenfilename(
            parent=parent,
            title="Select Face-on Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        
        if not face_path:
            return None, None
        
        return dtl_path, face_path
    
    @staticmethod
    def ask_save_video(parent, default_name: str = "swing_video.mp4") -> Optional[str]:
        """Ask user where to save exported video"""
        return tk_filedialog.asksaveasfilename(
            parent=parent,
            title="Export Swing Video",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*")
            ],
            initialfile=default_name
        )
    
    @staticmethod
    def ask_save_html(parent, default_name: str = "swing_report.html") -> Optional[str]:
        """Ask user where to save HTML report"""
        return tk_filedialog.asksaveasfilename(
            parent=parent,
            title="Save HTML Report",
            defaultextension=".html",
            filetypes=[
                ("HTML files", "*.html"),
                ("All files", "*.*")
            ],
            initialfile=default_name
        )
    
    @staticmethod
    def ask_save_csv(parent, default_name: str = "swing_data.csv") -> Optional[str]:
        """Ask user where to save CSV export"""
        return tk_filedialog.asksaveasfilename(
            parent=parent,
            title="Export CSV Data",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile=default_name
        )
    
    @staticmethod
    def ask_save_pdf(parent, default_name: str = "swing_report.pdf") -> Optional[str]:
        """Ask user where to save PDF report"""
        return tk_filedialog.asksaveasfilename(
            parent=parent,
            title="Export PDF Report",
            defaultextension=".pdf",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ],
            initialfile=default_name
        )
    
    @staticmethod
    def ask_batch_videos(parent) -> List[str]:
        """Ask user to select multiple video files for batch processing"""
        files = tk_filedialog.askopenfilenames(
            parent=parent,
            title="Select Videos for Batch Processing",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*")
            ]
        )
        return list(files) if files else []
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """Show info message box"""
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Show warning message box"""
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """Show error message box"""
        messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def ask_yes_no(parent, title: str, message: str) -> bool:
        """Ask yes/no question"""
        return messagebox.askyesno(title, message, parent=parent)


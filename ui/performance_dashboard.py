"""
Performance Dashboard - Real-time performance metrics display
Shows CPU, GPU, memory usage, FPS, ETA, and frame processing times
"""

import tkinter as tk
from typing import Dict, Optional
import logging
import psutil
import time
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """Performance dashboard widget showing real-time system metrics"""
    
    def __init__(self, parent, colors: Dict[str, str]):
        """
        Initialize performance dashboard
        
        Args:
            parent: Parent widget
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.colors = colors
        
        # Metrics tracking
        self.cpu_history = deque(maxlen=50)
        self.memory_history = deque(maxlen=50)
        self.gpu_history = deque(maxlen=50)
        self.fps_history = deque(maxlen=50)
        self.frame_time_history = deque(maxlen=50)
        
        # Current values
        self.current_cpu = 0.0
        self.current_memory = 0.0
        self.current_gpu = 0.0
        self.current_fps = 0.0
        self.current_frame_time = 0.0
        self.eta_seconds = 0.0
        
        # UI components
        self.frame = None
        self.update_interval = 500  # Update every 500ms
        self.update_job = None
        
        self.create_widgets()
        self.start_updates()
    
    def create_widgets(self):
        """Create dashboard widgets"""
        self.frame = tk.Frame(
            self.parent,
            bg=self.colors['bg_panel'],
            relief='flat',
            bd=0
        )
        self.frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Title
        title = tk.Label(
            self.frame,
            text="PERFORMANCE",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary']
        )
        title.pack(anchor='w', pady=(0, 12))
        
        # Metrics grid
        metrics_frame = tk.Frame(self.frame, bg=self.colors['bg_panel'])
        metrics_frame.pack(fill='both', expand=True)
        
        # CPU Usage
        self.cpu_label = tk.Label(
            metrics_frame,
            text="CPU: --%",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.cpu_label.pack(fill='x', pady=2)
        
        self.cpu_bar = tk.Canvas(
            metrics_frame,
            bg=self.colors['bg_panel'],
            height=4,
            highlightthickness=0
        )
        self.cpu_bar.pack(fill='x', pady=(0, 8))
        
        # Memory Usage
        self.memory_label = tk.Label(
            metrics_frame,
            text="Memory: -- MB",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.memory_label.pack(fill='x', pady=2)
        
        self.memory_bar = tk.Canvas(
            metrics_frame,
            bg=self.colors['bg_panel'],
            height=4,
            highlightthickness=0
        )
        self.memory_bar.pack(fill='x', pady=(0, 8))
        
        # GPU Usage (if available)
        self.gpu_label = tk.Label(
            metrics_frame,
            text="GPU: --%",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.gpu_label.pack(fill='x', pady=2)
        
        self.gpu_bar = tk.Canvas(
            metrics_frame,
            bg=self.colors['bg_panel'],
            height=4,
            highlightthickness=0
        )
        self.gpu_bar.pack(fill='x', pady=(0, 8))
        
        # FPS
        self.fps_label = tk.Label(
            metrics_frame,
            text="FPS: --",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.fps_label.pack(fill='x', pady=2)
        
        # Frame Time
        self.frame_time_label = tk.Label(
            metrics_frame,
            text="Frame Time: -- ms",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.frame_time_label.pack(fill='x', pady=2)
        
        # ETA
        self.eta_label = tk.Label(
            metrics_frame,
            text="ETA: --",
            font=("Segoe UI", 8),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.eta_label.pack(fill='x', pady=2)
    
    def start_updates(self):
        """Start periodic updates"""
        self.update_metrics()
    
    def update_metrics(self):
        """Update all performance metrics"""
        try:
            # CPU usage
            self.current_cpu = psutil.cpu_percent(interval=0.1)
            self.cpu_history.append(self.current_cpu)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.current_memory = memory.used / (1024 * 1024)  # MB
            memory_percent = memory.percent
            self.memory_history.append(memory_percent)
            
            # GPU usage (if available)
            self.current_gpu = self._get_gpu_usage()
            self.gpu_history.append(self.current_gpu)
            
            # Update UI
            self._update_ui()
            
        except Exception as e:
            logger.debug(f"Error updating performance metrics: {e}")
        
        # Schedule next update
        self.update_job = self.frame.after(self.update_interval, self.update_metrics)
    
    def _get_gpu_usage(self) -> float:
        """Get GPU usage percentage"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(util.gpu)
        except:
            return 0.0
    
    def _update_ui(self):
        """Update UI elements with current metrics"""
        # CPU
        self.cpu_label.config(text=f"CPU: {self.current_cpu:.1f}%")
        self._update_bar(self.cpu_bar, self.current_cpu / 100.0, self.colors['accent_red'])
        
        # Memory
        memory_mb = self.current_memory
        memory_gb = memory_mb / 1024
        self.memory_label.config(text=f"Memory: {memory_gb:.1f} GB")
        memory_percent = psutil.virtual_memory().percent
        self._update_bar(self.memory_bar, memory_percent / 100.0, self.colors['warning'])
        
        # GPU
        if self.current_gpu > 0:
            self.gpu_label.config(text=f"GPU: {self.current_gpu:.1f}%")
            self._update_bar(self.gpu_bar, self.current_gpu / 100.0, self.colors['good'])
        else:
            self.gpu_label.config(text="GPU: N/A")
            self._update_bar(self.gpu_bar, 0, self.colors['text_dim'])
        
        # FPS
        if self.current_fps > 0:
            self.fps_label.config(text=f"FPS: {self.current_fps:.1f}")
        else:
            self.fps_label.config(text="FPS: --")
        
        # Frame Time
        if self.current_frame_time > 0:
            color = self.colors['good'] if self.current_frame_time < 100 else self.colors['warning']
            self.frame_time_label.config(
                text=f"Frame Time: {self.current_frame_time:.1f} ms",
                fg=color
            )
        else:
            self.frame_time_label.config(text="Frame Time: -- ms")
        
        # ETA
        if self.eta_seconds > 0:
            eta_str = self._format_eta(self.eta_seconds)
            self.eta_label.config(text=f"ETA: {eta_str}")
        else:
            self.eta_label.config(text="ETA: --")
    
    def _update_bar(self, canvas, value: float, color: str):
        """Update progress bar"""
        canvas.delete("all")
        w = canvas.winfo_width()
        if w > 1:
            bar_width = int(w * min(value, 1.0))
            canvas.create_rectangle(
                0, 0, bar_width, 4,
                fill=color,
                outline=''
            )
    
    def _format_eta(self, seconds: float) -> str:
        """Format ETA as human-readable string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"
    
    def update_fps(self, fps: float):
        """Update FPS value"""
        self.current_fps = fps
        self.fps_history.append(fps)
    
    def update_frame_time(self, frame_time_ms: float):
        """Update frame processing time"""
        self.current_frame_time = frame_time_ms
        self.frame_time_history.append(frame_time_ms)
    
    def update_eta(self, eta_seconds: float):
        """Update ETA"""
        self.eta_seconds = eta_seconds
    
    def get_stats(self) -> Dict:
        """Get current performance statistics"""
        return {
            'cpu': self.current_cpu,
            'memory_mb': self.current_memory,
            'gpu': self.current_gpu,
            'fps': self.current_fps,
            'frame_time_ms': self.current_frame_time,
            'eta_seconds': self.eta_seconds
        }
    
    def destroy(self):
        """Clean up dashboard"""
        if self.update_job:
            self.frame.after_cancel(self.update_job)
        if self.frame:
            self.frame.destroy()


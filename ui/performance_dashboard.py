"""
Performance Dashboard - Real-time performance metrics display
Shows CPU, GPU, memory usage, FPS, ETA, and frame processing times
"""

import customtkinter as ctk
from typing import Dict, Optional
import logging
import psutil
import time
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceDashboard(ctk.CTkFrame):
    """Performance dashboard widget showing real-time system metrics"""
    
    def __init__(self, parent, colors: Dict[str, str]):
        """
        Initialize performance dashboard
        
        Args:
            parent: Parent widget
            colors: Color scheme dictionary
        """
        super().__init__(parent, fg_color=colors['bg_panel'], corner_radius=8)
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
        self.update_interval = 500  # Update every 500ms
        self.update_job = None
        
        self.create_widgets()
        self.start_updates()
    
    def create_widgets(self):
        """Create dashboard widgets"""
        self.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="PERFORMANCE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        title.pack(anchor='w', pady=(0, 12))
        
        # Metrics grid
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill='both', expand=True)
        
        # CPU Usage
        self.cpu_label = ctk.CTkLabel(
            metrics_frame,
            text="CPU: --%",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.cpu_label.pack(fill='x', pady=2)
        
        self.cpu_bar = ctk.CTkProgressBar(
            metrics_frame,
            height=4,
            fg_color=self.colors['bg_dark'],
            progress_color=self.colors['accent_red']
        )
        self.cpu_bar.pack(fill='x', pady=(0, 8))
        self.cpu_bar.set(0)
        
        # Memory Usage
        self.memory_label = ctk.CTkLabel(
            metrics_frame,
            text="Memory: -- GB",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.memory_label.pack(fill='x', pady=2)
        
        self.memory_bar = ctk.CTkProgressBar(
            metrics_frame,
            height=4,
            fg_color=self.colors['bg_dark'],
            progress_color=self.colors['warning']
        )
        self.memory_bar.pack(fill='x', pady=(0, 8))
        self.memory_bar.set(0)
        
        # GPU Usage (if available)
        self.gpu_label = ctk.CTkLabel(
            metrics_frame,
            text="GPU: --%",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.gpu_label.pack(fill='x', pady=2)
        
        self.gpu_bar = ctk.CTkProgressBar(
            metrics_frame,
            height=4,
            fg_color=self.colors['bg_dark'],
            progress_color=self.colors['good']
        )
        self.gpu_bar.pack(fill='x', pady=(0, 8))
        self.gpu_bar.set(0)
        
        # FPS
        self.fps_label = ctk.CTkLabel(
            metrics_frame,
            text="FPS: --",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.fps_label.pack(fill='x', pady=2)
        
        # Frame Time
        self.frame_time_label = ctk.CTkLabel(
            metrics_frame,
            text="Frame Time: -- ms",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
            anchor='w'
        )
        self.frame_time_label.pack(fill='x', pady=2)
        
        # ETA
        self.eta_label = ctk.CTkLabel(
            metrics_frame,
            text="ETA: --",
            font=ctk.CTkFont(size=8),
            text_color=self.colors['text_secondary'],
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
        self.update_job = self.after(self.update_interval, self.update_metrics)
    
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
        self.cpu_label.configure(text=f"CPU: {self.current_cpu:.1f}%")
        self.cpu_bar.set(self.current_cpu / 100.0)
        
        # Memory
        memory_mb = self.current_memory
        memory_gb = memory_mb / 1024
        self.memory_label.configure(text=f"Memory: {memory_gb:.1f} GB")
        memory_percent = psutil.virtual_memory().percent
        self.memory_bar.set(memory_percent / 100.0)
        
        # GPU
        if self.current_gpu > 0:
            self.gpu_label.configure(text=f"GPU: {self.current_gpu:.1f}%")
            self.gpu_bar.set(self.current_gpu / 100.0)
        else:
            self.gpu_label.configure(text="GPU: N/A")
            self.gpu_bar.set(0)
        
        # FPS
        if self.current_fps > 0:
            self.fps_label.configure(text=f"FPS: {self.current_fps:.1f}")
        else:
            self.fps_label.configure(text="FPS: --")
        
        # Frame Time
        if self.current_frame_time > 0:
            color = self.colors['good'] if self.current_frame_time < 100 else self.colors['warning']
            self.frame_time_label.configure(
                text=f"Frame Time: {self.current_frame_time:.1f} ms",
                text_color=color
            )
        else:
            self.frame_time_label.configure(text="Frame Time: -- ms")
        
        # ETA
        if self.eta_seconds > 0:
            eta_str = self._format_eta(self.eta_seconds)
            self.eta_label.configure(text=f"ETA: {eta_str}")
        else:
            self.eta_label.configure(text="ETA: --")
    
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
            self.after_cancel(self.update_job)
        super().destroy()


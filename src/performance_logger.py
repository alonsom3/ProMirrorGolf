"""
Performance Logger - Logs processing performance metrics to CSV
"""

import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import psutil
import time

logger = logging.getLogger(__name__)


class PerformanceLogger:
    """
    Logs performance metrics for video processing to CSV file
    Tracks: frame processing times, CPU/GPU usage, throughput
    """
    
    def __init__(self, log_dir: Path = Path("./logs")):
        """
        Initialize performance logger
        
        Args:
            log_dir: Directory to save performance logs
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.log_dir / "performance_log.csv"
        self._initialize_csv()
        self.current_session = None
        self.processing_times = []
        self.start_time = None
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'video_name',
                    'total_frames',
                    'total_time',
                    'avg_frame_time',
                    'max_frame_time',
                    'min_frame_time',
                    'p95_frame_time',
                    'cpu_usage',
                    'gpu_usage',
                    'memory_usage_mb',
                    'quality_mode',
                    'downsample_factor'
                ])
    
    def start_session(self, video_name: str, quality_mode: str = "balanced", downsample_factor: int = 1):
        """
        Start a new processing session
        
        Args:
            video_name: Name/identifier of the video being processed
            quality_mode: Quality mode used ("speed", "balanced", "quality")
            downsample_factor: Downsample factor used
        """
        self.current_session = {
            'video_name': video_name,
            'quality_mode': quality_mode,
            'downsample_factor': downsample_factor,
            'start_time': time.time(),
            'processing_times': []
        }
        self.start_time = time.time()
        logger.info(f"Performance logging started for: {video_name}")
    
    def log_frame_time(self, frame_time_ms: float):
        """
        Log processing time for a single frame
        
        Args:
            frame_time_ms: Processing time in milliseconds
        """
        if self.current_session:
            self.current_session['processing_times'].append(frame_time_ms)
    
    def end_session(self, total_frames: int):
        """
        End current session and write to CSV
        
        Args:
            total_frames: Total number of frames processed
        """
        if not self.current_session:
            return
        
        total_time = time.time() - self.start_time if self.start_time else 0
        processing_times = self.current_session['processing_times']
        
        if not processing_times:
            logger.warning("No processing times recorded for session")
            return
        
        # Calculate statistics
        avg_frame_time = sum(processing_times) / len(processing_times)
        max_frame_time = max(processing_times)
        min_frame_time = min(processing_times)
        p95_frame_time = self._percentile(processing_times, 95)
        
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
        gpu_usage = self._get_gpu_usage()
        
        # Write to CSV
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                self.current_session['video_name'],
                total_frames,
                f"{total_time:.2f}",
                f"{avg_frame_time:.2f}",
                f"{max_frame_time:.2f}",
                f"{min_frame_time:.2f}",
                f"{p95_frame_time:.2f}",
                f"{cpu_usage:.1f}",
                f"{gpu_usage:.1f}",
                f"{memory_usage:.1f}",
                self.current_session['quality_mode'],
                self.current_session['downsample_factor']
            ])
        
        logger.info(
            f"Performance logged: {total_frames} frames, "
            f"avg={avg_frame_time:.1f}ms, "
            f"total={total_time:.1f}s, "
            f"CPU={cpu_usage:.1f}%"
        )
        
        # Reset session
        self.current_session = None
        self.start_time = None
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a list"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_gpu_usage(self) -> float:
        """
        Get GPU usage percentage
        
        Returns:
            GPU usage percentage (0-100), or 0 if not available
        """
        try:
            # Try to use nvidia-ml-py if available
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(util.gpu)
        except ImportError:
            # pynvml not available, return 0
            return 0.0
        except Exception as e:
            logger.debug(f"Could not get GPU usage: {e}")
            return 0.0
    
    def get_recent_stats(self, limit: int = 10) -> List[Dict]:
        """
        Get recent performance statistics from CSV
        
        Args:
            limit: Number of recent entries to return
            
        Returns:
            List of dictionaries with performance data
        """
        if not self.csv_path.exists():
            return []
        
        stats = []
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Return last N entries
                for row in rows[-limit:]:
                    stats.append(row)
        except Exception as e:
            logger.error(f"Error reading performance log: {e}")
        
        return stats


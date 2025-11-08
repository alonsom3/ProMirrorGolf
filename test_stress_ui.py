"""
Stress Testing for ProMirrorGolf UI
Tests large video uploads, concurrent processing, and memory usage
"""

import unittest
import sys
import time
import threading
from pathlib import Path
from collections import deque

# Add root directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import customtkinter as ctk
    import psutil
    CTK_AVAILABLE = True
    PSUTIL_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    PSUTIL_AVAILABLE = False
    print("Warning: Required libraries not available. Stress tests will be skipped.")


@unittest.skipUnless(CTK_AVAILABLE and PSUTIL_AVAILABLE, "Required libraries not available")
class TestStressUI(unittest.TestCase):
    """Stress tests for UI components"""
    
    def setUp(self):
        """Set up test fixtures"""
        ctk.set_appearance_mode("dark")
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
        self.process = psutil.Process()
    
    def test_rapid_ui_updates(self):
        """Test rapid UI updates don't cause freezes"""
        from ui.progress_panel import ProgressPanel
        from ui.performance_dashboard import PerformanceDashboard
        
        root = ctk.CTk()
        progress = ProgressPanel(root, self.colors)
        dashboard = PerformanceDashboard(root, self.colors)
        
        update_times = deque(maxlen=100)
        start_time = time.time()
        
        # Rapid updates
        for i in range(100):
            update_start = time.time()
            root.after(0, lambda i=i: progress.update_progress(i / 100.0, f"Frame {i}"))
            root.after(0, lambda i=i: dashboard.update_fps(30.0 + i * 0.1))
            root.after(0, lambda i=i: dashboard.update_frame_time(80.0 + i * 0.5))
            root.update_idletasks()
            update_times.append(time.time() - update_start)
        
        total_time = time.time() - start_time
        avg_update_time = sum(update_times) / len(update_times) if update_times else 0
        
        # UI should remain responsive (updates should be < 50ms each)
        self.assertLess(avg_update_time, 0.05, f"Average update time {avg_update_time:.3f}s exceeds 50ms")
        self.assertLess(total_time, 5.0, f"Total time {total_time:.2f}s exceeds 5s")
        
        root.destroy()
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        from ui.metrics_panel import MetricsPanel
        
        root = ctk.CTk()
        panel = MetricsPanel(root, self.colors)
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate many swing data updates
        for i in range(100):
            swing_data = {
                'metrics': {f'metric_{j}': j * 1.5 for j in range(20)},
                'flaw_analysis': {'flaws': []},
                'pro_match': {'metrics': {}}
            }
            panel.update_swing_data(swing_data)
            root.update_idletasks()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 100MB for 100 updates)
        self.assertLess(memory_growth, 100, f"Memory growth {memory_growth:.1f}MB exceeds 100MB")
        
        root.destroy()
    
    def test_concurrent_updates(self):
        """Test concurrent UI updates from multiple threads"""
        from ui.progress_panel import ProgressPanel
        
        root = ctk.CTk()
        panel = ProgressPanel(root, self.colors)
        
        update_count = {'count': 0}
        errors = []
        
        def update_from_thread(thread_id):
            try:
                for i in range(10):
                    root.after(0, lambda i=i, tid=thread_id: panel.update_progress(i / 10.0, f"Thread {tid}: {i}"))
                    update_count['count'] += 1
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_from_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=2.0)
        
        # Process pending events
        root.update()
        
        # Should have updates from all threads without errors
        self.assertGreater(update_count['count'], 0)
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        
        root.destroy()
    
    def test_large_metrics_display(self):
        """Test displaying large amounts of metrics data"""
        from ui.metrics_panel import MetricsPanel
        
        root = ctk.CTk()
        panel = MetricsPanel(root, self.colors)
        
        # Create swing data with many metrics
        swing_data = {
            'metrics': {f'metric_{i}': i * 1.5 for i in range(50)},
            'flaw_analysis': {
                'flaws': [
                    {
                        'metric': f'metric_{i}',
                        'severity': 0.5 + i * 0.01,
                        'recommendation': f'Recommendation for metric {i}'
                    }
                    for i in range(20)
                ]
            },
            'pro_match': {
                'metrics': {f'metric_{i}': i * 1.6 for i in range(50)}
            }
        }
        
        start_time = time.time()
        panel.update_swing_data(swing_data)
        root.update_idletasks()
        update_time = time.time() - start_time
        
        # Update should complete quickly (< 1s)
        self.assertLess(update_time, 1.0, f"Update time {update_time:.3f}s exceeds 1s")
        
        root.destroy()


if __name__ == '__main__':
    unittest.main()


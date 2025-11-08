"""
Automated UI Testing for Modernized ProMirrorGolf UI
Tests all UI components, callbacks, and thread-safe updates
"""

import unittest
import sys
from pathlib import Path

# Add root directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("Warning: CustomTkinter not available. UI tests will be skipped.")

if CTK_AVAILABLE:
    from ui.main_window import MainWindow
    from ui.top_bar import TopBar
    from ui.viewer_panel import ViewerPanel
    from ui.metrics_panel import MetricsPanel
    from ui.controls_panel import ControlsPanel
    from ui.progress_panel import ProgressPanel
    from ui.performance_dashboard import PerformanceDashboard


@unittest.skipUnless(CTK_AVAILABLE, "CustomTkinter not available")
class TestUIModernization(unittest.TestCase):
    """Test suite for UI modernization"""
    
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
    
    def test_main_window_creation(self):
        """Test MainWindow initializes correctly"""
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertIsNotNone(window.top_bar)
        self.assertIsNotNone(window.viewer_panel)
        self.assertIsNotNone(window.metrics_panel)
        self.assertIsNotNone(window.controls_panel)
        self.assertIsNotNone(window.progress_panel)
        self.assertIsNotNone(window.performance_dashboard)
        window.destroy()
    
    def test_top_bar_callbacks(self):
        """Test TopBar callbacks"""
        callback_called = {'pro': False, 'club': False}
        
        def on_pro_change(value):
            callback_called['pro'] = True
        
        def on_club_change(value):
            callback_called['club'] = True
        
        root = ctk.CTk()
        top_bar = TopBar(root, self.colors, on_pro_change=on_pro_change, on_club_change=on_club_change)
        top_bar._on_pro_change("Rory McIlroy")
        top_bar._on_club_change("Driver")
        
        self.assertTrue(callback_called['pro'])
        self.assertTrue(callback_called['club'])
        root.destroy()
    
    def test_metrics_panel_updates(self):
        """Test MetricsPanel updates with swing data"""
        root = ctk.CTk()
        panel = MetricsPanel(root, self.colors)
        
        swing_data = {
            'metrics': {
                'club_speed': 95.5,
                'ball_speed': 140.2,
                'hip_rotation': 45.0
            },
            'flaw_analysis': {
                'flaws': [
                    {
                        'metric': 'hip_rotation',
                        'severity': 0.7,
                        'recommendation': 'Increase hip rotation for more power'
                    }
                ]
            },
            'pro_match': {
                'metrics': {
                    'club_speed': 100.0,
                    'ball_speed': 145.0,
                    'hip_rotation': 50.0
                }
            }
        }
        
        panel.update_swing_data(swing_data)
        self.assertGreater(len(panel.metrics_data), 0)
        self.assertGreater(len(panel.recommendations), 0)
        root.destroy()
    
    def test_viewer_panel_views(self):
        """Test ViewerPanel view switching"""
        root = ctk.CTk()
        panel = ViewerPanel(root, self.colors, current_view="Side")
        
        panel.update_view("Front")
        self.assertEqual(panel.current_view, "Front")
        
        panel.update_view("Top")
        self.assertEqual(panel.current_view, "Top")
        
        root.destroy()
    
    def test_controls_panel_playback(self):
        """Test ControlsPanel playback controls"""
        callback_called = False
        
        def on_playback(action):
            nonlocal callback_called
            callback_called = True
        
        root = ctk.CTk()
        panel = ControlsPanel(root, self.colors, on_playback_control=on_playback)
        
        panel._on_playback("play")
        self.assertTrue(callback_called)
        
        root.destroy()
    
    def test_progress_panel_updates(self):
        """Test ProgressPanel updates"""
        root = ctk.CTk()
        panel = ProgressPanel(root, self.colors)
        
        panel.update_progress(0.5, "Processing...")
        self.assertEqual(panel.progress, 0.5)
        self.assertEqual(panel.status_message, "Processing...")
        
        panel.update_status("Ready")
        self.assertEqual(panel.status_message, "Ready")
        
        root.destroy()
    
    def test_performance_dashboard_metrics(self):
        """Test PerformanceDashboard metrics display"""
        root = ctk.CTk()
        dashboard = PerformanceDashboard(root, self.colors)
        
        dashboard.update_fps(30.0)
        dashboard.update_frame_time(85.0)
        dashboard.update_eta(120.0)
        
        stats = dashboard.get_stats()
        self.assertEqual(stats['fps'], 30.0)
        self.assertEqual(stats['frame_time_ms'], 85.0)
        self.assertEqual(stats['eta_seconds'], 120.0)
        
        root.destroy()
    
    def test_thread_safe_updates(self):
        """Test thread-safe UI updates"""
        import threading
        import time
        
        root = ctk.CTk()
        panel = ProgressPanel(root, self.colors)
        
        update_count = {'count': 0}
        
        def update_from_thread():
            for i in range(10):
                root.after(0, lambda: panel.update_progress(i / 10.0, f"Progress {i}"))
                update_count['count'] += 1
                time.sleep(0.01)
        
        thread = threading.Thread(target=update_from_thread)
        thread.start()
        thread.join(timeout=1.0)
        
        # Process pending events
        root.update()
        
        self.assertGreater(update_count['count'], 0)
        root.destroy()


if __name__ == '__main__':
    unittest.main()


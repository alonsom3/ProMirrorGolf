"""
Enhanced Features Test Suite
Tests for frame caching, performance logging, analytics, batch processing, and exports
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.frame_cache import FrameCache
from src.performance_logger import PerformanceLogger
from src.analytics import SwingAnalytics
from src.batch_processor import BatchProcessor, ProcessingStatus
from src.export_manager import ExportManager
from src.database import SwingDatabase


class TestFrameCache(unittest.TestCase):
    """Test frame caching functionality"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = FrameCache(max_size=10, cache_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_cache_set_get(self):
        """Test basic cache set and get"""
        video_id = "test_video"
        frame_idx = 0
        pose_data = {"swing_detected": True, "dtl_poses": []}
        
        # Set cache
        self.cache.set(video_id, frame_idx, pose_data)
        
        # Get cache
        cached = self.cache.get(video_id, frame_idx)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["swing_detected"], True)
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        video_id = "test_video"
        
        # Fill cache beyond max_size
        for i in range(15):
            self.cache.set(video_id, i, {"frame": i})
        
        # First frames should be evicted
        self.assertIsNone(self.cache.get(video_id, 0))
        # Recent frames should still be cached
        self.assertIsNotNone(self.cache.get(video_id, 14))
    
    def test_cache_stats(self):
        """Test cache statistics"""
        video_id = "test_video"
        
        # Add some entries
        for i in range(5):
            self.cache.set(video_id, i, {"frame": i})
        
        # Get some entries
        for i in range(3):
            self.cache.get(video_id, i)
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 5)
        self.assertEqual(stats['hits'], 3)
        self.assertEqual(stats['misses'], 0)
        self.assertGreater(stats['hit_rate'], 0)
    
    def test_cache_clear(self):
        """Test cache clearing"""
        video_id = "test_video"
        
        # Add entries
        for i in range(5):
            self.cache.set(video_id, i, {"frame": i})
        
        # Clear
        self.cache.clear(video_id)
        
        # Should be empty
        self.assertIsNone(self.cache.get(video_id, 0))
        self.assertEqual(self.cache.get_stats()['size'], 0)


class TestPerformanceLogger(unittest.TestCase):
    """Test performance logging functionality"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = PerformanceLogger(log_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_log_session(self):
        """Test logging a processing session"""
        self.logger.start_session("test_video", "balanced", 1)
        
        # Log some frame times
        for i in range(10):
            self.logger.log_frame_time(50.0 + i)
        
        self.logger.end_session(10)
        
        # Check CSV was created
        csv_path = self.temp_dir / "performance_log.csv"
        self.assertTrue(csv_path.exists())
        
        # Read and verify
        import csv
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['video_name'], 'test_video')
            self.assertEqual(rows[0]['total_frames'], '10')
    
    def test_get_recent_stats(self):
        """Test getting recent statistics"""
        self.logger.start_session("test_video1", "speed", 2)
        for i in range(5):
            self.logger.log_frame_time(40.0)
        self.logger.end_session(5)
        
        self.logger.start_session("test_video2", "quality", 1)
        for i in range(5):
            self.logger.log_frame_time(60.0)
        self.logger.end_session(5)
        
        stats = self.logger.get_recent_stats(limit=2)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[-1]['video_name'], 'test_video2')


class TestAnalytics(unittest.TestCase):
    """Test analytics functionality"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.analytics = SwingAnalytics(output_dir=str(self.temp_dir))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_log_swing(self):
        """Test logging a swing"""
        swing_data = {
            'swing_id': 'test_swing_1',
            'metrics': {'hip_rotation_top': 45.0, 'shoulder_rotation_top': 90.0},
            'flaw_analysis': {'overall_score': 80.0, 'flaw_count': 2, 'flaws': []},
            'pro_match': {'golfer_name': 'Rory McIlroy', 'similarity_score': 85.0},
            'shot_data': {'BallSpeed': 150.0}
        }
        
        self.analytics.log_swing(**swing_data)
        
        self.assertEqual(len(self.analytics.swing_history), 1)
        self.assertEqual(self.analytics.swing_history[0]['swing_id'], 'test_swing_1')
    
    def test_get_best_swings(self):
        """Test getting best swings"""
        # Add multiple swings with different scores
        for i in range(5):
            swing_data = {
                'swing_id': f'swing_{i}',
                'metrics': {},
                'flaw_analysis': {'overall_score': 70.0 + i * 5, 'flaw_count': 0, 'flaws': []},
                'pro_match': {'golfer_name': 'Test Pro', 'similarity_score': 80.0},
                'shot_data': {}
            }
            self.analytics.log_swing(**swing_data)
        
        best = self.analytics.get_best_swings(limit=3)
        self.assertEqual(len(best), 3)
        self.assertEqual(best[0]['overall_score'], 90.0)  # Highest score first
    
    def test_get_improvement_trends(self):
        """Test getting improvement trends"""
        # Add swings over time
        for i in range(10):
            swing_data = {
                'swing_id': f'swing_{i}',
                'metrics': {'overall_score': 70.0 + i * 2},  # Improving over time
                'flaw_analysis': {'overall_score': 70.0 + i * 2, 'flaw_count': 0, 'flaws': []},
                'pro_match': {'golfer_name': 'Test Pro', 'similarity_score': 80.0},
                'shot_data': {}
            }
            self.analytics.log_swing(**swing_data)
        
        trend = self.analytics.get_improvement_trends('overall_score', days=30)
        self.assertEqual(trend['trend'], 'improving')
        self.assertGreater(len(trend['data']), 0)
    
    def test_export_csv(self):
        """Test CSV export"""
        # Add some swings
        for i in range(3):
            swing_data = {
                'swing_id': f'swing_{i}',
                'metrics': {'hip_rotation_top': 45.0 + i},
                'flaw_analysis': {'overall_score': 75.0 + i, 'flaw_count': 0, 'flaws': []},
                'pro_match': {'golfer_name': 'Test Pro', 'similarity_score': 80.0},
                'shot_data': {'BallSpeed': 150.0 + i}
            }
            self.analytics.log_swing(**swing_data)
        
        csv_path = self.analytics.export_csv()
        self.assertTrue(Path(csv_path).exists())


class TestBatchProcessor(unittest.TestCase):
    """Test batch processing functionality"""
    
    def setUp(self):
        # Create mock controller
        class MockController:
            def __init__(self):
                self.on_progress_update = None
            
            async def process_uploaded_videos(self, dtl_path, face_path, **kwargs):
                return {
                    'success': True,
                    'swing_id': 'test_swing',
                    'frames_processed': 100
                }
        
        self.controller = MockController()
        self.processor = BatchProcessor(self.controller, quality_mode="balanced", downsample_factor=1)
    
    def test_add_video(self):
        """Test adding video to queue"""
        video_id = self.processor.add_video("dtl.mp4", "face.mp4")
        self.assertIsNotNone(video_id)
        self.assertEqual(len(self.processor.queue), 1)
        self.assertEqual(self.processor.queue[0].status, ProcessingStatus.PENDING)
    
    def test_add_videos(self):
        """Test adding multiple videos"""
        pairs = [("dtl1.mp4", "face1.mp4"), ("dtl2.mp4", "face2.mp4")]
        video_ids = self.processor.add_videos(pairs)
        self.assertEqual(len(video_ids), 2)
        self.assertEqual(len(self.processor.queue), 2)
    
    def test_get_queue_status(self):
        """Test getting queue status"""
        self.processor.add_video("dtl.mp4", "face.mp4")
        status = self.processor.get_queue_status()
        self.assertEqual(status['total'], 1)
        self.assertEqual(status['pending'], 1)
    
    async def test_process_all(self):
        """Test processing all videos"""
        self.processor.add_video("dtl.mp4", "face.mp4")
        completed = await self.processor.process_all()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].status, ProcessingStatus.COMPLETED)


class TestExportManager(unittest.TestCase):
    """Test export functionality"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.export_manager = ExportManager(output_dir=str(self.temp_dir))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_export_swing_csv(self):
        """Test exporting swing to CSV"""
        swing_data = {
            'swing_id': 'test_swing',
            'timestamp': '2025-01-01T00:00:00',
            'session_id': 'test_session',
            'metrics': {'hip_rotation_top': 45.0, 'shoulder_rotation_top': 90.0},
            'flaw_analysis': {'overall_score': 80.0, 'flaw_count': 2},
            'pro_match': {'golfer_name': 'Rory McIlroy', 'similarity_score': 85.0},
            'shot_data': {'BallSpeed': 150.0, 'ClubSpeed': 100.0}
        }
        
        csv_path = self.export_manager.export_swing_csv(swing_data)
        self.assertTrue(Path(csv_path).exists())
    
    def test_export_session_csv(self):
        """Test exporting session to CSV"""
        session_data = [
            {
                'swing_id': f'swing_{i}',
                'timestamp': f'2025-01-01T00:00:0{i}',
                'session_id': 'test_session',
                'metrics': {'hip_rotation_top': 45.0 + i},
                'flaw_analysis': {'overall_score': 75.0 + i},
                'pro_match': {'golfer_name': 'Test Pro', 'similarity_score': 80.0},
                'shot_data': {}
            }
            for i in range(3)
        ]
        
        csv_path = self.export_manager.export_session_csv(session_data)
        self.assertTrue(Path(csv_path).exists())
    
    def test_export_swing_html(self):
        """Test exporting swing to HTML"""
        swing_data = {
            'swing_id': 'test_swing',
            'timestamp': '2025-01-01T00:00:00',
            'metrics': {'hip_rotation_top': 45.0},
            'flaw_analysis': {'overall_score': 80.0, 'flaws': []},
            'pro_match': {'golfer_name': 'Rory McIlroy', 'similarity_score': 85.0},
            'shot_data': {}
        }
        
        html_path = self.export_manager.export_swing_html(swing_data)
        self.assertTrue(Path(html_path).exists())
        
        # Verify HTML content
        with open(html_path, 'r') as f:
            content = f.read()
            self.assertIn('ProMirrorGolf', content)
            self.assertIn('test_swing', content)


def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFrameCache))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalytics))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestExportManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)


"""Automated tests for core ProMirrorGolf functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from core.session_manager import SessionManager, SessionModel, ShotModel
from core.buffer import CircularBuffer
from core.thumbnails import generate_thumbnail, get_thumbnail_path
from core.export import (
    export_session_to_csv_by_id,
    export_session_to_json_by_id,
    export_session_to_pdf_by_id,
)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager functionality."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.manager = SessionManager(str(self.db_path))
    
    def tearDown(self):
        """Clean up test database."""
        # Close any open database connections
        if hasattr(self, 'manager'):
            self.manager.end_session()
            # Give the database a moment to release file locks
            import time
            time.sleep(0.1)
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            # On Windows, sometimes files are still locked - try again after a delay
            import time
            time.sleep(0.5)
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass  # Best effort cleanup
    
    def test_start_session(self):
        """Test starting a session."""
        session_id = self.manager.start_session("Test Session", club="Driver", notes="Test notes")
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, int)
    
    def test_log_shot(self):
        """Test logging a shot."""
        session_id = self.manager.start_session("Test Session")
        shot_data = {
            "ClubSpeed": 100.5,
            "BallSpeed": 150.0,
            "TotalSpin": 2500,
            "LaunchAngle": 12.5,
            "CarryDistance": 250.0,
            "TotalDistance": 280.0,
        }
        shot_id = self.manager.log_shot(shot_data, "dtl_path.mp4", "face_path.mp4")
        self.assertIsNotNone(shot_id)
    
    def test_update_session(self):
        """Test updating session details."""
        session_id = self.manager.start_session("Original Name")
        success = self.manager.update_session(session_id, name="Updated Name", club="Iron", notes="Updated notes")
        self.assertTrue(success)
    
    def test_update_shot(self):
        """Test updating shot metadata."""
        session_id = self.manager.start_session("Test Session")
        shot_id = self.manager.log_shot({"ClubSpeed": 100}, None, None)
        
        # Test updating tags
        success = self.manager.update_shot(shot_id, tags=["good", "straight"])
        self.assertTrue(success)
        
        # Test updating favorite
        success = self.manager.update_shot(shot_id, is_favorite=True)
        self.assertTrue(success)
        
        # Test updating notes
        success = self.manager.update_shot(shot_id, notes="Great shot!")
        self.assertTrue(success)
    
    def test_delete_session(self):
        """Test deleting a session."""
        session_id = self.manager.start_session("Test Session")
        self.manager.log_shot({"ClubSpeed": 100}, None, None)
        
        success = self.manager.delete_session(session_id)
        self.assertTrue(success)
    
    def test_end_session(self):
        """Test ending a session."""
        session_id = self.manager.start_session("Test Session")
        self.manager.end_session()
        # Session should be ended (no exception)


class TestCircularBuffer(unittest.TestCase):
    """Test CircularBuffer functionality."""
    
    def setUp(self):
        """Set up test buffer."""
        self.buffer = CircularBuffer(max_frames=10)
    
    def test_add_and_dump(self):
        """Test adding frames and dumping buffer."""
        import numpy as np
        
        for i in range(5):
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            self.buffer.add(frame, datetime.now().timestamp())
        
        frames = self.buffer.dump()
        self.assertEqual(len(frames), 5)
    
    def test_max_size(self):
        """Test buffer respects max size."""
        import numpy as np
        
        for i in range(15):
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            self.buffer.add(frame, datetime.now().timestamp())
        
        frames = self.buffer.dump()
        self.assertEqual(len(frames), 10)  # Should only keep last 10


class TestThumbnails(unittest.TestCase):
    """Test thumbnail generation."""
    
    def setUp(self):
        """Set up test video file."""
        import cv2
        import numpy as np
        
        self.temp_dir = Path(tempfile.mkdtemp())
        self.video_path = self.temp_dir / "test_video.mp4"
        
        # Create a simple test video
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(self.video_path), fourcc, 30.0, (640, 480))
        
        for i in range(30):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :] = (i * 8, i * 8, i * 8)  # Gradual brightness
            out.write(frame)
        out.release()
    
    def tearDown(self):
        """Clean up test files."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_thumbnail(self):
        """Test thumbnail generation."""
        thumb_path = generate_thumbnail(self.video_path)
        self.assertIsNotNone(thumb_path)
        self.assertTrue(thumb_path.exists())
        self.assertEqual(thumb_path.suffix, ".jpg")
    
    def test_get_thumbnail_path(self):
        """Test thumbnail path generation."""
        thumb_path = get_thumbnail_path(self.video_path)
        expected = self.video_path.parent / f"{self.video_path.stem}_thumb.jpg"
        self.assertEqual(thumb_path, expected)


class TestExport(unittest.TestCase):
    """Test export functionality."""
    
    def setUp(self):
        """Set up test session with shots."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.manager = SessionManager(str(self.db_path))
        
        self.session_id = self.manager.start_session("Test Session", club="Driver")
        self.manager.log_shot(
            {"ClubSpeed": 100, "BallSpeed": 150, "TotalSpin": 2500},
            "dtl.mp4",
            "face.mp4"
        )
    
    def tearDown(self):
        """Clean up test files."""
        # Close any open database connections
        if hasattr(self, 'manager'):
            self.manager.end_session()
            # Give the database a moment to release file locks
            import time
            time.sleep(0.1)
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            # On Windows, sometimes files are still locked - try again after a delay
            import time
            time.sleep(0.5)
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass  # Best effort cleanup
    
    def test_export_csv(self):
        """Test CSV export."""
        output_path = self.temp_dir / "export.csv"
        result = export_session_to_csv_by_id(self.session_id, str(output_path), self.manager.engine)
        self.assertTrue(result)
        self.assertTrue(output_path.exists())
    
    def test_export_json(self):
        """Test JSON export."""
        output_path = self.temp_dir / "export.json"
        result = export_session_to_json_by_id(self.session_id, str(output_path), self.manager.engine)
        self.assertTrue(result)
        self.assertTrue(output_path.exists())
        
        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)
            self.assertIn("session", data)
            self.assertIn("shots", data)
    
    def test_export_pdf(self):
        """Test PDF export."""
        output_path = self.temp_dir / "export.pdf"
        result = export_session_to_pdf_by_id(self.session_id, str(output_path), self.manager.engine)
        self.assertTrue(result)
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()


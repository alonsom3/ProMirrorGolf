"""Integration tests for UI workflows."""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# Mock Qt before importing PyQt6
sys.modules['PyQt6'] = type(sys)('PyQt6')
sys.modules['PyQt6.QtCore'] = type(sys)('PyQt6.QtCore')
sys.modules['PyQt6.QtGui'] = type(sys)('PyQt6.QtGui')
sys.modules['PyQt6.QtWidgets'] = type(sys)('PyQt6.QtWidgets')

from core.session_manager import SessionManager


class TestUIFlows(unittest.TestCase):
    """Test UI workflow integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.manager = SessionManager(str(self.db_path))
    
    def tearDown(self):
        """Clean up test environment."""
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
    
    def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        # Start session
        session_id = self.manager.start_session("Test Session", club="Driver")
        self.assertIsNotNone(session_id)
        
        # Add shots
        for i in range(3):
            shot_data = {
                "ClubSpeed": 100 + i,
                "BallSpeed": 150 + i,
                "TotalSpin": 2500 + i * 100,
            }
            self.manager.log_shot(shot_data, f"dtl_{i}.mp4", f"face_{i}.mp4")
        
        # Update session
        self.manager.update_session(session_id, notes="Updated notes")
        
        # End session
        self.manager.end_session()
    
    def test_shot_metadata_workflow(self):
        """Test shot metadata editing workflow."""
        session_id = self.manager.start_session("Test Session")
        shot_id = self.manager.log_shot({"ClubSpeed": 100}, None, None)
        
        # Add tags
        self.manager.update_shot(shot_id, tags=["good", "straight"])
        
        # Mark as favorite
        self.manager.update_shot(shot_id, is_favorite=True)
        
        # Add notes
        self.manager.update_shot(shot_id, notes="Great shot!")
        
        # Update tags
        self.manager.update_shot(shot_id, tags=["excellent", "straight", "long"])
        
        # Remove favorite
        self.manager.update_shot(shot_id, is_favorite=False)


if __name__ == "__main__":
    unittest.main()


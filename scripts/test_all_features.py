"""Comprehensive test script for all new features."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import tempfile
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")
    try:
        from core.data_validation import validate_shot_data_dict, ValidationResult
        from core.cache_manager import CacheManager, get_session_cache, get_shot_cache
        from core.duplicate_detection import find_duplicates, merge_shots, DuplicateMatch
        from core.multi_monitor import detect_monitors, get_optimal_window_rect
        from core.data_import import import_shots_from_csv, import_shots_from_excel
        from app.widgets.import_dialog import ImportDialog
        from app.widgets.enhanced_table import FilterableTableWidget
        logger.info("[OK] All imports successful")
        return True
    except Exception as e:
        logger.error("[FAIL] Import error: %s", e)
        return False

def test_data_validation():
    """Test data validation functionality."""
    logger.info("Testing data validation...")
    try:
        from core.data_validation import validate_shot_data_dict, ValidationResult
        
        # Test valid data
        valid_data = {
            "ClubSpeed": 100.0,
            "BallSpeed": 150.0,
            "LaunchAngle": 12.0,
            "SpinRate": 3000.0,
            "CarryDistance": 250.0,
            "TotalDistance": 280.0,
        }
        result = validate_shot_data_dict(valid_data)
        assert result.is_valid, "Valid data should pass validation"
        logger.info("[OK] Valid data passes validation")
        
        # Test invalid data (ball speed too high)
        invalid_data = {
            "ClubSpeed": 100.0,
            "BallSpeed": 300.0,  # Unrealistically high
            "LaunchAngle": 12.0,
        }
        result = validate_shot_data_dict(invalid_data)
        assert not result.is_valid or len(result.errors) > 0, "Invalid data should fail validation"
        logger.info("[OK] Invalid data detected")
        
        # Test missing data (should be OK)
        minimal_data = {"ClubSpeed": 100.0}
        result = validate_shot_data_dict(minimal_data)
        assert result.is_valid, "Minimal data should be valid"
        logger.info("[OK] Minimal data passes validation")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Data validation test error: %s", e, exc_info=True)
        return False

def test_cache_manager():
    """Test cache manager functionality."""
    logger.info("Testing cache manager...")
    try:
        from core.cache_manager import CacheManager, get_session_cache, get_shot_cache
        
        cache = CacheManager(max_size=10, default_ttl=60)
        
        # Test set/get
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value", "Cache should return stored value"
        logger.info("[OK] Cache set/get works")
        
        # Test expiration (simulate by setting very short TTL)
        cache.set("expire_key", "expire_value", ttl=1)  # Expires in 1 second
        value = cache.get("expire_key")
        assert value == "expire_value", "Cache should return value before expiration"
        
        # Test invalidation
        cache.invalidate("expire_key")
        value = cache.get("expire_key")
        assert value is None, "Invalidated cache should return None"
        logger.info("[OK] Cache invalidation works")
        
        # Test get_or_compute
        def compute_func():
            return "computed_value"
        
        value = cache.get_or_compute("compute_key", compute_func)
        assert value == "computed_value", "get_or_compute should return computed value"
        logger.info("[OK] Cache get_or_compute works")
        
        # Test global caches
        session_cache = get_session_cache()
        shot_cache = get_shot_cache()
        assert session_cache is not None, "Session cache should be available"
        assert shot_cache is not None, "Shot cache should be available"
        logger.info("[OK] Global caches available")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Cache manager test error: %s", e, exc_info=True)
        return False

def test_duplicate_detection():
    """Test duplicate detection functionality."""
    logger.info("Testing duplicate detection...")
    try:
        from core.duplicate_detection import find_duplicates, merge_shots, DuplicateMatch
        
        # Create test shots
        shot1 = {
            "id": 1,
            "session_id": 1,
            "recorded_at": datetime.now().isoformat(),
            "club_speed": 100.0,
            "ball_speed": 150.0,
            "launch_angle": 12.0,
        }
        
        shot2 = {
            "id": 2,
            "session_id": 1,
            "recorded_at": datetime.now().isoformat(),  # Same time
            "club_speed": 100.5,  # Very similar
            "ball_speed": 150.2,  # Very similar
            "launch_angle": 12.1,  # Very similar
        }
        
        shot3 = {
            "id": 3,
            "session_id": 1,
            "recorded_at": datetime.now().isoformat(),
            "club_speed": 80.0,  # Different
            "ball_speed": 120.0,  # Different
            "launch_angle": 8.0,  # Different
        }
        
        shots = [shot1, shot2, shot3]
        
        # Find duplicates
        duplicates = find_duplicates(shots, similarity_threshold=0.8)
        assert len(duplicates) > 0, "Should find duplicates"
        assert duplicates[0].shot1_id in [1, 2], "Should match shot1 and shot2"
        assert duplicates[0].shot2_id in [1, 2], "Should match shot1 and shot2"
        logger.info("[OK] Duplicate detection works")
        
        # Test merge
        merged = merge_shots(shot1, shot2, prefer="first")
        assert "club_speed" in merged, "Merged shot should have metrics"
        logger.info("[OK] Shot merging works")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Duplicate detection test error: %s", e, exc_info=True)
        return False

def test_pagination():
    """Test pagination functionality."""
    logger.info("Testing pagination...")
    try:
        from PyQt6.QtWidgets import QApplication
        from app.widgets.enhanced_table import FilterableTableWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create table widget
        table = FilterableTableWidget(
            columns=["Col1", "Col2", "Col3"],
            table_id="test_table"
        )
        
        # Test pagination enable
        def data_loader(offset, limit):
            return [["Row", str(i), "Data"] for i in range(offset, offset + limit)]
        
        table.enable_pagination(100, data_loader)
        assert table.pagination_enabled, "Pagination should be enabled"
        assert table.total_rows == 100, "Total rows should be set"
        logger.info("[OK] Pagination enable works")
        
        # Test disable
        table.disable_pagination()
        assert not table.pagination_enabled, "Pagination should be disabled"
        logger.info("[OK] Pagination disable works")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Pagination test error: %s", e, exc_info=True)
        return False

def test_multi_monitor():
    """Test multi-monitor support."""
    logger.info("Testing multi-monitor support...")
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        from core.multi_monitor import detect_monitors, get_optimal_window_rect, get_monitor_info
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test monitor detection
        layouts = detect_monitors()
        assert isinstance(layouts, list), "Should return list of layouts"
        logger.info("[OK] Monitor detection works (found %d layout(s))", len(layouts))
        
        # Test get optimal rect
        widget = QWidget()
        rect = get_optimal_window_rect(widget, "main", 0)
        assert rect.width() > 0 and rect.height() > 0, "Should return valid rect"
        logger.info("[OK] Optimal window rect calculation works")
        
        # Test monitor info
        info = get_monitor_info()
        assert "count" in info, "Should return monitor info"
        assert info["count"] >= 1, "Should detect at least one monitor"
        logger.info("[OK] Monitor info retrieval works (%d monitor(s))", info["count"])
        
        return True
    except Exception as e:
        logger.error("[FAIL] Multi-monitor test error: %s", e, exc_info=True)
        return False

def test_import_dialog():
    """Test import dialog can be created."""
    logger.info("Testing import dialog...")
    try:
        from PyQt6.QtWidgets import QApplication
        from app.widgets.import_dialog import ImportDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create mock session manager
        class MockSessionManager:
            def __init__(self):
                self.engine = None
        
        session_manager = MockSessionManager()
        
        # Create dialog (don't show it)
        dialog = ImportDialog(session_manager)
        assert dialog is not None, "Dialog should be created"
        assert hasattr(dialog, 'file_path_edit'), "Dialog should have file path edit"
        assert hasattr(dialog, 'button_box'), "Dialog should have button box"
        logger.info("[OK] Import dialog creation works")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Import dialog test error: %s", e, exc_info=True)
        return False

def test_enhanced_table():
    """Test enhanced table widget."""
    logger.info("Testing enhanced table...")
    try:
        from PyQt6.QtWidgets import QApplication
        from app.widgets.enhanced_table import FilterableTableWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create table
        table = FilterableTableWidget(
            columns=["Time", "Club Speed", "Ball Speed"],
            table_id="test_table"
        )
        
        # Test add row
        row = table.add_row(["10:00:00", "100.0", "150.0"])
        assert row >= 0, "Should return valid row index"
        assert table.table.rowCount() == 1, "Should have one row"
        logger.info("[OK] Table add_row works")
        
        # Test clear
        table.clear()
        assert table.table.rowCount() == 0, "Should have no rows after clear"
        logger.info("[OK] Table clear works")
        
        return True
    except Exception as e:
        logger.error("[FAIL] Enhanced table test error: %s", e, exc_info=True)
        return False

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Running comprehensive feature tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Data Validation", test_data_validation),
        ("Cache Manager", test_cache_manager),
        ("Duplicate Detection", test_duplicate_detection),
        ("Pagination", test_pagination),
        ("Multi-Monitor", test_multi_monitor),
        ("Import Dialog", test_import_dialog),
        ("Enhanced Table", test_enhanced_table),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error("[FAIL] Test '%s' crashed: %s", name, e, exc_info=True)
            results.append((name, False))
    
    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        logger.info("%s %s", status, name)
    
    logger.info("=" * 60)
    logger.info("Total: %d/%d tests passed", passed, total)
    logger.info("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

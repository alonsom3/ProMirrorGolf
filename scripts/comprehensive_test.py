"""Comprehensive test suite for ProMirrorGolf."""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all critical imports."""
    logger.info("Testing imports...")
    try:
        from app.main_window import MainWindow
        from app.design_constants import get_current_colors, COLORS, LIGHT_COLORS
        from app.theme import get_current_theme
        from core.session_manager import SessionManager
        from core.camera_service import CameraService
        from core.config import ConfigManager
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_theme_system():
    """Test theme system."""
    logger.info("Testing theme system...")
    try:
        from app.design_constants import get_current_colors
        from app.theme import get_current_theme
        from core.themes import ThemeManager
        
        colors = get_current_colors()
        theme = get_current_theme()
        
        assert colors is not None, "Colors should not be None"
        assert theme is not None, "Theme should not be None"
        assert hasattr(colors, 'BACKGROUND_BASE'), "Colors should have BACKGROUND_BASE"
        
        logger.info("✓ Theme system working")
        return True
    except Exception as e:
        logger.error(f"✗ Theme system test failed: {e}")
        return False

def test_widget_imports():
    """Test widget imports."""
    logger.info("Testing widget imports...")
    try:
        from app.widgets.session_browser import SessionBrowser
        from app.widgets.shot_review_window import ShotReviewWindow
        from app.widgets.analysis_dashboard import AnalysisDashboard
        from app.widgets.settings_dialog import SettingsDialog
        from app.widgets.goals_dialog import GoalsDialog
        from app.widgets.recent_shots_dialog import RecentShotsDialog
        from app.widgets.report_builder_dialog import ReportBuilderDialog
        from app.widgets.session_comparison import SessionComparison
        from app.widgets.video_comparison_window import VideoComparisonWindow
        from app.widgets.trajectory_3d import Trajectory3DDialog
        logger.info("✓ All widget imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Widget import failed: {e}")
        return False

def test_core_modules():
    """Test core module imports."""
    logger.info("Testing core modules...")
    try:
        from core.analytics import calculate_consistency_metrics, calculate_tempo_ratio, estimate_swing_plane_angle
        from core.backup import create_backup, restore_backup
        from core.layout_manager import LayoutManager
        from core.recent_shots import RecentShotsTracker
        from core.session_templates import TemplateManager
        logger.info("✓ All core module imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Core module import failed: {e}")
        return False

def test_web_api():
    """Test web API imports."""
    logger.info("Testing web API...")
    try:
        from web.api import create_api
        logger.info("✓ Web API import successful")
        return True
    except Exception as e:
        logger.error(f"✗ Web API import failed: {e}")
        return False

def test_syntax():
    """Test Python syntax for all files."""
    logger.info("Testing Python syntax...")
    import py_compile
    import os
    
    errors = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"{filepath}: {e}")
    
    if errors:
        logger.error(f"✗ Syntax errors found: {len(errors)}")
        for error in errors[:10]:
            logger.error(f"  {error}")
        return False
    else:
        logger.info("✓ All Python files have valid syntax")
        return True

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Comprehensive Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Theme System", test_theme_system),
        ("Widget Imports", test_widget_imports),
        ("Core Modules", test_core_modules),
        ("Web API", test_web_api),
        ("Syntax", test_syntax),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info("")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"✗ {name} test crashed: {e}")
            results.append((name, False))
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())


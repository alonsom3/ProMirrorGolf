"""Quick test script to verify application can start and basic functionality works."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all critical modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.main_window import MainWindow
        print("  [OK] MainWindow")
    except Exception as e:
        print(f"  [FAIL] MainWindow: {e}")
        return False
    
    try:
        from app.widgets.shot_review_window import ShotReviewWindow
        print("  [OK] ShotReviewWindow")
    except Exception as e:
        print(f"  [FAIL] ShotReviewWindow: {e}")
        return False
    
    try:
        from app.widgets.session_browser import SessionBrowser
        print("  [OK] SessionBrowser")
    except Exception as e:
        print(f"  [FAIL] SessionBrowser: {e}")
        return False
    
    try:
        from app.widgets.analysis_dashboard import AnalysisDashboard
        print("  [OK] AnalysisDashboard")
    except Exception as e:
        print(f"  [FAIL] AnalysisDashboard: {e}")
        return False
    
    try:
        from app.widgets.session_comparison import SessionComparison
        print("  [OK] SessionComparison")
    except Exception as e:
        print(f"  [FAIL] SessionComparison: {e}")
        return False
    
    try:
        from core.session_manager import SessionManager
        print("  [OK] SessionManager")
    except Exception as e:
        print(f"  [FAIL] SessionManager: {e}")
        return False
    
    try:
        from core.thumbnails import generate_thumbnail
        print("  [OK] Thumbnails")
    except Exception as e:
        print(f"  [FAIL] Thumbnails: {e}")
        return False
    
    try:
        from core.export import export_session_to_csv
        print("  [OK] Export")
    except Exception as e:
        print(f"  [FAIL] Export: {e}")
        return False
    
    return True

def test_methods_exist():
    """Test that required methods exist."""
    print("\nTesting method existence...")
    
    try:
        from app.main_window import MainWindow
        methods = [
            '_setup_shortcuts',
            '_setup_context_menus',
            '_show_shot_table_context_menu',
            '_toggle_shot_favorite',
            '_edit_shot_tags',
            '_edit_shot_notes',
            '_delete_selected_shots',
            '_refresh_shot_table',
        ]
        
        for method in methods:
            if hasattr(MainWindow, method):
                print(f"  [OK] MainWindow.{method}")
            else:
                print(f"  [FAIL] MainWindow.{method} - MISSING")
                return False
    except Exception as e:
        print(f"  [FAIL] Error checking methods: {e}")
        return False
    
    try:
        from app.widgets.shot_review_window import ShotReviewWindow
        if hasattr(ShotReviewWindow, '_setup_shortcuts'):
            print("  [OK] ShotReviewWindow._setup_shortcuts")
        else:
            print("  [FAIL] ShotReviewWindow._setup_shortcuts - MISSING")
            return False
    except Exception as e:
        print(f"  [FAIL] Error checking ShotReviewWindow: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from core.config import ConfigManager
        config = ConfigManager()
        print("  [OK] ConfigManager initialized")
        
        # Test some key config values
        db_path = config.get("storage.database", "data/promirror.db")
        print(f"  [OK] Database path: {db_path}")
        
        fps = config.get("cameras.fps", 60)
        print(f"  [OK] FPS: {fps}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Config error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ProMirrorGolf Quick Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_methods_exist()
    all_passed &= test_config()
    
    print()
    print("=" * 60)
    if all_passed:
        print("[OK] All tests passed! Application should be ready to run.")
        print("\nNext steps:")
        print("  1. Run: python main.py")
        print("  2. Test keyboard shortcuts")
        print("  3. Test context menus (right-click on shot table)")
        print("  4. Verify all features work as expected")
    else:
        print("[FAIL] Some tests failed. Please review errors above.")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)

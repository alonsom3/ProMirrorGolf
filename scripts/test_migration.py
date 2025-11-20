"""Test script to verify design system migration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all design system imports work."""
    print("Testing design system imports...")
    try:
        from app.design_constants import COLORS, SPACING, TYPOGRAPHY, SIZES
        from app.style_helpers import style_button, style_input, style_label
        print("[OK] Design constants imported successfully")
        print(f"   COLORS.ACCENT: {COLORS.ACCENT}")
        print(f"   SPACING.MEDIUM: {SPACING.MEDIUM}")
        print(f"   TYPOGRAPHY.BODY: {TYPOGRAPHY.BODY}")
        print(f"   SIZES.BORDER_RADIUS_SMALL: {SIZES.BORDER_RADIUS_SMALL}")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_style_helpers():
    """Test style helper functions."""
    print("\nTesting style helpers...")
    try:
        from app.style_helpers import style_button, style_input, style_label
        from app.design_constants import COLORS, TYPOGRAPHY
        
        # Test style_label
        label_style = style_label(secondary=True, size=12)
        assert "color:" in label_style
        assert COLORS.TEXT_SECONDARY in label_style
        print("[OK] style_label() works")
        
        # Test style_button
        button_style = style_button(variant="primary")
        assert COLORS.ACCENT in button_style
        print("[OK] style_button() works")
        
        # Test style_input
        input_style = style_input()
        assert COLORS.BACKGROUND_CONTROL in input_style
        print("[OK] style_input() works")
        
        return True
    except Exception as e:
        print(f"[FAIL] Style helper error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_imports():
    """Test that migrated widgets can be imported."""
    print("\nTesting widget imports...")
    try:
        # Test import_dialog
        from app.widgets.import_dialog import ImportDialog
        print("[OK] ImportDialog imported")
        
        # Test settings_dialog
        from app.widgets.settings_dialog import SettingsDialog
        print("[OK] SettingsDialog imported")
        
        # Test shot_review_window
        from app.widgets.shot_review_window import ShotReviewWindow
        print("[OK] ShotReviewWindow imported")
        
        # Test main_window
        from app.main_window import MainWindow
        print("[OK] MainWindow imported")
        
        return True
    except Exception as e:
        print(f"[FAIL] Widget import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_theme():
    """Test that theme can be imported and generated."""
    print("\nTesting theme generation...")
    try:
        from app.theme import DARK_THEME
        from app.design_constants import COLORS
        assert len(DARK_THEME) > 0
        assert COLORS.BACKGROUND_BASE in DARK_THEME or "#0f1116" in DARK_THEME
        print("[OK] DARK_THEME generated successfully")
        print(f"   Theme length: {len(DARK_THEME)} characters")
        return True
    except Exception as e:
        print(f"[FAIL] Theme error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Design System Migration Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Style Helpers", test_style_helpers()))
    results.append(("Widget Imports", test_widget_imports()))
    results.append(("Theme", test_theme()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! Migration successful.")
        return 0
    else:
        print("[FAILURE] Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


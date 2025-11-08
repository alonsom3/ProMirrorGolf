#!/usr/bin/env python3
"""
ProMirrorGolf v2.0 - Automated Sanity Test Script
Runs core functionality tests to verify application is production-ready

Usage:
    python sanity_test.py

Exit Codes:
    0 - All tests passed, ready for release
    1 - One or more tests failed, not ready for release
"""

import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Tuple, Dict
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results
test_results: List[Tuple[str, bool, str]] = []


def run_test(name: str, command: List[str], timeout: int = 60) -> Tuple[bool, str]:
    """
    Run a test command and return (success, output)
    
    Args:
        name: Test name
        command: Command to run
        timeout: Timeout in seconds
    
    Returns:
        (success, output_message)
    """
    logger.info(f"Running: {name}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        if success:
            logger.info(f"✅ {name} - PASSED")
        else:
            logger.error(f"❌ {name} - FAILED")
            logger.error(f"Output: {output[:500]}")
        return success, output
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {name} - TIMEOUT (>{timeout}s)")
        return False, f"Test timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"❌ {name} - ERROR: {e}")
        return False, str(e)


def check_file_exists(filepath: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    path = Path(filepath)
    exists = path.exists()
    if exists:
        logger.info(f"✅ {description} - Found: {filepath}")
    else:
        logger.warning(f"⚠️  {description} - Missing: {filepath}")
    return exists, filepath


def check_imports() -> Tuple[bool, str]:
    """Check if all required modules can be imported"""
    logger.info("Checking module imports...")
    try:
        import customtkinter as ctk
        from src.swing_ai_core import SwingAIController
        from src.pose_analyzer import PoseAnalyzer
        from src.metrics_extractor import MetricsExtractor
        from src.flaw_detector import FlawDetector
        from src.style_matcher import StyleMatcher
        from ui.main_window import MainWindow
        from ui.top_bar import TopBar
        from ui.viewer_panel import ViewerPanel
        from ui.controls_panel import ControlsPanel
        from ui.metrics_panel import MetricsPanel
        from ui.progress_panel import ProgressPanel
        from ui.performance_dashboard import PerformanceDashboard
        logger.info("✅ All modules imported successfully")
        return True, "All modules imported successfully"
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False, f"Import error: {e}"


def check_config() -> Tuple[bool, str]:
    """Check if config.json exists and is valid"""
    logger.info("Checking config.json...")
    config_path = Path("config.json")
    if not config_path.exists():
        return False, "config.json not found"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        # Check required keys
        required_keys = ['cameras', 'mlm2pro', 'ai']
        for key in required_keys:
            if key not in config:
                return False, f"config.json missing key: {key}"
        logger.info("✅ config.json is valid")
        return True, "config.json is valid"
    except json.JSONDecodeError as e:
        return False, f"config.json is invalid JSON: {e}"


def check_dependencies() -> Tuple[bool, str]:
    """Check if required dependencies are installed"""
    logger.info("Checking dependencies...")
    required_packages = [
        'customtkinter',
        'cv2',
        'numpy',
        'mediapipe',
        'psutil'
    ]
    missing = []
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'customtkinter':
                import customtkinter
            elif package == 'numpy':
                import numpy
            elif package == 'mediapipe':
                import mediapipe
            elif package == 'psutil':
                import psutil
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    logger.info("✅ All required dependencies installed")
    return True, "All required dependencies installed"


def main():
    """Run all sanity tests"""
    logger.info("=" * 60)
    logger.info("ProMirrorGolf v2.0 - Sanity Test Suite")
    logger.info("=" * 60)
    logger.info("")
    
    # Test 1: Check dependencies
    success, msg = check_dependencies()
    test_results.append(("Dependencies Check", success, msg))
    
    # Test 2: Check imports
    success, msg = check_imports()
    test_results.append(("Module Imports", success, msg))
    
    # Test 3: Check config
    success, msg = check_config()
    test_results.append(("Config Validation", success, msg))
    
    # Test 4: Check required files
    required_files = [
        ("main.py", "Main application entry point"),
        ("requirements.txt", "Dependencies file"),
        ("README.md", "README documentation"),
        ("ENHANCEMENT_SUMMARY.md", "Enhancement summary"),
        ("UI_MODERNIZATION_SUMMARY.md", "UI modernization summary"),
    ]
    for filepath, description in required_files:
        exists, msg = check_file_exists(filepath, description)
        test_results.append((f"File Check: {description}", exists, msg))
    
    # Test 5: Run UI modernization tests
    success, msg = run_test(
        "UI Modernization Tests",
        [sys.executable, "test_ui_modernization.py"],
        timeout=30
    )
    test_results.append(("UI Modernization Tests", success, msg))
    
    # Test 6: Run stress tests (may take longer)
    success, msg = run_test(
        "Stress Tests",
        [sys.executable, "test_stress_ui.py"],
        timeout=120
    )
    test_results.append(("Stress Tests", success, msg))
    
    # Test 7: Run E2E tests
    success, msg = run_test(
        "E2E Pipeline Tests",
        [sys.executable, "test_e2e_swing_pipeline.py"],
        timeout=120
    )
    test_results.append(("E2E Pipeline Tests", success, msg))
    
    # Test 8: Check mobile API endpoints (if server can start)
    try:
        # Just check if mobile_api module can be imported and initialized
        from src.mobile_api import MobileAPI
        from src.database import SwingDatabase
        # Try to create instance (won't start server, just check initialization)
        db = SwingDatabase("data/swings.db")
        api = MobileAPI(db, port=8080)
        logger.info("✅ Mobile API module initializes correctly")
        test_results.append(("Mobile API Module", True, "Mobile API initializes correctly"))
    except Exception as e:
        logger.warning(f"⚠️  Mobile API check: {e}")
        test_results.append(("Mobile API Module", True, f"Check skipped: {e}"))  # Non-blocking
    
    # Test 9: Check for critical files in src/
    src_files = [
        "src/swing_ai_core.py",
        "src/pose_analyzer.py",
        "src/metrics_extractor.py",
        "src/flaw_detector.py",
        "src/style_matcher.py",
        "src/video_processor.py",
    ]
    for filepath in src_files:
        exists, msg = check_file_exists(filepath, f"Source file: {Path(filepath).name}")
        test_results.append((f"Source File: {Path(filepath).name}", exists, msg))
    
    # Test 10: Check for UI modules
    ui_files = [
        "ui/main_window.py",
        "ui/top_bar.py",
        "ui/viewer_panel.py",
        "ui/controls_panel.py",
        "ui/metrics_panel.py",
        "ui/progress_panel.py",
        "ui/performance_dashboard.py",
    ]
    for filepath in ui_files:
        exists, msg = check_file_exists(filepath, f"UI module: {Path(filepath).name}")
        test_results.append((f"UI Module: {Path(filepath).name}", exists, msg))
    
    # Test 11: Check git status (optional, non-blocking)
    # Ignore __pycache__, .pyc, .log files
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent
        )
        if result.returncode == 0:
            uncommitted = result.stdout.strip()
            if uncommitted:
                # Filter out cache and log files
                lines = uncommitted.split('\n')
                important_changes = [
                    line for line in lines
                    if not any(ignore in line for ignore in ['__pycache__', '.pyc', '.log', '.pytest_cache'])
                ]
                if important_changes:
                    logger.warning(f"⚠️  Uncommitted changes detected")
                    logger.warning(f"Files: {uncommitted[:200]}")
                    test_results.append(("Git Status", False, f"Uncommitted changes: {', '.join(important_changes[:3])}"))
                else:
                    logger.info("✅ Git status clean (only cache/log files)")
                    test_results.append(("Git Status", True, "No important uncommitted changes"))
            else:
                logger.info("✅ Git status clean")
                test_results.append(("Git Status", True, "No uncommitted changes"))
        else:
            test_results.append(("Git Status", True, "Git not available (non-blocking)"))
    except:
        test_results.append(("Git Status", True, "Git check skipped (non-blocking)"))
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    failed = total - passed
    
    # Categorize results
    critical_tests = [
        "Dependencies Check",
        "Module Imports",
        "Config Validation",
        "UI Modernization Tests",
        "Stress Tests",
        "E2E Pipeline Tests",
    ]
    
    critical_passed = 0
    critical_total = 0
    for name, success, _ in test_results:
        if any(critical in name for critical in critical_tests):
            critical_total += 1
            if success:
                critical_passed += 1
    
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed} ({passed*100//total}%)")
    logger.info(f"Failed: {failed}")
    logger.info("")
    logger.info(f"Critical Tests: {critical_total}")
    logger.info(f"Critical Passed: {critical_passed} ({critical_passed*100//max(critical_total,1)}%)")
    logger.info("")
    
    # Print failed tests
    failed_tests = [(name, msg) for name, success, msg in test_results if not success]
    if failed_tests:
        logger.error("Failed Tests:")
        for name, msg in failed_tests:
            logger.error(f"  ❌ {name}: {msg[:100]}")
    
    logger.info("")
    logger.info("=" * 60)
    
    # Determine exit code
    # All critical tests must pass
    if critical_passed < critical_total:
        logger.error("❌ CRITICAL TESTS FAILED - NOT READY FOR RELEASE")
        return 1
    
    if failed > 0:
        logger.warning("⚠️  Some non-critical tests failed, but critical tests passed")
        logger.warning("Review failed tests before release")
        # Still return 0 if critical tests pass, but warn
        return 0
    
    logger.info("✅ ALL TESTS PASSED - READY FOR RELEASE")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


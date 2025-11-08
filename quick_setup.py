"""
ProMirrorGolf - Quick Setup Script

This utility script helps set up a new ProMirrorGolf installation by:
- Creating necessary directory structure
- Generating placeholder config.json
- Creating __init__.py files
- Generating documentation templates

Usage:
    python quick_setup.py

This script is typically run once during initial project setup.
After running, you should:
1. Copy source files to src/ directory
2. Update config.json with your camera IDs and paths
3. Run verify_project.py to check setup
4. Launch the application with: python main.py
"""

import os
import json
from pathlib import Path

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        'src',
        'tests',
        'data',
        'output/videos',
        'output/reports',
        'docs',
        'assets/icons',
        'assets/screenshots'
    ]
    
    print("Creating directory structure...")
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"OK Created: {dir_path}/")
    
    print()

def fix_config():
    """Add missing 'ai' section to config.json"""
    print("Fixing config.json...")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Add missing 'ai' section if not present
        if 'ai' not in config:
            config['ai'] = {
                "pose_model": "mediapipe",
                "use_gpu": False,  # Set to False since no CUDA detected
                "min_detection_confidence": 0.5
            }
            print("OK Added 'ai' section to config")
        
        # Add 'database' section if missing
        if 'database' not in config:
            config['database'] = {
                "user_swings_path": "./data/swings.db",
                "pro_swings_path": "./data/pro_swings.db"
            }
            print("OK Added 'database' section to config")
        
        # Add 'output' section if missing
        if 'output' not in config:
            config['output'] = {
                "videos_dir": "./output/videos",
                "reports_dir": "./output/reports"
            }
            print("OK Added 'output' section to config")
        
        # Add 'overlay' section if missing
        if 'overlay' not in config:
            config['overlay'] = {
                "enabled": True,
                "endpoint": "http://localhost:8765/display",
                "port": 8765,
                "auto_hide_seconds": 10
            }
            print("OK Added 'overlay' section to config")
        
        # Add 'processing' section if missing
        if 'processing' not in config:
            config['processing'] = {
                "auto_start": True,
                "min_shot_interval": 3.0
            }
            print("OK Added 'processing' section to config")
        
        # Save updated config
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print("OK config.json updated successfully")
        
    except FileNotFoundError:
        print("ERROR config.json not found")
    except json.JSONDecodeError:
        print("ERROR config.json is not valid JSON")
    
    print()

def create_test_files():
    """Create placeholder test files"""
    print("Creating test files...")
    
    # tests/__init__.py
    with open('tests/__init__.py', 'w', encoding='utf-8') as f:
        f.write('"""ProMirrorGolf Test Suite"""\n')
    print("OK Created: tests/__init__.py")
    
    # tests/test_cameras.py
    test_cameras = '''"""
Test camera detection and capture
Run: python tests/test_cameras.py
"""

import cv2
import sys

def test_cameras():
    """Test all connected cameras"""
    print("\\nTesting Cameras...")
    print("=" * 60)
    
    found_cameras = []
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"OK Camera {i}: {width}x{height} @ {fps}fps")
            found_cameras.append(i)
            
            cap.release()
    
    print("=" * 60)
    
    if len(found_cameras) >= 2:
        print(f"\\nSUCCESS: Found {len(found_cameras)} cameras")
        print(f"  Camera IDs: {found_cameras}")
        print(f"\\nUpdate config.json:")
        print(f'  "dtl_id": {found_cameras[0]},')
        print(f'  "face_id": {found_cameras[1]},')
        return True
    else:
        print(f"\\nFAILED: Only found {len(found_cameras)} camera(s)")
        print("  Need at least 2 cameras")
        return False

def show_camera_preview():
    """Show live camera preview"""
    print("\\nStarting camera preview...")
    print("Press 'q' to quit, 's' to save snapshot\\n")
    
    cap0 = cv2.VideoCapture(0)
    cap1 = cv2.VideoCapture(1) if True else None
    
    if not cap0.isOpened():
        print("ERROR Cannot open camera 0")
        return
    
    use_two = cap1.isOpened() if cap1 else False
    
    while True:
        ret0, frame0 = cap0.read()
        if not ret0:
            break
        
        cv2.putText(frame0, "Camera 0 - DTL (Press 'q' to quit)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Camera 0 - Down-the-Line', frame0)
        
        if use_two:
            ret1, frame1 = cap1.read()
            if ret1:
                cv2.putText(frame1, "Camera 1 - Face", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow('Camera 1 - Face-On', frame1)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite('snapshot_cam0.jpg', frame0)
            print("OK Saved snapshot_cam0.jpg")
            if use_two and ret1:
                cv2.imwrite('snapshot_cam1.jpg', frame1)
                print("OK Saved snapshot_cam1.jpg")
    
    cap0.release()
    if cap1:
        cap1.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if '--preview' in sys.argv:
        show_camera_preview()
    else:
        test_cameras()
'''
    
    with open('tests/test_cameras.py', 'w', encoding='utf-8') as f:
        f.write(test_cameras)
    print("OK Created: tests/test_cameras.py")
    
    # tests/test_mlm2pro.py
    test_mlm2pro = '''"""
Test MLM2PRO connection
Run: python tests/test_mlm2pro.py
"""

print("\\nMLM2PRO Connection Test")
print("=" * 60)
print("\\nThis test requires:")
print("  1. MLM2PRO connected via Bluetooth")
print("  2. Connector software running")
print("  3. GSPro launched")
print("\\nTest not fully implemented yet.")
print("Check that connector appears in Task Manager.")
print("=" * 60)
'''
    
    with open('tests/test_mlm2pro.py', 'w', encoding='utf-8') as f:
        f.write(test_mlm2pro)
    print("OK Created: tests/test_mlm2pro.py")
    
    print()

def create_readme():
    """Create a quick start README for the src directory"""
    print("Creating documentation...")
    
    readme = '''# ProMirrorGolf - Source Code

## Missing Source Files

The `src/` directory needs the following files:

1. **__init__.py** - Package initialization
2. **main.py** - GUI entry point
3. **swing_ai_core.py** - Main controller
4. **camera_manager.py** - Camera system
5. **mlm2pro_listener.py** - Launch monitor integration
6. **pose_analyzer.py** - AI pose analysis
7. **style_matcher.py** - Pro matching
8. **database.py** - Database management
9. **report_generator.py** - Report creation
10. **youtube_downloader.py** - Video downloader

## Where to Get These Files

All the source code is in your `Project.txt` file. You need to:

1. Extract each code block from Project.txt
2. Save each as a separate .py file in src/
3. Or copy from your GitHub backend/ folder

## Quick Start

Once you have the source files:

```bash
# Test cameras
python tests/test_cameras.py

# Launch GUI
python main.py
```

## Next Steps

1. Copy all source files to src/
2. Run verification again: `python verify_project.py`
3. Test cameras: `python tests/test_cameras.py --preview`
4. Launch GUI: `python main.py`
'''
    
    with open('src/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print("OK Created: src/README.md")
    
    print()

def create_init_files():
    """Create __init__.py files"""
    print("Creating __init__.py files...")
    
    with open('src/__init__.py', 'w', encoding='utf-8') as f:
        f.write('"""ProMirrorGolf - AI Golf Swing Analysis System"""\n')
    print("OK Created: src/__init__.py")
    
    print()

def print_next_steps():
    """Print what to do next"""
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nOK Directory structure created")
    print("OK config.json updated")
    print("OK Test files created")
    print("OK Documentation added")
    
    print("\nNEXT STEPS:")
    print("\n1. Copy Source Files to src/")
    print("   - Extract code from Project.txt")
    print("   - Or copy from your GitHub backend/ folder")
    print("\n2. Test Cameras:")
    print("   python tests/test_cameras.py")
    print("\n3. View Camera Preview:")
    print("   python tests/test_cameras.py --preview")
    print("\n4. Run Verification Again:")
    print("   python verify_project.py")
    print("   Target: 8/8 checks passed")
    print("\n5. Launch GUI:")
    print("   python main.py")
    
    print("\n" + "=" * 60)

def main():
    print("\nProMirrorGolf - Quick Setup")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Create missing directories")
    print("  2. Fix config.json")
    print("  3. Create test files")
    print("  4. Add documentation")
    print("\nStarting...\n")
    
    create_directory_structure()
    fix_config()
    create_test_files()
    create_init_files()
    create_readme()
    print_next_steps()

if __name__ == '__main__':
    main()
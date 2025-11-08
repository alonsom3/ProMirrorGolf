"""
ProMirrorGolf - Comprehensive Project Verification Script
Run this to verify your entire project setup
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
import importlib.util

class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

class ProjectVerifier:
    """Verifies the entire ProMirrorGolf project"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.errors = []
        self.warnings = []
        self.missing_files = []
        
    def verify_all(self) -> bool:
        """Run all verification checks"""
        print_header("ProMirrorGolf Project Verification")
        
        checks = [
            ("Project Structure", self.check_structure),
            ("Python Environment", self.check_python),
            ("Dependencies", self.check_dependencies),
            ("Configuration", self.check_config),
            ("Source Files", self.check_source_files),
            ("Import Checks", self.check_imports),
            ("Database Setup", self.check_databases),
            ("Hardware Detection", self.check_hardware),
        ]
        
        results = []
        for name, check_func in checks:
            print(f"\n{Colors.BOLD}Checking {name}...{Colors.END}")
            passed = check_func()
            results.append((name, passed))
        
        # Print summary
        self.print_summary(results)
        
        return all(passed for _, passed in results)
    
    def check_structure(self) -> bool:
        """Verify project directory structure"""
        required_structure = {
            'src': ['__init__.py', 'main.py', 'swing_ai_core.py', 
                   'camera_manager.py', 'mlm2pro_listener.py', 
                   'pose_analyzer.py', 'style_matcher.py', 
                   'database.py', 'report_generator.py', 
                   'youtube_downloader.py'],
            'tests': ['__init__.py', 'test_cameras.py', 'test_mlm2pro.py'],
            'data': [],
            'output': ['videos', 'reports'],
            'docs': [],
        }
        
        passed = True
        
        for directory, files in required_structure.items():
            dir_path = self.project_root / directory
            
            if not dir_path.exists():
                print_error(f"Missing directory: {directory}/")
                self.missing_files.append(f"{directory}/")
                passed = False
            else:
                print_success(f"Found directory: {directory}/")
                
                # Check files in directory
                for file in files:
                    file_path = dir_path / file
                    if not file_path.exists():
                        print_warning(f"  Missing file: {directory}/{file}")
                        self.missing_files.append(f"{directory}/{file}")
                    else:
                        print_success(f"  Found: {directory}/{file}")
        
        # Check root files
        root_files = ['config.json', 'requirements.txt', 'README.md']
        for file in root_files:
            file_path = self.project_root / file
            if not file_path.exists():
                print_warning(f"Missing root file: {file}")
                self.missing_files.append(file)
            else:
                print_success(f"Found: {file}")
        
        return passed
    
    def check_python(self) -> bool:
        """Check Python version"""
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print_error(f"Python version {version.major}.{version.minor} is too old")
            print_error("Required: Python 3.9 or higher")
            return False
        
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required packages are installed"""
        required_packages = {
            'cv2': 'opencv-python',
            'mediapipe': 'mediapipe',
            'numpy': 'numpy',
            'matplotlib': 'matplotlib',
            'aiohttp': 'aiohttp',
            'yt_dlp': 'yt-dlp',
            'PIL': 'Pillow',
        }
        
        all_installed = True
        
        for module_name, package_name in required_packages.items():
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    print_error(f"Missing: {package_name}")
                    all_installed = False
                else:
                    print_success(f"Installed: {package_name}")
            except ImportError:
                print_error(f"Missing: {package_name}")
                all_installed = False
        
        if not all_installed:
            print_info("\nTo install missing packages:")
            print_info("pip install -r requirements.txt")
        
        return all_installed
    
    def check_config(self) -> bool:
        """Verify config.json exists and is valid"""
        config_path = self.project_root / 'config.json'
        
        if not config_path.exists():
            print_error("config.json not found")
            print_info("Creating default config.json...")
            self.create_default_config()
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            required_keys = [
                'cameras', 'mlm2pro', 'ai', 
                'database', 'output', 'overlay'
            ]
            
            for key in required_keys:
                if key in config:
                    print_success(f"Config section: {key}")
                else:
                    print_error(f"Missing config section: {key}")
                    return False
            
            return True
            
        except json.JSONDecodeError:
            print_error("config.json is not valid JSON")
            return False
    
    def check_source_files(self) -> bool:
        """Check that all source files have valid Python syntax"""
        src_dir = self.project_root / 'src'
        
        if not src_dir.exists():
            print_error("src/ directory not found")
            return False
        
        python_files = list(src_dir.glob('*.py'))
        all_valid = True
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file.name, 'exec')
                print_success(f"Valid syntax: {py_file.name}")
            except SyntaxError as e:
                print_error(f"Syntax error in {py_file.name}: {e}")
                all_valid = False
        
        return all_valid
    
    def check_imports(self) -> bool:
        """Check if source files can be imported"""
        src_dir = self.project_root / 'src'
        
        if not src_dir.exists():
            return False
        
        # Add src to path temporarily
        sys.path.insert(0, str(src_dir))
        
        modules_to_check = [
            'swing_ai_core',
            'camera_manager',
            'mlm2pro_listener',
            'pose_analyzer',
            'style_matcher',
            'database',
            'report_generator',
        ]
        
        all_importable = True
        
        for module in modules_to_check:
            try:
                importlib.import_module(module)
                print_success(f"Can import: {module}")
            except ImportError as e:
                print_error(f"Cannot import {module}: {e}")
                all_importable = False
            except Exception as e:
                print_warning(f"Import warning for {module}: {e}")
        
        sys.path.pop(0)
        return all_importable
    
    def check_databases(self) -> bool:
        """Check database files"""
        data_dir = self.project_root / 'data'
        
        if not data_dir.exists():
            print_warning("data/ directory not found - will be created on first run")
            return True
        
        user_db = data_dir / 'swings.db'
        pro_db = data_dir / 'pro_swings.db'
        
        if user_db.exists():
            print_success("User database exists")
        else:
            print_info("User database will be created on first run")
        
        if pro_db.exists():
            print_success("Pro database exists")
            # Check if it has data
            try:
                import sqlite3
                conn = sqlite3.connect(str(pro_db))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM pro_swings")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 0:
                    print_success(f"Pro database has {count} swings")
                else:
                    print_warning("Pro database is empty - need to import swings")
            except:
                print_warning("Pro database exists but couldn't verify contents")
        else:
            print_warning("Pro database not found - need to build it")
            print_info("Run: python src/build_pro_database.py")
        
        return True
    
    def check_hardware(self) -> bool:
        """Check for cameras and GPU"""
        print_info("Checking hardware...")
        
        # Check cameras
        try:
            import cv2
            camera_count = 0
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_count += 1
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print_success(f"Camera {i}: {width}x{height} @ {fps}fps")
                    cap.release()
            
            if camera_count >= 2:
                print_success(f"Found {camera_count} cameras (need 2)")
            elif camera_count == 1:
                print_warning("Only 1 camera found (need 2)")
            else:
                print_warning("No cameras found")
        except:
            print_warning("Could not check cameras")
        
        # Check GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print_success(f"GPU detected: {gpu_name}")
            else:
                print_warning("No CUDA GPU detected - will use CPU (slower)")
        except:
            print_info("Could not check GPU (torch not installed)")
        
        return True
    
    def create_default_config(self):
        """Create a default config.json file"""
        default_config = {
            "cameras": {
                "dtl_id": 0,
                "face_id": 1,
                "fps": 120,
                "resolution": [1920, 1080],
                "buffer_seconds": 10.0
            },
            "mlm2pro": {
                "connector_path": "C:/MLM2PRO-OGS-Connector/connector.exe",
                "connector_type": "opengolfsim",
                "listen_port": 5555
            },
            "ai": {
                "pose_model": "mediapipe",
                "use_gpu": True,
                "min_detection_confidence": 0.5
            },
            "database": {
                "user_swings_path": "./data/swings.db",
                "pro_swings_path": "./data/pro_swings.db"
            },
            "output": {
                "videos_dir": "./output/videos",
                "reports_dir": "./output/reports"
            },
            "overlay": {
                "enabled": True,
                "endpoint": "http://localhost:8765/display",
                "port": 8765,
                "auto_hide_seconds": 10
            },
            "processing": {
                "auto_start": True,
                "min_shot_interval": 3.0
            }
        }
        
        config_path = self.project_root / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print_success("Created default config.json")
    
    def print_summary(self, results: List[Tuple[str, bool]]):
        """Print verification summary"""
        print_header("Verification Summary")
        
        passed = sum(1 for _, p in results if p)
        total = len(results)
        
        for name, passed_check in results:
            if passed_check:
                print_success(f"{name}: PASSED")
            else:
                print_error(f"{name}: FAILED")
        
        print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.END}\n")
        
        if self.missing_files:
            print_warning("Missing files:")
            for file in self.missing_files:
                print(f"  - {file}")
            print()
        
        if passed == total:
            print_success("✓ All checks passed! Project is ready to run.")
            print_info("\nNext steps:")
            print_info("1. Review and update config.json with your settings")
            print_info("2. Build the pro swing database (if not done)")
            print_info("3. Test cameras: python tests/test_cameras.py")
            print_info("4. Run the application: python src/main.py")
        else:
            print_error("✗ Some checks failed. Please fix the issues above.")
            print_info("\nCommon fixes:")
            print_info("- Install dependencies: pip install -r requirements.txt")
            print_info("- Create missing directories: mkdir src tests data output")
            print_info("- Copy source files from the project log")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify ProMirrorGolf project')
    parser.add_argument('--path', type=str, help='Project root path', default='.')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    
    args = parser.parse_args()
    
    verifier = ProjectVerifier(Path(args.path))
    success = verifier.verify_all()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

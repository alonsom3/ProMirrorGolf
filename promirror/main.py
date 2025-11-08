"""
ProMirrorGolf - Main Application
Entry point for the application
"""
import asyncio
import argparse
import logging
import json  # Moved import to top
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProMirrorGolf:
    def __init__(self, config_path="config.json"):
        
        # --- FIX 1: Build the correct, full path to the config file ---
        # This makes sure it finds 'config.json' in the root folder,
        # not inside the 'promirror' folder.
        try:
            script_dir = Path(__file__).parent.resolve()
            root_dir = script_dir.parent
            full_config_path = root_dir / config_path
        except NameError:
            # Fallback if __file__ is not defined (e.g., in interactive shell)
            full_config_path = config_path

        self.config = self.load_config(full_config_path)
        logger.info("ProMirrorGolf initialized")
    
    def load_config(self, path):
        # --- FIX 2: Fixed the NameError ---
        # Changed 'config_path' to 'path' to match the function's argument
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"FATAL: Config file not found at {path}")
            logger.error("Please ensure 'config.json' exists in the root project directory.")
            exit(1)
        except json.JSONDecodeError:
            logger.error(f"FATAL: Error decoding 'config.json'. Check for syntax errors (like missing commas).")
            exit(1)
    
    async def start(self, user_id="default"):
        logger.info(f"Starting session for user: {user_id}")
        
        # Import components
        from promirror.capture.camera_manager import DualCameraManager
        from promirror.analysis.pose_detector import PoseDetector
        from promirror.server.web_server import start_server
        
        # Initialize
        self.cameras = DualCameraManager(
            self.config['cameras']['dtl_id'],
            self.config['cameras']['face_id'],
            self.config['cameras']['fps']
        )
        
        self.pose_detector = PoseDetector()
        
        # Start web server
        await start_server(self.config['server']['port'])
        
        # Start main loop
        await self.main_loop()
    
    async def main_loop(self):
        logger.info("Waiting for swings...")
        while True:
            await asyncio.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(description="ProMirrorGolf")
    parser.add_argument('command', choices=['start', 'calibrate', 'add-pro'])
    parser.add_argument('--user', default='default')
    args = parser.parse_args()
    
    app = ProMirrorGolf()
    
    if args.command == 'start':
        asyncio.run(app.start(args.user))


if __name__ == "__main__":
    main()
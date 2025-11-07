"""
ProMirrorGolf - Main Application
Entry point for the application
"""
import asyncio
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProMirrorGolf:
    def __init__(self, config_path="config.json"):
        self.config = self.load_config(config_path)
        logger.info("ProMirrorGolf initialized")
    
    def load_config(self, path):
        import json
        with open(path, 'r') as f:
            return json.load(f)
    
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

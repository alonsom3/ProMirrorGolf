# File: swing_ai_core.py

import asyncio
import logging
from backend.camera_manager import CameraManager
from backend.pose_analyzer import PoseAnalyzer
from backend.database import Database
from backend.style_matcher import StyleMatcher
from backend.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class SwingAIController:
    """Main controller for Swing AI"""

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = None
        self.camera_manager = None
        self.pose_analyzer = None
        self.db = None
        self.style_matcher = None
        self.report_generator = None
        self.session_active = False
        self.current_user = None
        self.session_name = None

        self.load_config()

    def load_config(self):
        import json
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            logger.info("SwingAIController config loaded")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}

    async def initialize(self):
        """Initialize all AI components"""
        logger.info("Initializing Swing AI modules...")

        self.camera_manager = CameraManager(self.config)
        self.pose_analyzer = PoseAnalyzer(self.config)
        self.db = Database(self.config)
        self.style_matcher = StyleMatcher(self.config)
        self.report_generator = ReportGenerator(self.config)

        logger.info("All Swing AI components initialized")

    async def start_session(self, user_id: str, session_name: str):
        """Start a practice session"""
        self.current_user = user_id
        self.session_name = session_name
        self.session_active = True

        logger.info(f"Starting session for {user_id} - {session_name}")

        if not self.camera_manager:
            self.camera_manager = CameraManager(self.config)

        # Start camera buffering
        await self.camera_manager.start_buffering()

        # Create DB session
        self.db.create_session(user_id, session_name)
        logger.info("Database session created")

        # Start monitoring swings
        asyncio.create_task(self._monitor_swings())

    async def stop_session(self):
        """Stop current session"""
        if not self.session_active:
            logger.warning("No active session to stop")
            return

        self.session_active = False
        await self.camera_manager.stop_buffering()
        logger.info("Session stopped successfully")

    async def _monitor_swings(self):
        """Monitor frames for swing detection"""
        logger.info("Monitoring swings...")

        while self.session_active:
            # Grab latest frames from camera manager
            frames = await self.camera_manager.get_latest_frames()
            if not frames:
                await asyncio.sleep(0.01)
                continue

            dtl_frame, face_frame = frames

            # Run pose analysis
            pose_data = self.pose_analyzer.analyze(dtl_frame, face_frame)

            # Check if swing detected
            if pose_data.get("swing_detected"):
                swing_data = self._analyze_swing(pose_data)
                self.db.store_swing(self.current_user, swing_data)

                # Trigger callback in GUI if set
                if hasattr(self, "on_swing_detected") and callable(self.on_swing_detected):
                    self.on_swing_detected(swing_data)

            await asyncio.sleep(self.config.get("processing", {}).get("min_shot_interval", 0.5))

    def _analyze_swing(self, pose_data):
        """Analyze pose and return swing stats"""
        # Example mock data; replace with real processing
        swing_data = {
            "shot_data": {
                "ClubSpeed": 85.0,
                "BallSpeed": 120.0
            },
            "overall_score": 75.0
        }
        return swing_data

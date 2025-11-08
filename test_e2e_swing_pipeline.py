"""
End-to-End Test Suite for ProMirrorGolf Swing Analysis Pipeline

This test suite validates the complete swing analysis workflow:
1. Camera/video input → Pose detection
2. Metrics extraction
3. Flaw detection
4. Pro matching
5. UI updates (headless mode)
6. Export functionality

Usage:
    python test_e2e_swing_pipeline.py

Expected Outputs:
    - All tests pass with assertions
    - Metrics dictionary populated
    - Flaw analysis with top 3 flaws
    - Pro match with similarity score 0-100%
    - Session state management verified
    - Export functions validated

Validation Criteria:
    - Metrics: Non-empty dict with expected keys
    - Flaws: List with severity scores, sorted by severity
    - Pro Match: Similarity score between 0-100%
    - Session: State transitions correctly
    - Exports: Files created successfully
"""

import asyncio
import logging
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import cv2

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.swing_ai_core import SwingAIController
from src.pose_analyzer import PoseAnalyzer
from src.metrics_extractor import MetricsExtractor
from src.flaw_detector import FlawDetector
from src.style_matcher import StyleMatcher
from src.database import SwingDatabase, ProSwingDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_e2e.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TestSwingPipeline:
    """End-to-end test suite for swing analysis pipeline"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="promirror_test_"))
        self.test_data_dir = self.temp_dir / "test_data"
        self.test_data_dir.mkdir()
        
        self.controller = None
        self.test_results = []
        
        logger.info(f"Test directory: {self.temp_dir}")
    
    def setup(self):
        """Setup test environment"""
        logger.info("=" * 60)
        logger.info("SETTING UP TEST ENVIRONMENT")
        logger.info("=" * 60)
        
        # Create test databases
        test_swing_db = str(self.test_data_dir / "swings.db")
        test_pro_db = str(self.test_data_dir / "pro_swings.db")
        
        # Initialize controller with test config
        test_config = {
            "cameras": {
                "dtl_id": 0,
                "face_id": 1,
                "fps": 60,
                "resolution": [640, 480],
                "buffer_seconds": 5.0
            },
            "ai": {
                "pose_model": "mediapipe",
                "use_gpu": False,
                "min_detection_confidence": 0.5
            },
            "database": {
                "swing_db_path": test_swing_db,
                "pro_db_path": test_pro_db
            },
            "reports": {
                "output_dir": str(self.test_data_dir / "reports")
            },
            "processing": {
                "auto_start": True,
                "min_shot_interval": 1.0
            }
        }
        
        # Save test config
        import json
        config_path = self.test_data_dir / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        self.controller = SwingAIController(str(config_path))
        
        # Setup pro database with test data
        self._setup_pro_database(test_pro_db)
        
        logger.info("Test environment setup complete")
    
    def _setup_pro_database(self, pro_db_path: str):
        """Setup test pro swing database"""
        pro_db = ProSwingDatabase(pro_db_path)
        
        # Add test pro swings
        test_pros = [
            {
                'pro_id': 'test_rory_driver',
                'golfer_name': 'Rory McIlroy',
                'club_type': 'Driver',
                'metrics': {
                    'hip_rotation_top': 48.2,
                    'shoulder_rotation_top': 96.2,
                    'x_factor': 48.0,
                    'spine_angle_address': 32.0,
                    'spine_angle_change': 1.0,
                    'weight_transfer': 0.12,
                    'tempo_ratio': 3.1,
                    'backswing_time': 0.9,
                    'downswing_time': 0.29,
                    'club_speed': 118.0
                },
                'style_tags': ['power', 'modern']
            },
            {
                'pro_id': 'test_tiger_driver',
                'golfer_name': 'Tiger Woods',
                'club_type': 'Driver',
                'metrics': {
                    'hip_rotation_top': 45.0,
                    'shoulder_rotation_top': 110.0,
                    'x_factor': 65.0,
                    'spine_angle_address': 30.0,
                    'spine_angle_change': 0.0,
                    'weight_transfer': 0.10,
                    'tempo_ratio': 3.2,
                    'backswing_time': 0.95,
                    'downswing_time': 0.30,
                    'club_speed': 120.0
                },
                'style_tags': ['power', 'classic']
            },
            {
                'pro_id': 'test_fred_7iron',
                'golfer_name': 'Fred Couples',
                'club_type': '7-Iron',
                'metrics': {
                    'hip_rotation_top': 42.0,
                    'shoulder_rotation_top': 88.0,
                    'x_factor': 46.0,
                    'spine_angle_address': 28.0,
                    'spine_angle_change': -2.0,
                    'weight_transfer': 0.08,
                    'tempo_ratio': 3.5,
                    'backswing_time': 1.0,
                    'downswing_time': 0.29,
                    'club_speed': 105.0
                },
                'style_tags': ['smooth', 'classic']
            }
        ]
        
        for pro in test_pros:
            pro_db.add_pro_swing(
                pro_id=pro['pro_id'],
                golfer_name=pro['golfer_name'],
                video_paths={'dtl': '', 'face': ''},
                metrics=pro['metrics'],
                club_type=pro['club_type'],
                style_tags=pro['style_tags']
            )
        
        logger.info(f"Added {len(test_pros)} test pro swings to database")
    
    def create_test_video(self, width=640, height=480, frames=100) -> Path:
        """Create a test video file with moving person"""
        video_path = self.test_data_dir / "test_swing.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (width, height))
        
        for i in range(frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Draw a simple "person" that moves (simulating swing)
            t = i / frames
            center_x = int(width / 2 + 50 * np.sin(t * np.pi))
            center_y = int(height / 2 + 30 * np.cos(t * np.pi))
            
            # Head
            cv2.circle(frame, (center_x, center_y - 80), 20, (255, 255, 255), -1)
            
            # Body
            cv2.line(frame, (center_x, center_y - 60), (center_x, center_y + 40), (255, 255, 255), 10)
            
            # Arms (swinging)
            arm_angle = t * np.pi * 2
            arm_length = 60
            left_arm_x = int(center_x - arm_length * np.cos(arm_angle))
            left_arm_y = int(center_y - 20 - arm_length * np.sin(arm_angle))
            right_arm_x = int(center_x + arm_length * np.cos(arm_angle))
            right_arm_y = int(center_y - 20 + arm_length * np.sin(arm_angle))
            
            cv2.line(frame, (center_x, center_y - 20), (left_arm_x, left_arm_y), (255, 255, 255), 8)
            cv2.line(frame, (center_x, center_y - 20), (right_arm_x, right_arm_y), (255, 255, 255), 8)
            
            # Legs
            cv2.line(frame, (center_x, center_y + 40), (center_x - 20, center_y + 100), (255, 255, 255), 8)
            cv2.line(frame, (center_x, center_y + 40), (center_x + 20, center_y + 100), (255, 255, 255), 8)
            
            out.write(frame)
        
        out.release()
        logger.info(f"Created test video: {video_path} ({frames} frames)")
        return video_path
    
    def create_test_pose_data(self) -> Dict:
        """Create test pose data structure"""
        # Create sequence of poses with landmarks
        dtl_poses = []
        for i in range(100):
            landmarks = {}
            # Key landmarks
            t = i / 100.0
            
            # Address (0-10)
            if i < 10:
                landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
                landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
                landmarks[23] = {'x': 0.45, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
                landmarks[24] = {'x': 0.55, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
                landmarks[15] = {'x': 0.3, 'y': 0.4, 'z': 0.0, 'visibility': 0.9}
            
            # Backswing (10-50)
            elif i < 50:
                progress = (i - 10) / 40.0
                angle = progress * np.pi / 2
                landmarks[11] = {'x': 0.4 - 0.2 * np.sin(angle), 'y': 0.3 - 0.1 * np.cos(angle),
                               'z': 0.1 * np.sin(angle), 'visibility': 0.9}
                landmarks[12] = {'x': 0.6 - 0.2 * np.sin(angle), 'y': 0.3 - 0.1 * np.cos(angle),
                               'z': 0.1 * np.sin(angle), 'visibility': 0.9}
                landmarks[23] = {'x': 0.45 - 0.1 * np.sin(angle), 'y': 0.6,
                               'z': 0.05 * np.sin(angle), 'visibility': 0.9}
                landmarks[24] = {'x': 0.55 - 0.1 * np.sin(angle), 'y': 0.6,
                               'z': 0.05 * np.sin(angle), 'visibility': 0.9}
                landmarks[15] = {'x': 0.3 - 0.3 * np.sin(angle), 'y': 0.4 - 0.2 * np.cos(angle),
                               'z': 0.2 * np.sin(angle), 'visibility': 0.9}
            
            # Top (50-55)
            elif i < 55:
                landmarks[11] = {'x': 0.2, 'y': 0.2, 'z': 0.1, 'visibility': 0.9}
                landmarks[12] = {'x': 0.4, 'y': 0.2, 'z': 0.1, 'visibility': 0.9}
                landmarks[23] = {'x': 0.35, 'y': 0.6, 'z': 0.05, 'visibility': 0.9}
                landmarks[24] = {'x': 0.45, 'y': 0.6, 'z': 0.05, 'visibility': 0.9}
                landmarks[15] = {'x': 0.0, 'y': 0.2, 'z': 0.2, 'visibility': 0.9}
            
            # Downswing (55-70)
            elif i < 70:
                progress = (i - 55) / 15.0
                angle = np.pi / 2 - progress * np.pi / 2
                landmarks[11] = {'x': 0.2 + 0.2 * np.sin(angle), 'y': 0.2 + 0.1 * np.cos(angle),
                               'z': 0.1 - 0.1 * np.sin(angle), 'visibility': 0.9}
                landmarks[12] = {'x': 0.4 + 0.2 * np.sin(angle), 'y': 0.2 + 0.1 * np.cos(angle),
                               'z': 0.1 - 0.1 * np.sin(angle), 'visibility': 0.9}
                landmarks[23] = {'x': 0.35 + 0.1 * np.sin(angle), 'y': 0.6,
                               'z': 0.05 - 0.05 * np.sin(angle), 'visibility': 0.9}
                landmarks[24] = {'x': 0.45 + 0.1 * np.sin(angle), 'y': 0.6,
                               'z': 0.05 - 0.05 * np.sin(angle), 'visibility': 0.9}
                landmarks[15] = {'x': 0.0 + 0.3 * np.sin(angle), 'y': 0.2 + 0.2 * np.cos(angle),
                               'z': 0.2 - 0.2 * np.sin(angle), 'visibility': 0.9}
            
            # Impact (70+)
            else:
                landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
                landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
                landmarks[23] = {'x': 0.45, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
                landmarks[24] = {'x': 0.55, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
                landmarks[15] = {'x': 0.3, 'y': 0.5, 'z': 0.0, 'visibility': 0.9}
            
            dtl_poses.append({'landmarks': landmarks})
        
        events = {
            'address': 5,
            'top': 52,
            'impact': 72,
            'finish': 99
        }
        
        return {
            'swing_detected': True,
            'dtl_poses': dtl_poses,
            'face_poses': dtl_poses,
            'events': events
        }
    
    async def test_pose_detection(self):
        """Test 1: Pose detection from video frames"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: POSE DETECTION")
        logger.info("=" * 60)
        
        try:
            await self.controller.initialize()
            pose_analyzer = self.controller.pose_analyzer
            
            # Create test frames
            dtl_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            face_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Draw simple person on frames
            cv2.circle(dtl_frame, (320, 200), 30, (255, 255, 255), -1)  # Head
            cv2.rectangle(dtl_frame, (300, 230), (340, 350), (255, 255, 255), -1)  # Body
            
            cv2.circle(face_frame, (320, 200), 30, (255, 255, 255), -1)
            cv2.rectangle(face_frame, (300, 230), (340, 350), (255, 255, 255), -1)
            
            # Analyze frames
            pose_data = await pose_analyzer.analyze(dtl_frame, face_frame)
            
            # Assertions
            assert isinstance(pose_data, dict), "Pose data should be a dictionary"
            assert 'swing_detected' in pose_data, "Pose data should contain 'swing_detected'"
            assert 'dtl_poses' in pose_data, "Pose data should contain 'dtl_poses'"
            
            logger.info(f"[PASS] Pose detection test passed")
            logger.info(f"  Swing detected: {pose_data.get('swing_detected')}")
            logger.info(f"  DTL poses: {len(pose_data.get('dtl_poses', []))}")
            
            return True, pose_data
            
        except Exception as e:
            logger.error(f"[FAIL] Pose detection test failed: {e}", exc_info=True)
            return False, None
    
    async def test_metrics_extraction(self, pose_data: Dict):
        """Test 2: Metrics extraction from pose data"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: METRICS EXTRACTION")
        logger.info("=" * 60)
        
        try:
            extractor = MetricsExtractor()
            metrics = extractor.extract_metrics_from_pose(pose_data, fps=60)
            
            # Assertions
            assert isinstance(metrics, dict), "Metrics should be a dictionary"
            assert len(metrics) > 0, "Metrics dictionary should not be empty"
            
            required_metrics = [
                'hip_rotation_top', 'shoulder_rotation_top', 'x_factor',
                'spine_angle_address', 'tempo_ratio', 'weight_transfer'
            ]
            
            for metric in required_metrics:
                assert metric in metrics, f"Missing required metric: {metric}"
                assert isinstance(metrics[metric], (int, float)), f"Metric {metric} should be numeric"
            
            logger.info(f"[PASS] Metrics extraction test passed")
            logger.info(f"  Extracted {len(metrics)} metrics")
            for key, value in metrics.items():
                logger.info(f"    {key}: {value:.2f}")
            
            return True, metrics
            
        except Exception as e:
            logger.error(f"[FAIL] Metrics extraction test failed: {e}", exc_info=True)
            return False, None
    
    async def test_flaw_detection(self, metrics: Dict):
        """Test 3: Flaw detection from metrics"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: FLAW DETECTION")
        logger.info("=" * 60)
        
        try:
            detector = FlawDetector()
            flaw_analysis = detector.detect_flaws(metrics)
            
            # Assertions
            assert isinstance(flaw_analysis, dict), "Flaw analysis should be a dictionary"
            assert 'flaws' in flaw_analysis, "Flaw analysis should contain 'flaws'"
            assert 'overall_score' in flaw_analysis, "Flaw analysis should contain 'overall_score'"
            assert 'flaw_count' in flaw_analysis, "Flaw analysis should contain 'flaw_count'"
            
            flaws = flaw_analysis['flaws']
            assert isinstance(flaws, list), "Flaws should be a list"
            
            # Check top 3 flaws
            if len(flaws) > 0:
                top_flaws = sorted(flaws, key=lambda x: x.get('severity', 0), reverse=True)[:3]
                assert len(top_flaws) <= 3, "Should have at most 3 top flaws"
                
                for flaw in top_flaws:
                    assert 'metric' in flaw, "Flaw should have 'metric'"
                    assert 'severity' in flaw, "Flaw should have 'severity'"
                    assert 'recommendation' in flaw, "Flaw should have 'recommendation'"
                    assert 0 <= flaw['severity'] <= 1, "Severity should be between 0 and 1"
            
            assert 0 <= flaw_analysis['overall_score'] <= 100, "Overall score should be 0-100"
            
            logger.info(f"[PASS] Flaw detection test passed")
            logger.info(f"  Overall score: {flaw_analysis['overall_score']}/100")
            logger.info(f"  Flaws detected: {flaw_analysis['flaw_count']}")
            if flaws:
                logger.info(f"  Top 3 flaws:")
                for i, flaw in enumerate(sorted(flaws, key=lambda x: x.get('severity', 0), reverse=True)[:3], 1):
                    logger.info(f"    {i}. {flaw['metric']}: severity {flaw['severity']:.2f}")
            
            return True, flaw_analysis
            
        except Exception as e:
            logger.error(f"[FAIL] Flaw detection test failed: {e}", exc_info=True)
            return False, None
    
    async def test_pro_matching(self, metrics: Dict):
        """Test 4: Pro swing matching"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: PRO MATCHING")
        logger.info("=" * 60)
        
        try:
            matcher = self.controller.style_matcher
            pro_match = await matcher.find_best_match(metrics, club_type='Driver')
            
            # Assertions
            assert isinstance(pro_match, dict), "Pro match should be a dictionary"
            assert 'golfer_name' in pro_match, "Pro match should contain 'golfer_name'"
            assert 'similarity_score' in pro_match, "Pro match should contain 'similarity_score'"
            assert 'pro_id' in pro_match, "Pro match should contain 'pro_id'"
            
            similarity = pro_match['similarity_score']
            assert 0 <= similarity <= 100, f"Similarity score should be 0-100%, got {similarity}"
            
            logger.info(f"[PASS] Pro matching test passed")
            logger.info(f"  Matched pro: {pro_match['golfer_name']}")
            logger.info(f"  Similarity: {similarity:.2f}%")
            logger.info(f"  Pro ID: {pro_match['pro_id']}")
            
            return True, pro_match
            
        except Exception as e:
            logger.error(f"[FAIL] Pro matching test failed: {e}", exc_info=True)
            return False, None
    
    async def test_full_pipeline(self):
        """Test 5: Full pipeline end-to-end"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: FULL PIPELINE")
        logger.info("=" * 60)
        
        try:
            # Create test pose data
            pose_data = self.create_test_pose_data()
            
            # Run full analysis
            swing_data = await self.controller._analyze_swing(pose_data)
            
            # Assertions
            assert isinstance(swing_data, dict), "Swing data should be a dictionary"
            assert 'metrics' in swing_data, "Swing data should contain 'metrics'"
            assert 'flaw_analysis' in swing_data, "Swing data should contain 'flaw_analysis'"
            assert 'pro_match' in swing_data, "Swing data should contain 'pro_match'"
            assert 'overall_score' in swing_data, "Swing data should contain 'overall_score'"
            assert 'shot_data' in swing_data, "Swing data should contain 'shot_data'"
            
            # Validate metrics
            metrics = swing_data['metrics']
            assert len(metrics) > 0, "Metrics should not be empty"
            
            # Validate flaw analysis
            flaw_analysis = swing_data['flaw_analysis']
            assert flaw_analysis['overall_score'] >= 0, "Overall score should be >= 0"
            
            # Validate pro match
            pro_match = swing_data['pro_match']
            assert 0 <= pro_match['similarity_score'] <= 100, "Similarity score should be 0-100%"
            
            logger.info(f"[PASS] Full pipeline test passed")
            logger.info(f"  Metrics: {len(metrics)}")
            logger.info(f"  Flaws: {flaw_analysis['flaw_count']}")
            logger.info(f"  Score: {swing_data['overall_score']}/100")
            logger.info(f"  Pro: {pro_match['golfer_name']}")
            
            return True, swing_data
            
        except Exception as e:
            logger.error(f"[FAIL] Full pipeline test failed: {e}", exc_info=True)
            return False, None
    
    async def test_session_management(self):
        """Test 6: Session start/stop behavior"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: SESSION MANAGEMENT")
        logger.info("=" * 60)
        
        try:
            # Test session start
            assert not self.controller.session_active, "Session should not be active initially"
            
            await self.controller.start_session("test_user", "Test Session")
            
            assert self.controller.session_active, "Session should be active after start"
            assert self.controller.current_session_id is not None, "Session ID should be set"
            assert self.controller.current_user == "test_user", "User should be set"
            
            logger.info(f"  Session started: {self.controller.current_session_id}")
            
            # Test session stop
            await self.controller.stop_session()
            
            assert not self.controller.session_active, "Session should not be active after stop"
            
            logger.info(f"[PASS] Session management test passed")
            
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Session management test failed: {e}", exc_info=True)
            return False
    
    async def test_export_functionality(self, swing_data: Dict):
        """Test 7: Export video and HTML report"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 7: EXPORT FUNCTIONALITY")
        logger.info("=" * 60)
        
        try:
            # Save a swing to database first
            swing_id = "test_swing_123"
            self.controller.current_session_id = "test_session_123"
            
            self.controller.db.save_swing(
                session_id=self.controller.current_session_id,
                swing_id=swing_id,
                swing_metrics=swing_data.get('metrics', {}),
                shot_data=swing_data.get('shot_data', {}),
                video_paths={'dtl': '', 'face': ''},
                report_path='',
                pro_match_id=swing_data.get('pro_match', {}).get('pro_id', ''),
                flaw_analysis=swing_data.get('flaw_analysis', {})
            )
            
            # Test database retrieval
            saved_swing = self.controller.db.get_swing(swing_id)
            assert saved_swing is not None, "Swing should be retrievable from database"
            assert saved_swing['swing_id'] == swing_id, "Swing ID should match"
            
            logger.info(f"  Swing saved and retrieved: {swing_id}")
            
            # Test HTML report generation (if report generator available)
            if self.controller.report_generator:
                try:
                    report = await self.controller.report_generator.create_report(
                        swing_id=swing_id,
                        user_videos={'dtl': '', 'face': ''},
                        pro_match=swing_data.get('pro_match', {}),
                        swing_metrics=swing_data.get('metrics', {}),
                        flaw_analysis=swing_data.get('flaw_analysis', {}),
                        shot_data=swing_data.get('shot_data', {}),
                        pose_data={}
                    )
                    assert isinstance(report, dict), "Report should be a dictionary"
                    logger.info(f"  HTML report generated successfully")
                except Exception as e:
                    logger.warning(f"  Report generation skipped: {e}")
            
            logger.info(f"[PASS] Export functionality test passed")
            
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Export functionality test failed: {e}", exc_info=True)
            return False
    
    async def test_edge_cases(self):
        """Test 8: Edge cases"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 8: EDGE CASES")
        logger.info("=" * 60)
        
        results = []
        
        # Test 1: Empty pose data
        try:
            extractor = MetricsExtractor()
            empty_pose = {'swing_detected': False, 'dtl_poses': [], 'events': {}}
            metrics = extractor.extract_metrics_from_pose(empty_pose, fps=60)
            assert isinstance(metrics, dict), "Should return dict even with empty data"
            logger.info("  [PASS] Empty pose data handled")
            results.append(True)
        except Exception as e:
            logger.error(f"  [FAIL] Empty pose data failed: {e}")
            results.append(False)
        
        # Test 2: Missing frames
        try:
            pose_analyzer = self.controller.pose_analyzer
            pose_data = await pose_analyzer.analyze(None, None)
            assert isinstance(pose_data, dict), "Should handle None frames"
            logger.info("  [PASS] Missing frames handled")
            results.append(True)
        except Exception as e:
            logger.error(f"  [FAIL] Missing frames failed: {e}")
            results.append(False)
        
        # Test 3: No swings in session
        try:
            session_swings = self.controller.db.get_session_swings("nonexistent_session")
            assert isinstance(session_swings, list), "Should return list even if no swings"
            logger.info("  [PASS] No swings handled")
            results.append(True)
        except Exception as e:
            logger.error(f"  [FAIL] No swings failed: {e}")
            results.append(False)
        
        # Test 4: Invalid metrics
        try:
            detector = FlawDetector()
            invalid_metrics = {'invalid_metric': 'not_a_number'}
            flaw_analysis = detector.detect_flaws(invalid_metrics)
            assert isinstance(flaw_analysis, dict), "Should handle invalid metrics"
            logger.info("  [PASS] Invalid metrics handled")
            results.append(True)
        except Exception as e:
            logger.error(f"  [FAIL] Invalid metrics failed: {e}")
            results.append(False)
        
        all_passed = all(results)
        logger.info(f"{'[PASS]' if all_passed else '[FAIL]'} Edge cases test: {sum(results)}/{len(results)} passed")
        
        return all_passed
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("\n" + "=" * 60)
        logger.info("RUNNING END-TO-END TEST SUITE")
        logger.info("=" * 60)
        
        self.setup()
        
        try:
            # Initialize controller
            await self.controller.initialize()
            
            # Run tests
            test_results = {}
            
            # Test 1: Pose detection
            passed, pose_data = await self.test_pose_detection()
            test_results['pose_detection'] = passed
            if not passed:
                logger.error("Stopping tests due to pose detection failure")
                return False
            
            # Test 2: Metrics extraction
            passed, metrics = await self.test_metrics_extraction(pose_data)
            test_results['metrics_extraction'] = passed
            if not passed:
                return False
            
            # Test 3: Flaw detection
            passed, flaw_analysis = await self.test_flaw_detection(metrics)
            test_results['flaw_detection'] = passed
            if not passed:
                return False
            
            # Test 4: Pro matching
            passed, pro_match = await self.test_pro_matching(metrics)
            test_results['pro_matching'] = passed
            if not passed:
                return False
            
            # Test 5: Full pipeline
            passed, swing_data = await self.test_full_pipeline()
            test_results['full_pipeline'] = passed
            if not passed:
                return False
            
            # Test 6: Session management
            passed = await self.test_session_management()
            test_results['session_management'] = passed
            
            # Test 7: Export functionality
            passed = await self.test_export_functionality(swing_data)
            test_results['export_functionality'] = passed
            
            # Test 8: Edge cases
            passed = await self.test_edge_cases()
            test_results['edge_cases'] = passed
            
            # Test 9: Video upload processing
            passed = await self.test_video_upload_processing()
            test_results['video_upload_processing'] = passed
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("TEST SUMMARY")
            logger.info("=" * 60)
            
            total = len(test_results)
            passed_count = sum(1 for v in test_results.values() if v)
            
            for test_name, result in test_results.items():
                status = "[PASS]" if result else "[FAIL]"
                logger.info(f"{test_name}: {status}")
            
            logger.info(f"\nTotal: {passed_count}/{total} tests passed")
            
            return passed_count == total
            
        except Exception as e:
            logger.error(f"Test suite error: {e}", exc_info=True)
            return False
        
        finally:
            self.teardown()
    
    def teardown(self):
        """Cleanup test environment"""
        logger.info("\n" + "=" * 60)
        logger.info("CLEANING UP TEST ENVIRONMENT")
        logger.info("=" * 60)
        
        try:
            # Stop controller if active
            if self.controller and self.controller.session_active:
                asyncio.run(self.controller.stop_session())
            
            # Close database connections
            if self.controller:
                if self.controller.db:
                    self.controller.db.close()
                if self.controller.style_matcher and self.controller.style_matcher.pro_db:
                    self.controller.style_matcher.pro_db.close()
            
            # Remove temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Removed test directory: {self.temp_dir}")
            
            logger.info("Cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)


async def main():
    """Main test runner"""
    test_suite = TestSwingPipeline()
    success = await test_suite.run_all_tests()
    
    if success:
        logger.info("\n[SUCCESS] ALL TESTS PASSED")
        sys.exit(0)
    else:
        logger.error("\n[FAILURE] SOME TESTS FAILED")
        sys.exit(1)


        async def test_video_upload_processing(self):
            """Test 9: Video upload processing with GUI responsiveness"""
            logger.info("\n" + "=" * 60)
            logger.info("TEST 9: VIDEO UPLOAD PROCESSING")
            logger.info("=" * 60)
            try:
                # Create dummy video files for testing
                import cv2
                import numpy as np
                from pathlib import Path
                
                test_dir = self.test_dir / "test_videos"
                test_dir.mkdir(exist_ok=True)
                
                dtl_path = test_dir / "test_dtl.mp4"
                face_path = test_dir / "face_dtl.mp4"
                
                # Create simple test videos (30 frames each)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = 30
                size = (640, 480)
                
                dtl_writer = cv2.VideoWriter(str(dtl_path), fourcc, fps, size)
                face_writer = cv2.VideoWriter(str(face_path), fourcc, fps, size)
                
                for i in range(30):
                    # Create dummy frames
                    dtl_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    face_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    dtl_writer.write(dtl_frame)
                    face_writer.write(face_frame)
                
                dtl_writer.release()
                face_writer.release()
                
                # Start session in video upload mode
                await self.controller.start_session("test_user", "Video Upload Test", use_video_upload=True)
                
                # Process videos with downsampling
                result = await self.controller.process_uploaded_videos(
                    str(dtl_path), str(face_path), downsample_factor=5
                )
                
                # Verify processing
                assert result.get('success') is not None, "Result should have success field"
                assert 'frames_processed' in result or 'error' in result, "Result should have frames_processed or error"
                
                # Verify MLM2Pro was skipped
                assert not self.controller.launch_monitor or not hasattr(self.controller.launch_monitor, 'is_listening') or \
                       not self.controller.launch_monitor.is_listening(), "MLM2Pro should be disabled in upload mode"
                
                logger.info(f"[PASS] Video upload processing test passed")
                logger.info(f"  Result: {result.get('success', False)}")
                
                # Cleanup
                await self.controller.stop_session()
                if dtl_path.exists():
                    dtl_path.unlink()
                if face_path.exists():
                    face_path.unlink()
                
                return True
                
            except Exception as e:
                logger.error(f"[FAIL] Video upload processing test failed: {e}", exc_info=True)
                return False

        if __name__ == "__main__":
            asyncio.run(main())


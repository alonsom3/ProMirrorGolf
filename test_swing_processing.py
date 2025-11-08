"""
End-to-end test for swing data processing pipeline
Tests metrics extraction, flaw detection, pro matching, and data flow
"""

import asyncio
import logging
import sys
from pathlib import Path
import json

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.swing_ai_core import SwingAIController
from src.metrics_extractor import MetricsExtractor
from src.flaw_detector import FlawDetector
from src.style_matcher import StyleMatcher
from src.database import ProSwingDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_pose_data():
    """Create sample pose data for testing"""
    import numpy as np
    
    # Create sample pose landmarks (simplified)
    def create_pose_frame(frame_num):
        """Create a pose frame with landmarks"""
        landmarks = {}
        
        # Key landmarks (MediaPipe indices)
        # 11=left_shoulder, 12=right_shoulder
        # 23=left_hip, 24=right_hip
        # 15=left_wrist, 16=right_wrist
        
        # Simulate swing motion
        t = frame_num / 60.0  # Time in seconds
        
        # Address position (frame 0-10)
        if frame_num < 10:
            landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
            landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
            landmarks[23] = {'x': 0.45, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
            landmarks[24] = {'x': 0.55, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
            landmarks[15] = {'x': 0.3, 'y': 0.4, 'z': 0.0, 'visibility': 0.9}
            landmarks[16] = {'x': 0.7, 'y': 0.4, 'z': 0.0, 'visibility': 0.9}
        
        # Backswing (frame 10-50)
        elif frame_num < 50:
            progress = (frame_num - 10) / 40.0
            angle = progress * np.pi / 2  # 90 degree rotation
            
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
            landmarks[16] = {'x': 0.7 - 0.3 * np.sin(angle), 'y': 0.4 - 0.2 * np.cos(angle),
                           'z': 0.2 * np.sin(angle), 'visibility': 0.9}
        
        # Top of backswing (frame 50-55)
        elif frame_num < 55:
            landmarks[11] = {'x': 0.2, 'y': 0.2, 'z': 0.1, 'visibility': 0.9}
            landmarks[12] = {'x': 0.4, 'y': 0.2, 'z': 0.1, 'visibility': 0.9}
            landmarks[23] = {'x': 0.35, 'y': 0.6, 'z': 0.05, 'visibility': 0.9}
            landmarks[24] = {'x': 0.45, 'y': 0.6, 'z': 0.05, 'visibility': 0.9}
            landmarks[15] = {'x': 0.0, 'y': 0.2, 'z': 0.2, 'visibility': 0.9}
            landmarks[16] = {'x': 0.4, 'y': 0.2, 'z': 0.2, 'visibility': 0.9}
        
        # Downswing (frame 55-70)
        elif frame_num < 70:
            progress = (frame_num - 55) / 15.0
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
            landmarks[16] = {'x': 0.4 + 0.3 * np.sin(angle), 'y': 0.2 + 0.2 * np.cos(angle),
                           'z': 0.2 - 0.2 * np.sin(angle), 'visibility': 0.9}
        
        # Impact (frame 70-75)
        else:
            landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
            landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0.0, 'visibility': 0.9}
            landmarks[23] = {'x': 0.45, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
            landmarks[24] = {'x': 0.55, 'y': 0.6, 'z': 0.0, 'visibility': 0.9}
            landmarks[15] = {'x': 0.3, 'y': 0.5, 'z': 0.0, 'visibility': 0.9}
            landmarks[16] = {'x': 0.7, 'y': 0.5, 'z': 0.0, 'visibility': 0.9}
        
        return {'landmarks': landmarks}
    
    # Create sequence of poses
    dtl_poses = [create_pose_frame(i) for i in range(100)]
    
    # Define events
    events = {
        'address': 5,
        'top': 52,
        'impact': 72,
        'finish': 99
    }
    
    return {
        'swing_detected': True,
        'dtl_poses': dtl_poses,
        'face_poses': dtl_poses,  # Simplified - same as DTL
        'events': events
    }


async def setup_pro_database():
    """Set up sample pro swing database"""
    pro_db_path = "./data/pro_swings.db"
    Path("./data").mkdir(exist_ok=True)
    
    pro_db = ProSwingDatabase(pro_db_path)
    
    # Add sample pro swings
    sample_pros = [
        {
            'pro_id': 'rory_mcilroy_driver',
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
            'style_tags': ['power', 'modern', 'athletic']
        },
        {
            'pro_id': 'tiger_woods_driver',
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
            'style_tags': ['power', 'classic', 'high_separation']
        },
        {
            'pro_id': 'fred_couples_driver',
            'golfer_name': 'Fred Couples',
            'club_type': 'Driver',
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
            'style_tags': ['smooth', 'classic', 'balanced_tempo']
        }
    ]
    
    for pro in sample_pros:
        pro_db.add_pro_swing(
            pro_id=pro['pro_id'],
            golfer_name=pro['golfer_name'],
            video_paths={'dtl': '', 'face': ''},
            metrics=pro['metrics'],
            club_type=pro['club_type'],
            style_tags=pro['style_tags']
        )
        logger.info(f"Added pro swing: {pro['golfer_name']}")
    
    return pro_db_path


async def test_metrics_extraction():
    """Test 1: Metrics extraction"""
    logger.info("\n=== TEST 1: Metrics Extraction ===")
    
    pose_data = create_sample_pose_data()
    extractor = MetricsExtractor()
    
    metrics = extractor.extract_metrics_from_pose(pose_data, fps=60)
    
    logger.info(f"Extracted metrics:")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value:.2f}")
    
    # Verify key metrics are present
    required_metrics = [
        'hip_rotation_top', 'shoulder_rotation_top', 'x_factor',
        'spine_angle_address', 'spine_angle_change', 'tempo_ratio',
        'backswing_time', 'downswing_time', 'weight_transfer'
    ]
    
    missing = [m for m in required_metrics if m not in metrics]
    if missing:
        logger.error(f"Missing metrics: {missing}")
        return False
    
    logger.info("✓ Metrics extraction test passed")
    return True, metrics


async def test_flaw_detection(metrics):
    """Test 2: Flaw detection"""
    logger.info("\n=== TEST 2: Flaw Detection ===")
    
    detector = FlawDetector()
    flaw_analysis = detector.detect_flaws(metrics)
    
    logger.info(f"Overall Score: {flaw_analysis['overall_score']}/100")
    logger.info(f"Flaws detected: {flaw_analysis['flaw_count']}")
    
    if flaw_analysis['flaws']:
        logger.info("Top flaws:")
        for flaw in flaw_analysis['flaws'][:3]:
            logger.info(f"  - {flaw['metric']}: {flaw['value']:.2f} "
                       f"(ideal: {flaw['ideal_min']:.2f}-{flaw['ideal_max']:.2f})")
            logger.info(f"    Recommendation: {flaw['recommendation'][:80]}...")
    
    # Verify structure
    required_keys = ['flaws', 'overall_score', 'flaw_count']
    missing = [k for k in required_keys if k not in flaw_analysis]
    if missing:
        logger.error(f"Missing keys in flaw analysis: {missing}")
        return False
    
    logger.info("✓ Flaw detection test passed")
    return True, flaw_analysis


async def test_pro_matching(metrics):
    """Test 3: Pro matching"""
    logger.info("\n=== TEST 3: Pro Matching ===")
    
    # Setup pro database
    pro_db_path = await setup_pro_database()
    matcher = StyleMatcher(pro_db_path)
    
    pro_match = await matcher.find_best_match(metrics, club_type='Driver')
    
    logger.info(f"Best match: {pro_match['golfer_name']}")
    logger.info(f"Similarity score: {pro_match['similarity_score']:.2f}")
    logger.info(f"Pro ID: {pro_match['pro_id']}")
    
    if pro_match['similarity_score'] < 0:
        logger.error("Invalid similarity score")
        return False
    
    logger.info("✓ Pro matching test passed")
    return True, pro_match


async def test_full_pipeline():
    """Test 4: Full pipeline end-to-end"""
    logger.info("\n=== TEST 4: Full Pipeline ===")
    
    # Initialize controller
    controller = SwingAIController("config.json")
    await controller.initialize()
    
    # Create sample pose data
    pose_data = create_sample_pose_data()
    
    # Run full analysis
    swing_data = await controller._analyze_swing(pose_data)
    
    logger.info(f"Swing ID: {swing_data.get('swing_id', 'N/A')}")
    logger.info(f"Overall Score: {swing_data['overall_score']}/100")
    logger.info(f"Metrics extracted: {len(swing_data['metrics'])}")
    logger.info(f"Flaws detected: {swing_data['flaw_analysis']['flaw_count']}")
    logger.info(f"Pro match: {swing_data['pro_match']['golfer_name']}")
    logger.info(f"Shot data: Club Speed={swing_data['shot_data']['ClubSpeed']:.1f} mph")
    
    # Verify all required fields
    required_fields = ['metrics', 'shot_data', 'flaw_analysis', 'pro_match', 'overall_score']
    missing = [f for f in required_fields if f not in swing_data]
    if missing:
        logger.error(f"Missing fields in swing_data: {missing}")
        return False
    
    logger.info("✓ Full pipeline test passed")
    return True


async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("SWING DATA PROCESSING VERIFICATION")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: Metrics extraction
    success, metrics = await test_metrics_extraction()
    results['metrics_extraction'] = success
    
    if not success:
        logger.error("Metrics extraction failed, stopping tests")
        return
    
    # Test 2: Flaw detection
    success, flaw_analysis = await test_flaw_detection(metrics)
    results['flaw_detection'] = success
    
    # Test 3: Pro matching
    success, pro_match = await test_pro_matching(metrics)
    results['pro_matching'] = success
    
    # Test 4: Full pipeline
    success = await test_full_pipeline()
    results['full_pipeline'] = success
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ All tests passed!")
    else:
        logger.error("\n✗ Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())


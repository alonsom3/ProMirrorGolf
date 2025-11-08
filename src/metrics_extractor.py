"""
Swing Metrics Extractor
Extracts biomechanical metrics from pose detection data
"""

import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class MetricsExtractor:
    """
    Extracts swing metrics from pose landmark data
    """
    
    @staticmethod
    def extract_metrics_from_pose(pose_data: Dict, fps: int = 60) -> Dict:
        """
        Extract swing metrics from pose detection results
        
        Args:
            pose_data: Dictionary with pose landmarks and events
            fps: Frames per second for time calculations
            
        Returns:
            Dictionary of calculated metrics
        """
        if not pose_data or 'dtl_poses' not in pose_data:
            logger.warning("No pose data available, returning default metrics")
            return MetricsExtractor._get_default_metrics()
        
        dtl_poses = pose_data.get('dtl_poses', [])
        events = pose_data.get('events', {})
        
        if not dtl_poses or not events:
            return MetricsExtractor._get_default_metrics()
        
        # Get key poses
        address_idx = events.get('address', 0)
        top_idx = events.get('top', len(dtl_poses) // 3)
        impact_idx = events.get('impact', len(dtl_poses) // 2)
        
        address_pose = dtl_poses[address_idx] if address_idx < len(dtl_poses) else dtl_poses[0]
        top_pose = dtl_poses[top_idx] if top_idx < len(dtl_poses) else dtl_poses[len(dtl_poses)//3]
        impact_pose = dtl_poses[impact_idx] if impact_idx < len(dtl_poses) else dtl_poses[len(dtl_poses)//2]
        
        metrics = {}
        
        # Hip rotation (from address to top)
        metrics['hip_rotation_top'] = MetricsExtractor._calc_hip_rotation(
            address_pose, top_pose
        )
        
        # Shoulder rotation (from address to top)
        metrics['shoulder_rotation_top'] = MetricsExtractor._calc_shoulder_rotation(
            address_pose, top_pose
        )
        
        # X-Factor (shoulder-hip separation at top)
        metrics['x_factor'] = (
            metrics['shoulder_rotation_top'] - metrics['hip_rotation_top']
        )
        
        # Spine angles
        metrics['spine_angle_address'] = MetricsExtractor._calc_spine_angle(address_pose)
        metrics['spine_angle_impact'] = MetricsExtractor._calc_spine_angle(impact_pose)
        metrics['spine_angle_change'] = (
            metrics['spine_angle_impact'] - metrics['spine_angle_address']
        )
        
        # Tempo calculations
        backswing_frames = top_idx - address_idx
        downswing_frames = impact_idx - top_idx
        
        metrics['backswing_time'] = backswing_frames / fps if fps > 0 else 0
        metrics['downswing_time'] = downswing_frames / fps if fps > 0 else 0
        metrics['tempo_ratio'] = (
            backswing_frames / downswing_frames if downswing_frames > 0 else 0
        )
        
        # Weight transfer (simplified - would need more sophisticated calculation)
        metrics['weight_transfer'] = MetricsExtractor._calc_weight_transfer(
            address_pose, impact_pose
        )
        
        logger.info(f"Extracted metrics: {metrics}")
        return metrics
    
    @staticmethod
    def _calc_hip_rotation(pose1: Dict, pose2: Dict) -> float:
        """Calculate hip rotation between two poses"""
        if not pose1 or not pose2:
            return 0.0
        if not pose1.get('landmarks') or not pose2.get('landmarks'):
            return 0.0
        
        landmarks1 = pose1['landmarks']
        landmarks2 = pose2['landmarks']
        
        # MediaPipe landmark indices: 23=left_hip, 24=right_hip
        def get_angle(landmarks):
            if 23 not in landmarks or 24 not in landmarks:
                return 0.0
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            dx = right_hip['x'] - left_hip['x']
            dz = right_hip.get('z', 0) - left_hip.get('z', 0)
            if abs(dx) < 0.001 and abs(dz) < 0.001:
                return 0.0
            return np.degrees(np.arctan2(dz, dx))
        
        angle1 = get_angle(landmarks1)
        angle2 = get_angle(landmarks2)
        rotation = angle2 - angle1
        
        # Normalize to -180 to 180
        while rotation > 180:
            rotation -= 360
        while rotation < -180:
            rotation += 360
        
        return abs(rotation)
    
    @staticmethod
    def _calc_shoulder_rotation(pose1: Dict, pose2: Dict) -> float:
        """Calculate shoulder rotation between two poses"""
        if not pose1 or not pose2:
            return 0.0
        if not pose1.get('landmarks') or not pose2.get('landmarks'):
            return 0.0
        
        landmarks1 = pose1['landmarks']
        landmarks2 = pose2['landmarks']
        
        # MediaPipe landmark indices: 11=left_shoulder, 12=right_shoulder
        def get_angle(landmarks):
            if 11 not in landmarks or 12 not in landmarks:
                return 0.0
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            dx = right_shoulder['x'] - left_shoulder['x']
            dz = right_shoulder.get('z', 0) - left_shoulder.get('z', 0)
            if abs(dx) < 0.001 and abs(dz) < 0.001:
                return 0.0
            return np.degrees(np.arctan2(dz, dx))
        
        angle1 = get_angle(landmarks1)
        angle2 = get_angle(landmarks2)
        rotation = angle2 - angle1
        
        # Normalize to -180 to 180
        while rotation > 180:
            rotation -= 360
        while rotation < -180:
            rotation += 360
        
        return abs(rotation)
    
    @staticmethod
    def _calc_spine_angle(pose: Dict) -> float:
        """Calculate spine angle (forward tilt) from a pose"""
        if not pose or not pose.get('landmarks'):
            return 0.0
        
        landmarks = pose['landmarks']
        
        # Get hip and shoulder midpoints
        if 23 not in landmarks or 24 not in landmarks or 11 not in landmarks or 12 not in landmarks:
            return 0.0
        
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        hip_mid_y = (left_hip['y'] + right_hip['y']) / 2
        shoulder_mid_y = (left_shoulder['y'] + right_shoulder['y']) / 2
        shoulder_mid_x = (left_shoulder['x'] + right_shoulder['x']) / 2
        hip_mid_x = (left_hip['x'] + right_hip['x']) / 2
        
        dy = shoulder_mid_y - hip_mid_y
        dx = shoulder_mid_x - hip_mid_x
        
        # Calculate angle from vertical (90 degrees = straight up)
        # For golf, we want forward tilt, so we calculate deviation from vertical
        if abs(dy) < 0.001:  # Avoid division by zero
            return 0.0
        
        angle = np.degrees(np.arctan2(abs(dx), abs(dy)))
        # Normalize: 0-90 degrees, where 0 is vertical, 90 is horizontal
        return min(90.0, max(0.0, angle))
    
    @staticmethod
    def _calc_weight_transfer(pose1: Dict, pose2: Dict) -> float:
        """Calculate weight transfer (simplified - uses hip position shift)"""
        if not pose1.get('landmarks') or not pose2.get('landmarks'):
            return 0.0
        
        landmarks1 = pose1['landmarks']
        landmarks2 = pose2['landmarks']
        
        if 23 not in landmarks1 or 24 not in landmarks1 or 23 not in landmarks2 or 24 not in landmarks2:
            return 0.0
        
        # Get hip center positions
        hip1_x = (landmarks1[23]['x'] + landmarks1[24]['x']) / 2
        hip2_x = (landmarks2[23]['x'] + landmarks2[24]['x']) / 2
        
        # Calculate shift (normalized)
        shift = abs(hip2_x - hip1_x)
        return min(shift, 0.2)  # Cap at 0.2
    
    @staticmethod
    def _get_default_metrics() -> Dict:
        """Return default metrics when pose data is unavailable"""
        return {
            'hip_rotation_top': 42.0,
            'shoulder_rotation_top': 89.0,
            'x_factor': 47.0,
            'spine_angle_address': 31.0,
            'spine_angle_impact': 31.0,
            'spine_angle_change': 0.0,
            'backswing_time': 0.9,
            'downswing_time': 0.3,
            'tempo_ratio': 3.0,
            'weight_transfer': 0.08
        }


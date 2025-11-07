"""
Extract Swing Metrics from Pose Data
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MetricsExtractor:
    @staticmethod
    def extract_metrics(pose_data):
        events = pose_data['events']
        dtl_poses = pose_data['dtl_poses']
        
        address_pose = dtl_poses[events['address']]
        top_pose = dtl_poses[events['top']]
        impact_pose = dtl_poses[events['impact']]
        
        metrics = {}
        
        metrics['hip_rotation_top'] = MetricsExtractor._calc_hip_rotation(
            address_pose, top_pose
        )
        
        metrics['shoulder_rotation_top'] = MetricsExtractor._calc_shoulder_rotation(
            address_pose, top_pose
        )
        
        metrics['x_factor'] = (
            metrics['shoulder_rotation_top'] - metrics['hip_rotation_top']
        )
        
        metrics['spine_angle_address'] = MetricsExtractor._calc_spine_angle(address_pose)
        metrics['spine_angle_impact'] = MetricsExtractor._calc_spine_angle(impact_pose)
        metrics['spine_angle_change'] = (
            metrics['spine_angle_impact'] - metrics['spine_angle_address']
        )
        
        fps = 60
        backswing_frames = events['top'] - events['address']
        downswing_frames = events['impact'] - events['top']
        
        metrics['backswing_time'] = backswing_frames / fps
        metrics['downswing_time'] = downswing_frames / fps
        metrics['tempo_ratio'] = (
            backswing_frames / downswing_frames if downswing_frames > 0 else 0
        )
        
        logger.info(f"Extracted metrics: {metrics}")
        return metrics
    
    @staticmethod
    def _calc_hip_rotation(pose1, pose2):
        if not pose1['landmarks'] or not pose2['landmarks']:
            return 0.0
        
        def get_angle(pose):
            left_hip = pose['landmarks'][23]
            right_hip = pose['landmarks'][24]
            dx = right_hip['x'] - left_hip['x']
            dz = right_hip['z'] - left_hip['z']
            return np.degrees(np.arctan2(dz, dx))
        
        return get_angle(pose2) - get_angle(pose1)
    
    @staticmethod
    def _calc_shoulder_rotation(pose1, pose2):
        if not pose1['landmarks'] or not pose2['landmarks']:
            return 0.0
        
        def get_angle(pose):
            left_shoulder = pose['landmarks'][11]
            right_shoulder = pose['landmarks'][12]
            dx = right_shoulder['x'] - left_shoulder['x']
            dz = right_shoulder['z'] - left_shoulder['z']
            return np.degrees(np.arctan2(dz, dx))
        
        return get_angle(pose2) - get_angle(pose1)
    
    @staticmethod
    def _calc_spine_angle(pose):
        if not pose['landmarks']:
            return 0.0
        
        left_hip = pose['landmarks'][23]
        right_hip = pose['landmarks'][24]
        left_shoulder = pose['landmarks'][11]
        right_shoulder = pose['landmarks'][12]
        
        hip_mid_y = (left_hip['y'] + right_hip['y']) / 2
        shoulder_mid_y = (left_shoulder['y'] + right_shoulder['y']) / 2
        shoulder_mid_x = (left_shoulder['x'] + right_shoulder['x']) / 2
        hip_mid_x = (left_hip['x'] + right_hip['x']) / 2
        
        dy = shoulder_mid_y - hip_mid_y
        dx = shoulder_mid_x - hip_mid_x
        
        return np.degrees(np.arctan2(dx, dy))
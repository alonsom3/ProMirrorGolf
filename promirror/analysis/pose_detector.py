"""
AI Pose Detection using MediaPipe
"""
import mediapipe as mp
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose_dtl = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5
        )
        self.pose_face = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5
        )
        logger.info("Pose detector initialized")
    
    def analyze_swing(self, dtl_frames, face_frames):
        dtl_poses = self._process_frames(dtl_frames, self.pose_dtl)
        face_poses = self._process_frames(face_frames, self.pose_face)
        
        events = self._detect_events(dtl_poses)
        
        return {
            'dtl_poses': dtl_poses,
            'face_poses': face_poses,
            'events': events
        }
    
    def _process_frames(self, frames, pose_model):
        poses = []
        
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_model.process(rgb)
            
            if results.pose_landmarks:
                landmarks = {}
                for idx, lm in enumerate(results.pose_landmarks.landmark):
                    landmarks[idx] = {
                        'x': lm.x,
                        'y': lm.y,
                        'z': lm.z,
                        'visibility': lm.visibility
                    }
                poses.append({'landmarks': landmarks})
            else:
                poses.append({'landmarks': None})
        
        return poses
    
    def _detect_events(self, poses):
        wrist_heights = []
        for pose in poses:
            if pose['landmarks']:
                left_wrist = pose['landmarks'][15]
                wrist_heights.append(left_wrist['y'])
            else:
                wrist_heights.append(None)
        
        valid_heights = [h for h in wrist_heights if h is not None]
        
        if len(valid_heights) < 10:
            return {'address': 0, 'top': len(poses)//3, 'impact': len(poses)//2, 'finish': len(poses)-1}
        
        top_idx = wrist_heights.index(min(valid_heights))
        impact_idx = wrist_heights.index(max(valid_heights[top_idx:]))
        
        return {
            'address': 0,
            'top': top_idx,
            'impact': impact_idx,
            'finish': len(poses) - 1
        }
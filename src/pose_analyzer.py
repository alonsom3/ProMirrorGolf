# backend/pose_analyzer.py

import mediapipe as mp
import cv2
from typing import List, Dict
import logging
import asyncio

logger = logging.getLogger(__name__)

class PoseAnalyzer:
    """Simplified Pose Analyzer for SwingAIController"""

    def __init__(self, config: dict):
        self.mp_pose = mp.solutions.pose
        self.pose_dtl = self.mp_pose.Pose(static_image_mode=False)
        self.pose_face = self.mp_pose.Pose(static_image_mode=False)

    async def analyze(self, dtl_frame, face_frame) -> Dict:
        """Analyze latest frames and detect swing"""
        dtl_result = self.pose_dtl.process(cv2.cvtColor(dtl_frame, cv2.COLOR_BGR2RGB))
        face_result = self.pose_face.process(cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB))

        # Simple heuristic: if both frames detected a pose -> swing_detected True
        swing_detected = bool(dtl_result.pose_landmarks) and bool(face_result.pose_landmarks)
        return {"swing_detected": swing_detected}

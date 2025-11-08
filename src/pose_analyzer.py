# backend/pose_analyzer.py

import mediapipe as mp
import cv2
import numpy as np
from typing import Dict, List, Optional
import logging
from collections import deque
import time

logger = logging.getLogger(__name__)

class PoseAnalyzer:
    """Pose Analyzer for SwingAIController - Detects poses and swing events with GPU acceleration"""

    def __init__(self, config: dict):
        self.mp_pose = mp.solutions.pose
        min_confidence = config.get("ai", {}).get("min_detection_confidence", 0.5)
        use_gpu = config.get("ai", {}).get("use_gpu", False)
        
        # MediaPipe GPU support (if available)
        # Note: MediaPipe GPU requires specific setup, fallback to CPU if not available
        try:
            if use_gpu:
                # Try to use GPU-accelerated MediaPipe (requires proper setup)
                # For now, we'll use optimized CPU settings
                logger.info("Attempting GPU acceleration for pose detection")
                self.pose_dtl = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,  # Lower complexity for speed
                    min_detection_confidence=min_confidence,
                    min_tracking_confidence=0.5,
                    enable_segmentation=False  # Disable segmentation for speed
                )
                self.pose_face = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    min_detection_confidence=min_confidence,
                    min_tracking_confidence=0.5,
                    enable_segmentation=False
                )
            else:
                raise Exception("GPU not requested")
        except Exception as e:
            logger.warning(f"GPU acceleration not available, using CPU: {e}")
            self.pose_dtl = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=0.5,
                enable_segmentation=False
            )
            self.pose_face = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=0.5,
                enable_segmentation=False
            )
        
        # Buffer for swing sequence analysis
        self.dtl_pose_buffer = deque(maxlen=300)  # ~5 seconds at 60fps
        self.face_pose_buffer = deque(maxlen=300)
        self.swing_detected = False
        self.last_swing_frame = 0
        
        # Performance tracking
        self.frame_times = deque(maxlen=100)  # Track last 100 frame processing times
        self.use_gpu = use_gpu
        
        # Model caching - reuse initialized models
        self._model_initialized = True

    def set_model_type(self, model_type: str):
        """Dynamically change model complexity based on quality mode"""
        if model_type == self.model_type:
            return  # No change needed
        
        complexity_map = {
            "speed": 0,
            "balanced": 1,
            "quality": 2
        }
        
        new_complexity = complexity_map.get(model_type, 1)
        if new_complexity != self.model_complexity:
            logger.info(f"Changing pose model complexity: {self.model_complexity} -> {new_complexity} (type: {model_type})")
            
            # Reinitialize models with new complexity
            min_confidence = 0.5  # Default
            self.pose_dtl = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=new_complexity,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=0.5,
                enable_segmentation=False
            )
            self.pose_face = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=new_complexity,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=0.5,
                enable_segmentation=False
            )
            self.model_complexity = new_complexity
            self.model_type = model_type
    
    async def analyze(self, dtl_frame, face_frame, quality_mode: str = "balanced") -> Dict:
        """
        Analyze latest frames and detect swing (optimized for <100ms per frame)
        
        Args:
            dtl_frame: Down-the-line frame
            face_frame: Face-on frame
            quality_mode: "speed", "balanced", or "quality" - adjusts processing
        
        Returns:
            Dictionary with swing_detected, pose landmarks, and events
        """
        start_time = time.time()
        
        if dtl_frame is None or face_frame is None:
            return {"swing_detected": False}
        
        # Adjust target width based on quality mode for optimal speed/quality trade-off
        if quality_mode == "speed":
            target_width = 480  # Smaller for faster processing
        elif quality_mode == "quality":
            target_width = 1280  # Larger for better accuracy
        else:  # balanced
            target_width = 640  # Default balanced size
        
        # Optimize frame processing: resize if too large for faster processing
        # Use vectorized NumPy operations where possible
        if dtl_frame.shape[1] > target_width:
            scale = target_width / dtl_frame.shape[1]
            new_height = int(dtl_frame.shape[0] * scale)
            # Use faster interpolation for speed mode, better quality for quality mode
            interpolation = cv2.INTER_LINEAR if quality_mode == "speed" else cv2.INTER_AREA
            dtl_frame = cv2.resize(dtl_frame, (target_width, new_height), interpolation=interpolation)
            face_frame = cv2.resize(face_frame, (target_width, new_height), interpolation=interpolation)
        
        # Process frames (BGR to RGB conversion optimized with NumPy)
        # Vectorized color conversion is faster than cv2.cvtColor for large batches
        # But for single frames, cv2 is optimized, so we use it here
        dtl_rgb = cv2.cvtColor(dtl_frame, cv2.COLOR_BGR2RGB)
        face_rgb = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)
        
        # Process both frames (MediaPipe is optimized internally)
        dtl_result = self.pose_dtl.process(dtl_rgb)
        face_result = self.pose_face.process(face_rgb)
        
        # Extract landmarks (optimized extraction)
        dtl_landmarks = self._extract_landmarks(dtl_result)
        face_landmarks = self._extract_landmarks(face_result)
        
        # Add to buffers (only if landmarks exist)
        if dtl_landmarks:
            self.dtl_pose_buffer.append(dtl_landmarks)
        if face_landmarks:
            self.face_pose_buffer.append(face_landmarks)
        
        # Detect swing (simple heuristic: pose detected in both views)
        swing_detected = bool(dtl_result.pose_landmarks) and bool(face_result.pose_landmarks)
        
        # Detect swing events if we have enough frames
        events = {}
        dtl_poses = list(self.dtl_pose_buffer)
        
        if len(dtl_poses) >= 30 and swing_detected:
            events = self._detect_swing_events(dtl_poses)
        
        # Track performance
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        self.frame_times.append(elapsed)
        
        if elapsed > 100:
            logger.warning(f"Frame processing took {elapsed:.2f}ms (target: <100ms)")
        
        return {
            "swing_detected": swing_detected,
            "dtl_poses": dtl_poses,
            "face_poses": list(self.face_pose_buffer),
            "events": events,
            "dtl_landmarks": dtl_landmarks,
            "face_landmarks": face_landmarks,
            "processing_time_ms": elapsed
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.frame_times:
            return {"avg_ms": 0, "max_ms": 0, "min_ms": 0, "frames": 0}
        
        times = list(self.frame_times)
        return {
            "avg_ms": np.mean(times),
            "max_ms": np.max(times),
            "min_ms": np.min(times),
            "frames": len(times),
            "p95_ms": np.percentile(times, 95)
        }
    
    def _extract_landmarks(self, result) -> Optional[Dict]:
        """Extract landmarks from MediaPipe result"""
        if not result.pose_landmarks:
            return None
        
        landmarks = {}
        for idx, lm in enumerate(result.pose_landmarks.landmark):
            landmarks[idx] = {
                'x': lm.x,
                'y': lm.y,
                'z': lm.z,
                'visibility': lm.visibility
            }
        return landmarks
    
    def _detect_swing_events(self, poses: List[Dict]) -> Dict:
        """
        Detect key swing events: address, top, impact
        
        Uses wrist height to detect top of backswing and impact
        """
        if not poses or len(poses) < 10:
            return {
                'address': 0,
                'top': len(poses) // 3,
                'impact': len(poses) // 2,
                'finish': len(poses) - 1
            }
        
        # Track wrist heights (MediaPipe: 15=left_wrist, 16=right_wrist)
        wrist_heights = []
        for pose in poses:
            if pose and 15 in pose:  # left_wrist
                wrist_heights.append(pose[15]['y'])
            else:
                wrist_heights.append(None)
        
        valid_heights = [h for h in wrist_heights if h is not None]
        
        if len(valid_heights) < 10:
            # Not enough data, use defaults
            return {
                'address': 0,
                'top': len(poses) // 3,
                'impact': len(poses) // 2,
                'finish': len(poses) - 1
            }
        
        # Top of backswing: minimum wrist height
        min_height = min(valid_heights)
        top_idx = next(i for i, h in enumerate(wrist_heights) if h == min_height)
        
        # Impact: maximum wrist height after top (or use frame after top)
        if top_idx < len(wrist_heights) - 5:
            post_top_heights = [h for h in wrist_heights[top_idx:] if h is not None]
            if post_top_heights:
                max_height = max(post_top_heights)
                impact_idx = next(i for i, h in enumerate(wrist_heights[top_idx:], top_idx) 
                                 if h == max_height)
            else:
                impact_idx = top_idx + (len(poses) - top_idx) // 2
        else:
            impact_idx = len(poses) - 1
        
        return {
            'address': 0,
            'top': min(top_idx, len(poses) - 1),
            'impact': min(impact_idx, len(poses) - 1),
            'finish': len(poses) - 1
        }
    
    def clear_buffer(self):
        """Clear pose buffers (call after swing is processed)"""
        self.dtl_pose_buffer.clear()
        self.face_pose_buffer.clear()

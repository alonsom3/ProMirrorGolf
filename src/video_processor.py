"""
Video Processor - Handles offline video upload and processing
Supports dual video (DTL + Face) upload with auto-sync
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Processes uploaded videos for swing analysis
    Handles video validation, synchronization, and frame extraction
    """
    
    def __init__(self):
        self.dtl_video = None
        self.face_video = None
        self.dtl_cap = None
        self.face_cap = None
        self.sync_offset = 0  # Frame offset for synchronization
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        
    def load_videos(self, dtl_path: str, face_path: str) -> Dict:
        """
        Load and validate two video files
        
        Args:
            dtl_path: Path to down-the-line video
            face_path: Path to face-on video
            
        Returns:
            Dictionary with validation results and video info
        """
        result = {
            'success': False,
            'errors': [],
            'dtl_info': {},
            'face_info': {},
            'sync_offset': 0
        }
        
        # Validate files exist
        if not Path(dtl_path).exists():
            result['errors'].append(f"DTL video not found: {dtl_path}")
            return result
        
        if not Path(face_path).exists():
            result['errors'].append(f"Face video not found: {face_path}")
            return result
        
        # Try to open videos
        try:
            self.dtl_cap = cv2.VideoCapture(dtl_path)
            self.face_cap = cv2.VideoCapture(face_path)
            
            if not self.dtl_cap.isOpened():
                result['errors'].append(f"Failed to open DTL video: {dtl_path}")
                return result
            
            if not self.face_cap.isOpened():
                result['errors'].append(f"Failed to open Face video: {face_path}")
                return result
            
            # Get video properties
            dtl_fps = self.dtl_cap.get(cv2.CAP_PROP_FPS)
            dtl_frames = int(self.dtl_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            dtl_width = int(self.dtl_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            dtl_height = int(self.dtl_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            face_fps = self.face_cap.get(cv2.CAP_PROP_FPS)
            face_frames = int(self.face_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            face_width = int(self.face_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            face_height = int(self.face_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            result['dtl_info'] = {
                'fps': dtl_fps,
                'frames': dtl_frames,
                'width': dtl_width,
                'height': dtl_height,
                'duration': dtl_frames / dtl_fps if dtl_fps > 0 else 0
            }
            
            result['face_info'] = {
                'fps': face_fps,
                'frames': face_frames,
                'width': face_width,
                'height': face_height,
                'duration': face_frames / face_fps if face_fps > 0 else 0
            }
            
            # Use shorter video as reference
            self.total_frames = min(dtl_frames, face_frames)
            
            # Auto-sync: find best alignment (simple approach: use first frame)
            # In production, could use more sophisticated sync (audio, motion, etc.)
            self.sync_offset = 0
            result['sync_offset'] = self.sync_offset
            
            result['success'] = True
            logger.info(f"Videos loaded: DTL ({dtl_frames} frames @ {dtl_fps}fps), "
                       f"Face ({face_frames} frames @ {face_fps}fps)")
            
        except Exception as e:
            result['errors'].append(f"Error loading videos: {e}")
            logger.error(f"Error loading videos: {e}", exc_info=True)
        
        return result
    
    def get_frame(self, frame_number: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get frames at specified frame number (synchronized)
        
        Args:
            frame_number: Frame index (0-based)
            
        Returns:
            Tuple of (dtl_frame, face_frame) or (None, None) if error
        """
        if not self.dtl_cap or not self.face_cap:
            return None, None
        
        if frame_number < 0 or frame_number >= self.total_frames:
            return None, None
        
        # Set frame positions
        self.dtl_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.face_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number + self.sync_offset)
        
        # Read frames
        dtl_ret, dtl_frame = self.dtl_cap.read()
        face_ret, face_frame = self.face_cap.read()
        
        if not dtl_ret or not face_ret:
            return None, None
        
        self.current_frame = frame_number
        return dtl_frame, face_frame
    
    def get_all_frames(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Extract all frames from both videos (for batch processing)
        
        Returns:
            List of (dtl_frame, face_frame) tuples
        """
        frames = []
        
        if not self.dtl_cap or not self.face_cap:
            return frames
        
        # Reset to beginning
        self.dtl_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.face_cap.set(cv2.CAP_PROP_POS_FRAMES, self.sync_offset)
        
        frame_count = 0
        while frame_count < self.total_frames:
            dtl_ret, dtl_frame = self.dtl_cap.read()
            face_ret, face_frame = self.face_cap.read()
            
            if not dtl_ret or not face_ret:
                break
            
            frames.append((dtl_frame, face_frame))
            frame_count += 1
        
        logger.info(f"Extracted {len(frames)} frame pairs")
        return frames
    
    def release(self):
        """Release video resources"""
        if self.dtl_cap:
            self.dtl_cap.release()
            self.dtl_cap = None
        
        if self.face_cap:
            self.face_cap.release()
            self.face_cap = None
        
        logger.info("Video resources released")
    
    def validate_video_format(self, video_path: str) -> Dict:
        """
        Validate video file format and properties
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'info': {}
        }
        
        if not Path(video_path).exists():
            result['errors'].append(f"File not found: {video_path}")
            return result
        
        # Check file extension
        ext = Path(video_path).suffix.lower()
        supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if ext not in supported_formats:
            result['errors'].append(f"Unsupported format: {ext}. Supported: {', '.join(supported_formats)}")
            return result
        
        # Try to open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            result['errors'].append(f"Cannot open video file: {video_path}")
            return result
        
        # Get properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        result['info'] = {
            'fps': fps,
            'frames': frames,
            'width': width,
            'height': height,
            'duration': frames / fps if fps > 0 else 0
        }
        
        # Validate properties
        if fps <= 0:
            result['errors'].append("Invalid FPS")
        if frames <= 0:
            result['errors'].append("No frames in video")
        if width <= 0 or height <= 0:
            result['errors'].append("Invalid resolution")
        
        cap.release()
        
        result['valid'] = len(result['errors']) == 0
        return result


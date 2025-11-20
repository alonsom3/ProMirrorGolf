"""Video thumbnail generation utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2

logger = logging.getLogger(__name__)


def find_best_frame(video_path: Path, sample_count: int = 10) -> int:
    """Find the best frame for thumbnail generation.
    
    Analyzes multiple frames and selects the one with highest motion/contrast.
    
    Args:
        video_path: Path to video file
        sample_count: Number of frames to sample (default: 10)
        
    Returns:
        Frame number with best quality, or 0 if detection fails
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return 0
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            return 0
        
        # Sample frames evenly throughout video
        sample_frames = []
        if total_frames <= sample_count:
            sample_frames = list(range(total_frames))
        else:
            step = total_frames // sample_count
            sample_frames = [i * step for i in range(sample_count)]
        
        best_frame = 0
        best_score = 0
        
        for frame_num in sample_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate variance (measure of contrast/motion)
            variance = gray.var()
            
            # Prefer middle frames (avoid black frames at start/end)
            position_bonus = 1.0 - abs(frame_num - total_frames / 2) / (total_frames / 2)
            score = variance * (0.7 + 0.3 * position_bonus)
            
            if score > best_score:
                best_score = score
                best_frame = frame_num
        
        cap.release()
        return best_frame
    except Exception as e:
        logger.error("Error finding best frame: %s", e)
        return 0


def generate_thumbnail(video_path: Path, output_path: Optional[Path] = None, frame_number: Optional[int] = None, use_smart_detection: bool = True) -> Optional[Path]:
    """Generate a thumbnail from a video file.
    
    Extracts a frame from the video, resizes it to fit within 320x240 pixels while maintaining
    aspect ratio, and saves it as a JPEG. If a thumbnail already exists, returns the existing path.
    
    Args:
        video_path: Path to video file
        output_path: Optional output path for thumbnail (defaults to video_path with _thumb.jpg extension)
        frame_number: Frame number to extract (None = auto-detect best frame)
        use_smart_detection: If True and frame_number is None, automatically find best frame
    
    Returns:
        Path to generated thumbnail, or None if generation failed
        
    Raises:
        No exceptions raised - all errors are logged and None is returned
    """
    if not video_path.exists():
        logger.warning("Video file not found: %s", video_path)
        return None
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("Failed to open video: %s", video_path)
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            logger.warning("Video has no frames: %s", video_path)
            cap.release()
            return None
        
        # Determine frame number
        if frame_number is None:
            if use_smart_detection:
                frame_number = find_best_frame(video_path)
            else:
                # Use middle frame as fallback
                frame_number = total_frames // 2
        
        # Clamp frame number to valid range
        frame_number = min(max(0, frame_number), total_frames - 1)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            logger.error("Failed to read frame %d from video: %s", frame_number, video_path)
            return None
        
        # Determine output path
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
        
        # Resize if needed (max 320x240)
        height, width = frame.shape[:2]
        max_width, max_height = 320, 240
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Save thumbnail
        success = cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if success:
            logger.debug("Generated thumbnail: %s", output_path)
            return output_path
        else:
            logger.error("Failed to save thumbnail: %s", output_path)
            return None
            
    except Exception as e:
        logger.error("Error generating thumbnail for %s: %s", video_path, e, exc_info=True)
        return None


def get_thumbnail_path(video_path: Path) -> Path:
    """Get the expected thumbnail path for a video file.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Path where thumbnail should be located (same directory as video with _thumb.jpg suffix)
    """
    return video_path.parent / f"{video_path.stem}_thumb.jpg"


"""
Video Processing Utilities
Helper functions for video manipulation and processing
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Utility class for common video processing tasks.
    Handles video loading, saving, frame extraction, and basic editing.
    """
    
    @staticmethod
    def load_video(video_path: str) -> List[np.ndarray]:
        """
        Load all frames from a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of frames as numpy arrays
        """
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return []
        
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            frame_count += 1
        
        cap.release()
        logger.info(f"Loaded {frame_count} frames from {video_path}")
        
        return frames
    
    @staticmethod
    def save_video(frames: List[np.ndarray], output_path: str, 
                   fps: int = 30, codec: str = 'mp4v') -> bool:
        """
        Save frames to a video file.
        
        Args:
            frames: List of frames to save
            output_path: Output file path
            fps: Frames per second
            codec: Video codec (default: mp4v)
            
        Returns:
            True if successful, False otherwise
        """
        if not frames:
            logger.error("No frames to save")
            return False
        
        # Create output directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Get frame dimensions
        height, width = frames[0].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            logger.error(f"Failed to open video writer: {output_path}")
            return False
        
        # Write frames
        for frame in frames:
            out.write(frame)
        
        out.release()
        logger.info(f"Saved {len(frames)} frames to {output_path}")
        
        return True
    
    @staticmethod
    def get_video_info(video_path: str) -> Optional[dict]:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video properties, or None if error
        """
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return None
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return None
        
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(cap.get(cv2.CAP_PROP_FPS)),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        cap.release()
        
        logger.info(f"Video info for {video_path}: {info['width']}x{info['height']} "
                   f"@ {info['fps']}fps, {info['frame_count']} frames")
        
        return info
    
    @staticmethod
    def extract_frame_range(video_path: str, start_frame: int, 
                          end_frame: int) -> List[np.ndarray]:
        """
        Extract a specific range of frames from a video.
        
        Args:
            video_path: Path to video file
            start_frame: Starting frame index (0-based)
            end_frame: Ending frame index (inclusive)
            
        Returns:
            List of frames in the range
        """
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return []
        
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_frame = start_frame
        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            current_frame += 1
        
        cap.release()
        logger.info(f"Extracted {len(frames)} frames ({start_frame}-{end_frame})")
        
        return frames
    
    @staticmethod
    def resize_video(frames: List[np.ndarray], 
                    target_size: Tuple[int, int]) -> List[np.ndarray]:
        """
        Resize all frames to target dimensions.
        
        Args:
            frames: List of frames to resize
            target_size: Target (width, height)
            
        Returns:
            List of resized frames
        """
        if not frames:
            return []
        
        resized = []
        for frame in frames:
            resized_frame = cv2.resize(frame, target_size)
            resized.append(resized_frame)
        
        logger.info(f"Resized {len(frames)} frames to {target_size}")
        
        return resized
    
    @staticmethod
    def create_side_by_side(frames1: List[np.ndarray], 
                           frames2: List[np.ndarray],
                           label1: str = "Video 1",
                           label2: str = "Video 2") -> List[np.ndarray]:
        """
        Create side-by-side comparison video from two frame lists.
        
        Args:
            frames1: First video frames
            frames2: Second video frames
            label1: Label for first video
            label2: Label for second video
            
        Returns:
            List of combined frames
        """
        if not frames1 or not frames2:
            logger.error("Both frame lists must be non-empty")
            return []
        
        # Determine dimensions
        h1, w1 = frames1[0].shape[:2]
        h2, w2 = frames2[0].shape[:2]
        
        # Use dimensions of first video
        target_height = h1
        target_width = w1
        
        # Resize second video to match first
        frames2_resized = [cv2.resize(f, (target_width, target_height)) 
                          for f in frames2]
        
        # Combine frames
        combined = []
        min_frames = min(len(frames1), len(frames2_resized))
        
        for i in range(min_frames):
            frame1 = frames1[i].copy()
            frame2 = frames2_resized[i].copy()
            
            # Add labels
            cv2.putText(frame1, label1, (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame2, label2, (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
            
            # Stack horizontally
            combined_frame = np.hstack([frame1, frame2])
            combined.append(combined_frame)
        
        logger.info(f"Created {len(combined)} side-by-side frames")
        
        return combined
    
    @staticmethod
    def add_skeleton_overlay(frames: List[np.ndarray], 
                            landmarks_list: List[dict]) -> List[np.ndarray]:
        """
        Add pose skeleton overlay to video frames.
        
        Args:
            frames: Video frames
            landmarks_list: List of landmark dictionaries for each frame
            
        Returns:
            Frames with skeleton overlay
        """
        if len(frames) != len(landmarks_list):
            logger.warning("Frame count doesn't match landmarks count")
            min_len = min(len(frames), len(landmarks_list))
            frames = frames[:min_len]
            landmarks_list = landmarks_list[:min_len]
        
        overlaid_frames = []
        
        for frame, landmarks in zip(frames, landmarks_list):
            frame_copy = frame.copy()
            
            if landmarks:
                # Draw skeleton on frame
                frame_copy = VideoProcessor._draw_skeleton(frame_copy, landmarks)
            
            overlaid_frames.append(frame_copy)
        
        logger.info(f"Added skeleton overlay to {len(overlaid_frames)} frames")
        
        return overlaid_frames
    
    @staticmethod
    def _draw_skeleton(frame: np.ndarray, landmarks: dict) -> np.ndarray:
        """Draw pose skeleton on a single frame"""
        height, width = frame.shape[:2]
        
        # MediaPipe skeleton connections
        connections = [
            (11, 12), (11, 13), (13, 15),  # Arms
            (12, 14), (14, 16),
            (11, 23), (12, 24),            # Torso
            (23, 24), (23, 25), (25, 27),  # Legs
            (24, 26), (26, 28)
        ]
        
        # Draw connections
        for start_idx, end_idx in connections:
            if start_idx in landmarks and end_idx in landmarks:
                start_lm = landmarks[start_idx]
                end_lm = landmarks[end_idx]
                
                start_point = (int(start_lm['x'] * width), 
                              int(start_lm['y'] * height))
                end_point = (int(end_lm['x'] * width), 
                            int(end_lm['y'] * height))
                
                cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        
        # Draw joints
        for idx, landmark in landmarks.items():
            point = (int(landmark['x'] * width), 
                    int(landmark['y'] * height))
            cv2.circle(frame, point, 4, (0, 0, 255), -1)
        
        return frame
    
    @staticmethod
    def extract_key_frames(frames: List[np.ndarray], 
                          event_indices: dict) -> dict:
        """
        Extract key frames from swing based on event indices.
        
        Args:
            frames: All video frames
            event_indices: Dictionary with event names and frame indices
                          (e.g., {'address': 10, 'top': 45, 'impact': 60})
            
        Returns:
            Dictionary mapping event names to frames
        """
        key_frames = {}
        
        for event, idx in event_indices.items():
            if 0 <= idx < len(frames):
                key_frames[event] = frames[idx]
                logger.debug(f"Extracted key frame: {event} at frame {idx}")
            else:
                logger.warning(f"Event index out of range: {event}={idx}")
        
        return key_frames
    
    @staticmethod
    def slow_motion(frames: List[np.ndarray], factor: int = 2) -> List[np.ndarray]:
        """
        Create slow motion effect by duplicating frames.
        
        Args:
            frames: Original frames
            factor: Slow motion factor (2 = half speed, 4 = quarter speed)
            
        Returns:
            Frames with slow motion effect
        """
        slow_frames = []
        
        for frame in frames:
            # Add original frame plus duplicates
            for _ in range(factor):
                slow_frames.append(frame.copy())
        
        logger.info(f"Created {len(slow_frames)} slow motion frames "
                   f"from {len(frames)} original frames (factor: {factor}x)")
        
        return slow_frames


# Test function
def test_video_processor():
    """Test video processing utilities"""
    print("Testing VideoProcessor...")
    
    # Create sample frames
    print("\n1. Creating sample frames...")
    frames = []
    for i in range(30):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (200, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        frames.append(frame)
    print(f"   Created {len(frames)} sample frames")
    
    # Save video
    print("\n2. Saving video...")
    output_path = "./test_video.mp4"
    success = VideoProcessor.save_video(frames, output_path, fps=30)
    print(f"   {'✓' if success else '✗'} Video saved: {output_path}")
    
    # Get video info
    print("\n3. Getting video info...")
    info = VideoProcessor.get_video_info(output_path)
    if info:
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   FPS: {info['fps']}")
        print(f"   Frames: {info['frame_count']}")
        print(f"   Duration: {info['duration']:.2f}s")
    
    # Load video back
    print("\n4. Loading video...")
    loaded_frames = VideoProcessor.load_video(output_path)
    print(f"   Loaded {len(loaded_frames)} frames")
    
    # Extract frame range
    print("\n5. Extracting frame range...")
    range_frames = VideoProcessor.extract_frame_range(output_path, 10, 20)
    print(f"   Extracted {len(range_frames)} frames")
    
    print("\n✓ All tests complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_video_processor()

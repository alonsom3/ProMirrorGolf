"""
Video Splitter - Automatically detects and splits dual-view golf videos
Handles side-by-side (DTL + Face-on) videos
"""

import cv2
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoSplitter:
    """
    Automatically detects layout and splits dual-view videos
    """
    
    def __init__(self):
        pass
    
    def detect_layout(self, video_path: str) -> dict:
        """
        Detect if video is side-by-side and which side is which
        
        Returns:
            dict with 'layout', 'dtl_side', 'split_ratio'
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Read first frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError("Cannot read video frame")
        
        height, width = frame.shape[:2]
        
        # Check if it's side-by-side (width >> height)
        aspect_ratio = width / height
        
        if aspect_ratio > 2.5:
            # Definitely side-by-side
            logger.info(f"Detected side-by-side layout (aspect ratio: {aspect_ratio:.2f})")
            
            # Split in half and analyze both sides
            mid = width // 2
            left_side = frame[:, :mid]
            right_side = frame[:, mid:]
            
            # Detect which side is DTL vs Face-on
            # DTL typically shows golfer from side/behind
            # Face-on shows golfer facing camera
            
            # Simple heuristic: DTL usually has more vertical motion lines
            # Face-on has more horizontal spread
            left_edges = cv2.Canny(left_side, 50, 150)
            right_edges = cv2.Canny(right_side, 50, 150)
            
            left_vertical = np.sum(left_edges[:, :] > 0)
            right_vertical = np.sum(right_edges[:, :] > 0)
            
            # More sophisticated: check center of mass
            left_gray = cv2.cvtColor(left_side, cv2.COLOR_BGR2GRAY)
            right_gray = cv2.cvtColor(right_side, cv2.COLOR_BGR2GRAY)
            
            # Calculate horizontal variance (face-on typically has more)
            left_h_var = np.var(np.sum(left_gray, axis=0))
            right_h_var = np.var(np.sum(right_gray, axis=0))
            
            # DTL is typically on the left in most videos
            # But let's make an educated guess
            if left_h_var < right_h_var:
                dtl_side = 'left'
                logger.info("Detected: DTL on LEFT, Face-on on RIGHT")
            else:
                dtl_side = 'right'
                logger.info("Detected: DTL on RIGHT, Face-on on LEFT")
            
            return {
                'layout': 'side_by_side',
                'dtl_side': dtl_side,
                'split_ratio': 0.5,
                'width': width,
                'height': height
            }
        else:
            # Single view
            logger.info(f"Detected single view (aspect ratio: {aspect_ratio:.2f})")
            return {
                'layout': 'single',
                'width': width,
                'height': height
            }
    
    def split_video(self, video_path: str, output_dir: str = None, 
                    force_dtl_side: str = None) -> dict:
        """
        Split a dual-view video into separate DTL and Face-on videos
        
        Args:
            video_path: Path to input video
            output_dir: Output directory (default: same as input)
            force_dtl_side: Force DTL to be 'left' or 'right' (overrides detection)
        
        Returns:
            dict with paths to DTL and Face-on videos
        """
        video_path = Path(video_path)
        
        if output_dir is None:
            output_dir = video_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect layout
        layout_info = self.detect_layout(str(video_path))
        
        if layout_info['layout'] == 'single':
            logger.warning("Video appears to be single view, not splitting")
            return {
                'dtl': str(video_path),
                'face': None,
                'layout': 'single'
            }
        
        # Override detection if forced
        if force_dtl_side:
            layout_info['dtl_side'] = force_dtl_side
            logger.info(f"Forced DTL side to: {force_dtl_side}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate split
        split_x = int(width * layout_info['split_ratio'])
        
        # Determine output regions
        if layout_info['dtl_side'] == 'left':
            dtl_region = (0, 0, split_x, height)
            face_region = (split_x, 0, width, height)
        else:
            dtl_region = (split_x, 0, width, height)
            face_region = (0, 0, split_x, height)
        
        # Create output paths
        base_name = video_path.stem
        dtl_path = output_dir / f"{base_name}_DTL.mp4"
        face_path = output_dir / f"{base_name}_Face.mp4"
        
        # Create video writers
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        dtl_writer = cv2.VideoWriter(
            str(dtl_path), 
            fourcc, 
            fps, 
            (dtl_region[2] - dtl_region[0], dtl_region[3] - dtl_region[1])
        )
        
        face_writer = cv2.VideoWriter(
            str(face_path), 
            fourcc, 
            fps, 
            (face_region[2] - face_region[0], face_region[3] - face_region[1])
        )
        
        logger.info(f"Splitting video: {video_path.name}")
        logger.info(f"Total frames: {total_frames}")
        logger.info(f"Output: {dtl_path.name} and {face_path.name}")
        
        # Process frames
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract regions
            dtl_frame = frame[
                dtl_region[1]:dtl_region[3],
                dtl_region[0]:dtl_region[2]
            ]
            
            face_frame = frame[
                face_region[1]:face_region[3],
                face_region[0]:face_region[2]
            ]
            
            # Write frames
            dtl_writer.write(dtl_frame)
            face_writer.write(face_frame)
            
            frame_count += 1
            
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"Progress: {progress:.1f}%")
        
        # Cleanup
        cap.release()
        dtl_writer.release()
        face_writer.release()
        
        logger.info("Split complete!")
        
        return {
            'dtl': str(dtl_path),
            'face': str(face_path),
            'layout': 'side_by_side',
            'dtl_side': layout_info['dtl_side']
        }


def main():
    """Command-line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python split_video.py <video_path> [output_dir] [--dtl-left|--dtl-right]")
        print("\nExample:")
        print('  python split_video.py "D:\\ProMirrorGolf\\data\\pro_videos\\Justin_Thomas_DTLandFFO.mp4"')
        print('  python split_video.py video.mp4 ./output --dtl-left')
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    
    force_dtl_side = None
    if '--dtl-left' in sys.argv:
        force_dtl_side = 'left'
    elif '--dtl-right' in sys.argv:
        force_dtl_side = 'right'
    
    splitter = VideoSplitter()
    
    try:
        result = splitter.split_video(video_path, output_dir, force_dtl_side)
        
        print("\n" + "="*60)
        print("SPLIT COMPLETE!")
        print("="*60)
        print(f"DTL video: {result['dtl']}")
        if result['face']:
            print(f"Face-on video: {result['face']}")
        print(f"Layout: {result['layout']}")
        if 'dtl_side' in result:
            print(f"DTL was on: {result['dtl_side']}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
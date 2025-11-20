"""Performance profiling script for ProMirrorGolf."""

import cProfile
import pstats
import io
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def profile_video_writing():
    """Profile video writing performance."""
    import cv2
    import numpy as np
    from pathlib import Path
    import tempfile
    
    # Create test frames
    frames = []
    for i in range(300):  # 5 seconds at 60fps
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[:, :] = (i % 255, (i * 2) % 255, (i * 3) % 255)
        frames.append(frame)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_video.mp4"
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Write video
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, 60.0, (1280, 720))
        
        for frame in frames:
            writer.write(frame)
        
        writer.release()
        
        profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        
        print("Video Writing Performance:")
        print(s.getvalue())

def profile_thumbnail_generation():
    """Profile thumbnail generation performance."""
    import cv2
    import numpy as np
    from pathlib import Path
    import tempfile
    from core.thumbnails import generate_thumbnail
    
    # Create test video
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / "test_video.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video_path), fourcc, 60.0, (1280, 720))
        
        for i in range(300):
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            frame[:, :] = (i % 255, (i * 2) % 255, (i * 3) % 255)
            writer.write(frame)
        
        writer.release()
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Generate thumbnail
        generate_thumbnail(video_path)
        
        profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        
        print("Thumbnail Generation Performance:")
        print(s.getvalue())

if __name__ == "__main__":
    print("=" * 60)
    print("ProMirrorGolf Performance Profiling")
    print("=" * 60)
    print()
    
    print("1. Profiling video writing...")
    profile_video_writing()
    print()
    
    print("2. Profiling thumbnail generation...")
    profile_thumbnail_generation()
    print()


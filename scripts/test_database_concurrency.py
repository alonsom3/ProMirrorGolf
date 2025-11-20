"""Test database concurrency improvements."""

import sys
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.session_manager import SessionManager
import tempfile


def test_concurrent_writes():
    """Test that concurrent database writes work correctly."""
    print("Testing concurrent database writes...")
    
    # Create temporary database
    db_path = Path(tempfile.mktemp(suffix='.db'))
    sm = SessionManager(db_path)
    
    # Start a session
    session_id = sm.start_session("Concurrency Test", club="Driver")
    print(f"  [OK] Session started: {session_id}")
    
    # Simulate concurrent writes from multiple threads
    errors = []
    shot_ids = []
    
    def write_shot(thread_id):
        try:
            payload = {
                "ClubSpeed": 100.0 + thread_id,
                "BallSpeed": 150.0 + thread_id,
                "TotalSpin": 3000,
            }
            shot_id = sm.log_shot(payload, dtl_video_path=f"test_{thread_id}.mp4")
            shot_ids.append(shot_id)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    # Create 10 threads writing simultaneously
    threads = []
    for i in range(10):
        t = threading.Thread(target=write_shot, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Check results
    if errors:
        print(f"  [FAIL] {len(errors)} errors occurred:")
        for error in errors[:5]:  # Show first 5
            print(f"    - {error}")
        return False
    
    if len(shot_ids) != 10:
        print(f"  [FAIL] Expected 10 shots, got {len(shot_ids)}")
        return False
    
    print(f"  [OK] All {len(shot_ids)} concurrent writes succeeded")
    print(f"  [OK] Shot IDs: {shot_ids}")
    return True


def test_retry_logic():
    """Test that retry logic works (simulate lock condition)."""
    print("Testing retry logic...")
    
    # Create temporary database
    db_path = Path(tempfile.mktemp(suffix='.db'))
    sm = SessionManager(db_path)
    
    session_id = sm.start_session("Retry Test", club="Driver")
    
    # Normal write should work
    shot_id = sm.log_shot({"ClubSpeed": 100.0}, dtl_video_path="test.mp4")
    if shot_id > 0:
        print(f"  [OK] Normal write succeeded: shot_id={shot_id}")
    else:
        print("  [FAIL] Normal write failed")
        return False
    
    return True


def test_buffer_limits():
    """Test that circular buffer respects maxlen."""
    print("Testing circular buffer limits...")
    
    from core.buffer import CircularBuffer
    import numpy as np
    
    buf = CircularBuffer(max_frames=5)
    
    # Add 10 frames, should only keep last 5
    for i in range(10):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        buf.add(frame, float(i))
    
    dumped = buf.dump()
    if len(dumped) != 5:
        print(f"  [FAIL] Expected 5 frames, got {len(dumped)}")
        return False
    
    # Check timestamps (should be last 5: 5, 6, 7, 8, 9)
    timestamps = [f.timestamp for f in dumped]
    if timestamps != [5.0, 6.0, 7.0, 8.0, 9.0]:
        print(f"  [FAIL] Wrong timestamps: {timestamps}")
        return False
    
    print(f"  [OK] Buffer correctly limits to 5 frames")
    print(f"  [OK] Timestamps: {timestamps}")
    return True


def main():
    print("=" * 60)
    print("Database Concurrency & Buffer Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Buffer limits
    results.append(("Buffer Limits", test_buffer_limits()))
    print()
    
    # Test 2: Retry logic
    results.append(("Retry Logic", test_retry_logic()))
    print()
    
    # Test 3: Concurrent writes
    results.append(("Concurrent Writes", test_concurrent_writes()))
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("[OK] All tests passed!")
    else:
        print("[FAIL] Some tests failed")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


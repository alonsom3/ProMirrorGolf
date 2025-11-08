"""
Test camera detection and capture
Run: python tests/test_cameras.py
"""

import cv2
import sys

def test_cameras():
    """Test all connected cameras"""
    print("\nTesting Cameras...")
    print("=" * 60)
    
    found_cameras = []
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"OK Camera {i}: {width}x{height} @ {fps}fps")
            found_cameras.append(i)
            
            cap.release()
    
    print("=" * 60)
    
    if len(found_cameras) >= 2:
        print(f"\nSUCCESS: Found {len(found_cameras)} cameras")
        print(f"  Camera IDs: {found_cameras}")
        print(f"\nUpdate config.json:")
        print(f'  "dtl_id": {found_cameras[0]},')
        print(f'  "face_id": {found_cameras[1]},')
        return True
    else:
        print(f"\nFAILED: Only found {len(found_cameras)} camera(s)")
        print("  Need at least 2 cameras")
        return False

def show_camera_preview():
    """Show live camera preview"""
    print("\nStarting camera preview...")
    print("Press 'q' to quit, 's' to save snapshot\n")
    
    cap0 = cv2.VideoCapture(0)
    cap1 = cv2.VideoCapture(1) if True else None
    
    if not cap0.isOpened():
        print("ERROR Cannot open camera 0")
        return
    
    use_two = cap1.isOpened() if cap1 else False
    
    while True:
        ret0, frame0 = cap0.read()
        if not ret0:
            break
        
        cv2.putText(frame0, "Camera 0 - DTL (Press 'q' to quit)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Camera 0 - Down-the-Line', frame0)
        
        if use_two:
            ret1, frame1 = cap1.read()
            if ret1:
                cv2.putText(frame1, "Camera 1 - Face", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow('Camera 1 - Face-On', frame1)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite('snapshot_cam0.jpg', frame0)
            print("OK Saved snapshot_cam0.jpg")
            if use_two and ret1:
                cv2.imwrite('snapshot_cam1.jpg', frame1)
                print("OK Saved snapshot_cam1.jpg")
    
    cap0.release()
    if cap1:
        cap1.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if '--preview' in sys.argv:
        show_camera_preview()
    else:
        test_cameras()

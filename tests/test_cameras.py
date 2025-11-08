"""
Camera Test Utility - Test and preview cameras
"""

import cv2
import sys
from pathlib import Path

def test_cameras(max_cameras=10):
    """Test all available cameras"""
    
    print("="*60)
    print("Camera Detection Test")
    print("="*60)
    print()
    
    available = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Camera {i}: FOUND")
            print(f"  Resolution: {int(width)}x{int(height)}")
            print(f"  FPS: {int(fps)}")
            print()
            
            available.append(i)
            cap.release()
    
    if not available:
        print("No cameras detected!")
        return []
    
    print(f"Found {len(available)} camera(s): {available}")
    print("="*60)
    
    return available


def preview_camera(camera_id):
    """Show live preview of a camera"""
    
    print(f"\nOpening camera {camera_id}...")
    print("Press 'q' to quit, 's' to save screenshot")
    print()
    
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {camera_id}")
        return
    
    # Try to set high resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 60)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"Camera {camera_id} opened:")
    print(f"  Resolution: {actual_width}x{actual_height}")
    print(f"  FPS: {actual_fps}")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to read frame")
            break
        
        frame_count += 1
        
        # Add info overlay
        cv2.putText(frame, f"Camera {camera_id}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save", (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(f'Camera {camera_id} Preview', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f'camera_{camera_id}_screenshot.jpg'
            cv2.imwrite(filename, frame)
            print(f"Saved screenshot: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    """Main entry point"""
    
    # Test all cameras
    available = test_cameras()
    
    if not available:
        sys.exit(1)
    
    # Ask which to preview
    print("\nWhich camera do you want to preview?")
    for cam_id in available:
        print(f"  {cam_id}")
    print("  a - Preview all cameras")
    print("  q - Quit")
    print()
    
    choice = input("Enter choice: ").strip().lower()
    
    if choice == 'q':
        return
    
    if choice == 'a':
        # Preview all
        for cam_id in available:
            preview_camera(cam_id)
    else:
        # Preview specific camera
        try:
            cam_id = int(choice)
            if cam_id in available:
                preview_camera(cam_id)
            else:
                print(f"Camera {cam_id} not available")
        except ValueError:
            print("Invalid choice")


if __name__ == "__main__":
    main()
import cv2
import time

def find_available_cameras(max_indices_to_check=5):
    """
    Cycles through potential camera indices and displays their video feed.
    """
    print("Checking for available cameras...")
    print("Press 'q' in the video window to check the next camera index.")
    
    for index in range(max_indices_to_check):
        # Use cv2.CAP_DSHOW for better Windows support
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) 
        
        if not cap.isOpened():
            print(f"No camera found at index {index}")
            continue
        
        print(f"\n--- Displaying Camera Index: {index} ---")
        window_name = f"Camera Index: {index} (Press 'q' to check next)"
        
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            if not ret:
                print(f"Error reading frame from camera {index}")
                break
            
            # Display the resulting frame
            cv2.imshow(window_name, frame)
            
            # Wait for 1ms and check if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release the capture and destroy the window
        cap.release()
        cv2.destroyWindow(window_name)
        
        # Add a small delay so windows can close properly
        time.sleep(0.5)

    print("\n--- Finished checking all indices ---")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    find_available_cameras()
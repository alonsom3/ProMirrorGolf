import cv2

print("Scanning for cameras...")
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"✅ Camera {i}: {w}x{h}")
        cap.release()
    else:
        print(f"❌ Camera {i}: Not available")

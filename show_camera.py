import cv2

# Maximum number of cameras to check
MAX_CAMERAS = 10

caps = []
window_names = []

print("Scanning for cameras...")

# Open all cameras
for i in range(MAX_CAMERAS):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            caps.append(cap)
            window_name = f"Camera {i}"
            window_names.append(window_name)
            cv2.imshow(window_name, frame)
            print(f"✅ Camera {i} detected")
        else:
            cap.release()
    else:
        print(f"❌ Camera {i} not available")

if not caps:
    print("No cameras detected.")
    exit()

print("\nPress 'q' in any window to close all feeds.")

# Show live feed for all cameras
while True:
    for idx, cap in enumerate(caps):
        ret, frame = cap.read()
        if ret:
            cv2.imshow(window_names[idx], frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release all cameras and close windows
for cap in caps:
    cap.release()
cv2.destroyAllWindows()

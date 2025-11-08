import cv2

for cam_id in range(3):
    print(f"\nTesting camera {cam_id}...")

    for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
        cap = cv2.VideoCapture(cam_id, backend)
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✅ Camera {cam_id} works with backend {backend}")
            cv2.imshow(f"Camera {cam_id}", frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            break
        cap.release()
    else:
        print(f"❌ Camera {cam_id} failed with all backends")

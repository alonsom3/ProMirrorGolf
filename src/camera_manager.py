# backend/camera_manager.py

import cv2
import numpy as np
import asyncio
import threading
import time
from collections import deque
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CameraBuffer:
    def __init__(self, max_seconds: float, fps: int):
        self.max_frames = int(max_seconds * fps)
        self.buffer = deque(maxlen=self.max_frames)
        self.timestamps = deque(maxlen=self.max_frames)
        self.fps = fps
        self.lock = threading.Lock()

    def add_frame(self, frame: np.ndarray, timestamp: float):
        with self.lock:
            self.buffer.append(frame.copy())
            self.timestamps.append(timestamp)

    def get_last_frame(self):
        with self.lock:
            if self.buffer:
                return self.buffer[-1].copy()
            return None

class DualCameraManager:
    """Manages two cameras with circular buffering"""

    def __init__(self, config: dict):
        cam_cfg = config.get("cameras", {})
        self.dtl_id = cam_cfg.get("dtl_id", 0)
        self.face_id = cam_cfg.get("face_id", 1)
        self.fps = cam_cfg.get("fps", 120)
        res = cam_cfg.get("resolution", [1280, 720])
        self.resolution = (res[0], res[1])

        self.buffer_seconds = 10.0

        self.dtl_buffer = CameraBuffer(self.buffer_seconds, self.fps)
        self.face_buffer = CameraBuffer(self.buffer_seconds, self.fps)

        self.dtl_cam = None
        self.face_cam = None
        self.is_capturing = False
        self.capture_threads = []

    def _init_camera(self, camera_id: int) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera {camera_id}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        return cap

    async def start_buffering(self):
        if self.is_capturing:
            return
        self.dtl_cam = self._init_camera(self.dtl_id)
        self.face_cam = self._init_camera(self.face_id)
        self.is_capturing = True

        dtl_thread = threading.Thread(target=self._capture_loop, args=(self.dtl_cam, self.dtl_buffer, "DTL"), daemon=True)
        face_thread = threading.Thread(target=self._capture_loop, args=(self.face_cam, self.face_buffer, "Face"), daemon=True)
        dtl_thread.start()
        face_thread.start()
        self.capture_threads = [dtl_thread, face_thread]

    def _capture_loop(self, cam, buffer, name: str):
        while self.is_capturing:
            ret, frame = cam.read()
            if ret:
                buffer.add_frame(frame, time.time())
            else:
                time.sleep(0.01)

    async def stop_buffering(self):
        self.is_capturing = False
        for t in self.capture_threads:
            t.join(timeout=2)
        if self.dtl_cam:
            self.dtl_cam.release()
        if self.face_cam:
            self.face_cam.release()

    async def get_latest_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        return self.dtl_buffer.get_last_frame(), self.face_buffer.get_last_frame()

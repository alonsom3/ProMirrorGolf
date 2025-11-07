"""
Dual Camera Manager with Circular Buffering
"""
import cv2
import numpy as np
import threading
from collections import deque
import time
import logging

logger = logging.getLogger(__name__)


class CameraBuffer:
    def __init__(self, max_seconds, fps):
        self.max_frames = int(max_seconds * fps)
        self.buffer = deque(maxlen=self.max_frames)
        self.timestamps = deque(maxlen=self.max_frames)
        self.lock = threading.Lock()
    
    def add_frame(self, frame, timestamp):
        with self.lock:
            self.buffer.append(frame.copy())
            self.timestamps.append(timestamp)
    
    def get_last_n_seconds(self, seconds):
        with self.lock:
            if len(self.timestamps) == 0:
                return []
            
            end_time = self.timestamps[-1]
            start_time = end_time - seconds
            
            frames = []
            for i, ts in enumerate(self.timestamps):
                if ts >= start_time:
                    frames.append(self.buffer[i].copy())
            
            return frames


class DualCameraManager:
    def __init__(self, dtl_id, face_id, fps=60, resolution=(1280, 720)):
        self.dtl_id = dtl_id
        self.face_id = face_id
        self.fps = fps
        self.resolution = resolution
        
        self.dtl_camera = None
        self.face_camera = None
        self.dtl_buffer = CameraBuffer(10.0, fps)
        self.face_buffer = CameraBuffer(10.0, fps)
        
        self.is_capturing = False
        self.threads = []
        
        logger.info(f"Camera manager initialized: {fps}fps @ {resolution}")
    
    def start_buffering(self):
        self.dtl_camera = cv2.VideoCapture(self.dtl_id)
        self.face_camera = cv2.VideoCapture(self.face_id)
        
        self.dtl_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.dtl_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.dtl_camera.set(cv2.CAP_PROP_FPS, self.fps)
        
        self.face_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.face_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.face_camera.set(cv2.CAP_PROP_FPS, self.fps)
        
        self.is_capturing = True
        
        dtl_thread = threading.Thread(
            target=self._capture_loop,
            args=(self.dtl_camera, self.dtl_buffer, "DTL"),
            daemon=True
        )
        face_thread = threading.Thread(
            target=self._capture_loop,
            args=(self.face_camera, self.face_buffer, "Face"),
            daemon=True
        )
        
        dtl_thread.start()
        face_thread.start()
        
        self.threads = [dtl_thread, face_thread]
        logger.info("Camera buffering started")
    
    def _capture_loop(self, camera, buffer, name):
        while self.is_capturing:
            ret, frame = camera.read()
            if ret:
                timestamp = time.time()
                buffer.add_frame(frame, timestamp)
    
    def capture_from_buffer(self, duration_seconds=5.0):
        dtl_frames = self.dtl_buffer.get_last_n_seconds(duration_seconds)
        face_frames = self.face_buffer.get_last_n_seconds(duration_seconds)
        
        return {
            'dtl': dtl_frames,
            'face': face_frames
        }
    
    def stop_buffering(self):
        self.is_capturing = False
        
        if self.dtl_camera:
            self.dtl_camera.release()
        if self.face_camera:
            self.face_camera.release()
        
        logger.info("Camera buffering stopped")
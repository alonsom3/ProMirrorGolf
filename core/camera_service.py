from __future__ import annotations

import logging
import time
from typing import Optional, Tuple

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


def detect_cameras(max_test: int = 10) -> list[int]:
    """Detect available camera IDs."""
    available = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
            cap.release()
    return available


class CameraWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray, float)
    status_changed = pyqtSignal(bool, str)

    def __init__(self, camera_id: int, fps: int, resolution: Tuple[int, int]) -> None:
        super().__init__()
        self.camera_id = camera_id
        self.fps = fps
        self.resolution = resolution
        self._running = True
        self.cap: Optional[cv2.VideoCapture] = None

    def run(self) -> None:
        logger.debug("Camera worker starting (id=%s)", self.camera_id)
        target_delay = 1 / max(self.fps, 1)
        consecutive_failures = 0
        max_failures = 10
        
        while self._running:
            if self.cap is None or not self.cap.isOpened():
                if self.cap:
                    self.cap.release()
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.status_changed.emit(False, f"Camera {self.camera_id} failed after {max_failures} attempts")
                        logger.error("Camera %s failed after %d attempts", self.camera_id, max_failures)
                        time.sleep(2.0)
                        consecutive_failures = 0
                    else:
                        self.status_changed.emit(False, f"Camera {self.camera_id} reconnecting... ({consecutive_failures}/{max_failures})")
                        time.sleep(1.0)
                    continue
                
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                consecutive_failures = 0
                self.status_changed.emit(True, "active")
                logger.debug("Camera %s connected", self.camera_id)

            start = time.perf_counter()
            ret, frame = self.cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.warning("Camera %s read failed %d times, attempting reconnect", self.camera_id, consecutive_failures)
                    self.status_changed.emit(False, f"Camera {self.camera_id} read failed, reconnecting...")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                    consecutive_failures = 0
                    time.sleep(0.5)
                else:
                    self.status_changed.emit(False, f"Camera {self.camera_id} no frame ({consecutive_failures}/{max_failures})")
                    time.sleep(0.1)
                continue

            consecutive_failures = 0
            timestamp = time.time()
            self.frame_ready.emit(frame, timestamp)
            elapsed = time.perf_counter() - start
            remaining = target_delay - elapsed
            if remaining > 0:
                self.msleep(int(remaining * 1000))

        self._cleanup()

    def stop(self) -> None:
        self._running = False

    def _cleanup(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.status_changed.emit(False, "stopped")
        logger.debug("Camera worker stopped (id=%s)", self.camera_id)


class CameraService(QObject):
    dtl_frame = pyqtSignal(np.ndarray, float)
    face_frame = pyqtSignal(np.ndarray, float)
    dtl_status = pyqtSignal(bool, str)
    face_status = pyqtSignal(bool, str)

    def __init__(self, dtl_id: int, face_id: int, fps: int, resolution: Tuple[int, int]):
        super().__init__()
        self.dtl_id = dtl_id
        self.face_id = face_id
        self.fps = fps
        self.resolution = resolution
        self.dtl_worker: Optional[CameraWorker] = None
        self.face_worker: Optional[CameraWorker] = None

    def update_camera_ids(self, dtl_id: int, face_id: int) -> None:
        """Update camera IDs (takes effect on next start)."""
        self.dtl_id = dtl_id
        self.face_id = face_id
        logger.debug("Camera IDs updated: DTL=%s, Face=%s", dtl_id, face_id)

    def start(self) -> None:
        if self.dtl_worker and self.dtl_worker.isRunning():
            return
        self.dtl_worker = CameraWorker(self.dtl_id, self.fps, self.resolution)
        self.face_worker = CameraWorker(self.face_id, self.fps, self.resolution)
        self.dtl_worker.frame_ready.connect(self.dtl_frame.emit)
        self.face_worker.frame_ready.connect(self.face_frame.emit)
        self.dtl_worker.status_changed.connect(self.dtl_status.emit)
        self.face_worker.status_changed.connect(self.face_status.emit)
        self.dtl_worker.start()
        self.face_worker.start()

    def stop(self) -> None:
        for attr in ("dtl_worker", "face_worker"):
            worker = getattr(self, attr)
            if worker:
                worker.stop()
                worker.wait()
                setattr(self, attr, None)


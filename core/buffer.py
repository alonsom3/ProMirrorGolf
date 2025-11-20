from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Deque, List

import numpy as np


@dataclass
class FrameRecord:
    frame: np.ndarray
    timestamp: float


class CircularBuffer:
    """Fixed-length buffer storing frames + timestamps."""

    def __init__(self, max_frames: int):
        self.max_frames = max_frames
        self._frames: Deque[FrameRecord] = collections.deque(maxlen=max_frames)

    def add(self, frame: np.ndarray, timestamp: float) -> None:
        # Copy frame to avoid reference issues when buffer is dumped
        self._frames.append(FrameRecord(frame.copy(), timestamp))

    def dump(self) -> List[FrameRecord]:
        return list(self._frames)

    def clear(self) -> None:
        self._frames.clear()


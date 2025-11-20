from __future__ import annotations

import asyncio
import logging
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from .shot_listener import ShotListener

logger = logging.getLogger(__name__)


class ShotListenerThread(QThread):
    shot_received = pyqtSignal(dict)

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._listener: Optional[ShotListener] = None

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._listener = ShotListener(self.host, self.port, self._on_shot)
        try:
            self._loop.run_until_complete(self._listener.start())
            logger.info("Shot listener started on %s:%d", self.host, self.port)
            try:
                self._loop.run_forever()
            finally:
                self._loop.run_until_complete(self._listener.stop())
        except OSError as e:
            if e.errno == 10048:  # Windows: Address already in use
                logger.error(
                    "Port %d is already in use. Another instance may be running, "
                    "or another application is using this port. "
                    "Shot detection will be disabled. To fix: close other instances or change the port in config.",
                    self.port
                )
            else:
                logger.error("Failed to start shot listener on %s:%d: %s", self.host, self.port, e)
        except Exception as e:
            logger.error("Unexpected error in shot listener: %s", e, exc_info=True)
        finally:
            self._loop.close()

    def stop(self) -> None:
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _on_shot(self, payload: dict) -> None:
        self.shot_received.emit(payload)


from __future__ import annotations

import ctypes
import logging
import sys
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def enable_high_resolution_timer(period_ms: int = 1) -> Optional[Tuple[ctypes.CDLL, int]]:
    """Increase Windows timer resolution to improve sleep/timer accuracy."""
    if not sys.platform.startswith("win"):
        return None

    try:
        winmm = ctypes.WinDLL("winmm")  # type: ignore[attr-defined]
        result = winmm.timeBeginPeriod(period_ms)
        if result != 0:
            logger.warning("timeBeginPeriod failed with code %s", result)
            return None

        logger.info("High resolution timer enabled (%d ms)", period_ms)
        return (winmm, period_ms)
    except Exception:
        logger.exception("Failed to enable high resolution timer")
        return None


def disable_high_resolution_timer(handle: Optional[Tuple[ctypes.CDLL, int]]) -> None:
    """Restore default timer resolution."""
    if not handle:
        return

    winmm, period_ms = handle
    try:
        result = winmm.timeEndPeriod(period_ms)
        if result != 0:
            logger.warning("timeEndPeriod failed with code %s", result)
        else:
            logger.info("High resolution timer disabled")
    except Exception:
        logger.exception("Failed to disable high resolution timer")


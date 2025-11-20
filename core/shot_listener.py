from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ShotListener:
    """Simple TCP JSON line listener for launch monitor data."""

    def __init__(self, host: str, port: int, on_shot: Callable[[dict], None]):
        self.host = host
        self.port = port
        self.on_shot = on_shot
        self._server: Optional[asyncio.base_events.Server] = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        addr = ", ".join(str(sock.getsockname()) for sock in self._server.sockets or [])
        logger.info("Shot listener running on %s", addr)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Shot listener stopped.")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.info("Shot client connected: %s", addr)
        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                try:
                    payload = json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError:
                    logger.debug("Bad shot payload: %s", line[:100])
                    continue
                self.on_shot(payload)
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info("Shot client disconnected: %s", addr)


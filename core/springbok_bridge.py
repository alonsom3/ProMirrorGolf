"""Bridge to intercept Springbok connector data and forward to GSPro and ProMirrorGolf.

The bridge listens on port 922 for Springbok connector connections, forwards data
to GSPro on port 921, and converts/forwards data to ProMirrorGolf on port 5556.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SpringbokBridge:
    """Bridge that intercepts Springbok connector data and forwards to both GSPro and ProMirrorGolf.
    
    Architecture:
        Springbok Connector → Bridge (listens on 922) → GSPro API Connect (connects to :921)
                                              └──────→ ProMirrorGolf (connects to :5556)
    
    The bridge intercepts Springbok on port 922, forwards unchanged to GSPro on port 921,
    and also converts and forwards to ProMirrorGolf on port 5556.
    """
    
    def __init__(
        self,
        listen_port: int = 922,
        gspro_host: str = "127.0.0.1",
        gspro_port: int = 921,
        promirror_host: str = "127.0.0.1",
        promirror_port: int = 5556,
    ) -> None:
        """Initialize the bridge.
        
        Args:
            listen_port: Port to listen on for Springbok data (default 922).
            gspro_host: GSPro API Connect host address.
            gspro_port: GSPro API Connect port (typically 921).
            promirror_host: ProMirrorGolf host address.
            promirror_port: ProMirrorGolf port (typically 5556).
        """
        self.listen_port = listen_port
        self.gspro_host = gspro_host
        self.gspro_port = gspro_port
        self.promirror_host = promirror_host
        self.promirror_port = promirror_port
        
        self._server: Optional[asyncio.base_events.Server] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Connection status tracking
        self._springbok_connected = False
        self._gspro_connected = False
        self._status_callbacks: list[Callable[[bool, bool], None]] = []
    
    async def start(self) -> None:
        """Start the bridge server."""
        if self._running:
            logger.warning("Bridge is already running")
            return
        
        self._server = await asyncio.start_server(
            self._handle_client,
            "127.0.0.1",
            self.listen_port
        )
        self._running = True
        addr = ", ".join(str(sock.getsockname()) for sock in self._server.sockets or [])
        logger.info("Springbok bridge started on %s", addr)
        logger.info("Forwarding to GSPro at %s:%d", self.gspro_host, self.gspro_port)
        logger.info("Forwarding to ProMirrorGolf at %s:%d", self.promirror_host, self.promirror_port)
        logger.info("Configure Springbok to connect to port %d", self.listen_port)
    
    async def stop(self) -> None:
        """Stop the bridge server."""
        if not self._running:
            return
        
        self._running = False
        if self._server:
            self._server.close()
            try:
                await asyncio.wait_for(self._server.wait_closed(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.debug("Server close timeout")
            logger.info("Springbok bridge stopped")
    
    def add_status_callback(self, callback: Callable[[bool, bool], None]) -> None:
        """Add a callback to be notified of connection status changes.
        
        Args:
            callback: Function that takes (springbok_connected, gspro_connected) as arguments.
        """
        self._status_callbacks.append(callback)
    
    def _notify_status(self) -> None:
        """Notify all status callbacks of current connection state."""
        for callback in self._status_callbacks:
            try:
                callback(self._springbok_connected, self._gspro_connected)
            except Exception as e:
                logger.debug("Error in status callback: %s", e)
    
    async def _handle_client(
        self,
        springbok_reader: asyncio.StreamReader,
        springbok_writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming connection from Springbok connector."""
        addr = springbok_writer.get_extra_info("peername")
        logger.info("Springbok connector connected from %s", addr)
        self._springbok_connected = True
        self._notify_status()
        
        try:
            # Connect to GSPro
            logger.debug("Connecting to GSPro API Connect at %s:%d", self.gspro_host, self.gspro_port)
            gspro_reader, gspro_writer = await asyncio.wait_for(
                asyncio.open_connection(self.gspro_host, self.gspro_port),
                timeout=5.0
            )
            logger.info("Connected to GSPro API Connect")
            self._gspro_connected = True
            self._notify_status()
            
            # Forward data bidirectionally and also to ProMirrorGolf
            await self._forward_bidirectional(
                springbok_reader,
                springbok_writer,
                gspro_reader,
                gspro_writer
            )
            
        except asyncio.TimeoutError:
            logger.error("Failed to connect to GSPro (timeout)")
            logger.error("Make sure GSPro API Connect is running on %s:%d", self.gspro_host, self.gspro_port)
            self._gspro_connected = False
            self._notify_status()
            springbok_writer.close()
            await springbok_writer.wait_closed()
        except ConnectionRefusedError:
            logger.error("Failed to connect to GSPro (connection refused)")
            logger.error("Make sure GSPro API Connect is running on %s:%d", self.gspro_host, self.gspro_port)
            self._gspro_connected = False
            self._notify_status()
            springbok_writer.close()
            await springbok_writer.wait_closed()
        except Exception as e:
            logger.error("Error handling Springbok connection: %s", e, exc_info=True)
            self._gspro_connected = False
            self._notify_status()
            springbok_writer.close()
            await springbok_writer.wait_closed()
        finally:
            # Connection closed
            self._springbok_connected = False
            self._gspro_connected = False
            self._notify_status()
    
    async def _forward_bidirectional(
        self,
        springbok_reader: asyncio.StreamReader,
        springbok_writer: asyncio.StreamWriter,
        gspro_reader: asyncio.StreamReader,
        gspro_writer: asyncio.StreamWriter
    ) -> None:
        """Forward data bidirectionally between Springbok and GSPro, and to ProMirrorGolf."""
        
        async def springbok_to_gspro():
            """Forward Springbok → GSPro and to ProMirrorGolf."""
            try:
                while True:
                    data = await springbok_reader.read(4096)
                    if not data:
                        logger.debug("Springbok connection closed")
                        break
                    
                    gspro_writer.write(data)
                    await gspro_writer.drain()
                    await self._forward_to_promirror(data)
                    
            except Exception as e:
                logger.error("Error forwarding Springbok → GSPro: %s", e, exc_info=True)
        
        async def gspro_to_springbok():
            """Forward GSPro → Springbok responses."""
            try:
                while True:
                    data = await gspro_reader.read(4096)
                    if not data:
                        logger.debug("GSPro connection closed")
                        break
                    springbok_writer.write(data)
                    await springbok_writer.drain()
                    
            except Exception as e:
                logger.error("Error forwarding GSPro → Springbok: %s", e, exc_info=True)
        
        try:
            await asyncio.gather(
                springbok_to_gspro(),
                gspro_to_springbok(),
                return_exceptions=True
            )
        finally:
            springbok_writer.close()
            gspro_writer.close()
            await springbok_writer.wait_closed()
            await gspro_writer.wait_closed()
    
    async def _forward_to_promirror(self, data: bytes) -> None:
        """Parse Springbok data and forward to ProMirrorGolf.
        
        Args:
            data: Raw data from Springbok connector.
        """
        try:
            try:
                text = data.decode("utf-8").strip()
            except UnicodeDecodeError:
                logger.debug("Could not decode data as UTF-8: %s", data[:100])
                return
            
            try:
                springbok_data = json.loads(text)
            except json.JSONDecodeError:
                logger.debug("Data is not JSON: %s", text[:200])
                return
            
            promirror_data = self._convert_springbok_to_promirror(springbok_data)
            if promirror_data:
                await self._send_json_to_promirror(promirror_data)
                
        except Exception as e:
            logger.error("Error forwarding to ProMirrorGolf: %s", e, exc_info=True)
    
    def _convert_springbok_to_promirror(self, springbok_data: dict) -> Optional[dict]:
        """Convert Springbok JSON format to ProMirrorGolf format.
        
        Args:
            springbok_data: JSON data from Springbok connector.
        
        Returns:
            Converted data in ProMirrorGolf format, or None if conversion fails.
        """
        converted = {}
        ball_data = springbok_data.get("BallData", {})
        if ball_data:
            if "Speed" in ball_data:
                converted["BallSpeed"] = ball_data["Speed"]
            if "TotalSpin" in ball_data:
                converted["TotalSpin"] = ball_data["TotalSpin"]
            if "Backspin" in ball_data:
                converted["BackSpin"] = ball_data["Backspin"]
            if "SideSpin" in ball_data:
                converted["SideSpin"] = ball_data["SideSpin"]
            if "HLA" in ball_data:
                converted["LaunchDirection"] = ball_data["HLA"]
            if "VLA" in ball_data:
                converted["LaunchAngle"] = ball_data["VLA"]
            if "CarryDistance" in ball_data:
                converted["CarryDistance"] = ball_data["CarryDistance"]
            # Note: SpinAxis is not currently in ProMirrorGolf schema, but we could add it
        
        # Extract ClubData fields
        club_data = springbok_data.get("ClubData", {})
        if club_data:
            if "Speed" in club_data:
                converted["ClubSpeed"] = club_data["Speed"]
            if "AngleOfAttack" in club_data:
                converted["AttackAngle"] = club_data["AngleOfAttack"]
            if "FaceToTarget" in club_data:
                converted["FaceAngle"] = club_data["FaceToTarget"]
            if "Path" in club_data:
                converted["ClubPath"] = club_data["Path"]
        
        return converted if converted else None
    
    async def _send_json_to_promirror(self, shot_data: dict) -> None:
        """Send JSON data to ProMirrorGolf.
        
        Args:
            shot_data: Shot data dictionary in ProMirrorGolf format.
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.promirror_host, self.promirror_port),
                timeout=2.0
            )
            json_line = json.dumps(shot_data) + "\n"
            writer.write(json_line.encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.debug("Error sending to ProMirrorGolf: %s", e)


class SpringbokBridgeThread:
    """Thread wrapper for SpringbokBridge to run in background."""
    
    def __init__(self, bridge: SpringbokBridge) -> None:
        """Initialize bridge thread.
        
        Args:
            bridge: SpringbokBridge instance to run.
        """
        self.bridge = bridge
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._status_callbacks: list[Callable[[bool, bool], None]] = []
    
    def add_status_callback(self, callback: Callable[[bool, bool], None]) -> None:
        """Add callback for connection status changes.
        
        Args:
            callback: Function that takes (springbok_connected, gspro_connected).
        """
        self._status_callbacks.append(callback)
        self.bridge.add_status_callback(self._on_status_changed)
    
    def _on_status_changed(self, springbok_connected: bool, gspro_connected: bool) -> None:
        """Handle status change from bridge and forward to callbacks."""
        for callback in self._status_callbacks:
            try:
                callback(springbok_connected, gspro_connected)
            except Exception as e:
                logger.debug("Error in status callback: %s", e)
    
    def start(self) -> None:
        """Start the bridge in a background thread."""
        import threading
        
        def run_bridge():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self.bridge.start())
                # Run until stop is called
                while not self._stop_event.is_set():
                    try:
                        self._loop.run_until_complete(asyncio.sleep(0.1))
                    except RuntimeError:
                        # Loop may have been stopped
                        break
            except Exception as e:
                logger.error("Bridge thread error: %s", e, exc_info=True)
            finally:
                # Properly stop the bridge and close connections
                try:
                    if self._loop and not self._loop.is_closed():
                        # Stop the bridge server
                        try:
                            self._loop.run_until_complete(self.bridge.stop())
                        except Exception as e:
                            logger.debug("Error stopping bridge: %s", e)
                        
                        # Cancel all pending tasks
                        try:
                            pending = [t for t in asyncio.all_tasks(self._loop) if not t.done()]
                            for task in pending:
                                task.cancel()
                            # Wait for tasks to complete cancellation (with timeout)
                            if pending:
                                self._loop.run_until_complete(
                                    asyncio.wait_for(
                                        asyncio.gather(*pending, return_exceptions=True),
                                        timeout=1.0
                                    )
                                )
                        except (asyncio.TimeoutError, RuntimeError):
                            # Tasks may not complete in time, that's okay
                            pass
                except Exception as e:
                    logger.debug("Error during bridge cleanup: %s", e)
                finally:
                    if self._loop and not self._loop.is_closed():
                        try:
                            self._loop.close()
                        except Exception:
                            pass
        
        self._thread = threading.Thread(target=run_bridge, daemon=True)
        self._thread.start()
        logger.info("Springbok bridge thread started")
    
    def stop(self) -> None:
        """Stop the bridge."""
        self._stop_event.set()
        if self._loop and not self._loop.is_closed():
            # Schedule stop on the event loop
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                # Loop may already be closed
                pass
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info("Springbok bridge thread stopped")

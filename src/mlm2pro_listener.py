"""
MLM2PRO Launch Monitor Listener
Integrates with the MLM2PRO connector to detect shots and capture data
"""

import asyncio
import json
import socket
import struct
import logging
from typing import Dict, Optional
from datetime import datetime
import subprocess
import time

logger = logging.getLogger(__name__)


class LaunchMonitorListener:
    """
    Listens for shot data from MLM2PRO via the connector
    Supports both the springbok and OpenGolfSim connectors
    """
    
    def __init__(self, connector_path: str, connector_type: str = "opengolfsim"):
        self.connector_path = connector_path
        self.connector_type = connector_type
        self.connector_process = None
        
        # UDP socket for receiving data
        self.sock = None
        self.listen_port = 5555  # Default port, adjust based on connector config
        
        # State
        self.is_listening = False
        self.last_shot_time = 0
        self.shot_queue = asyncio.Queue()
        
        # Shot detection parameters
        self.min_shot_interval = 3.0  # Minimum seconds between shots
        
        logger.info(f"LaunchMonitor initialized: {connector_type}")
    
    def start_connector(self):
        """Start the MLM2PRO connector process"""
        try:
            # Start the connector as a subprocess
            self.connector_process = subprocess.Popen(
                [self.connector_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("MLM2PRO connector started")
            time.sleep(2)  # Give it time to initialize
        except Exception as e:
            logger.error(f"Failed to start connector: {e}")
            raise
    
    def start_listening(self):
        """Start listening for shot data"""
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        # Start connector if not already running
        if not self.connector_process:
            self.start_connector()
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', self.listen_port))
        self.sock.setblocking(False)
        
        self.is_listening = True
        
        # Start listening loop
        asyncio.create_task(self._listen_loop())
        
        logger.info(f"Listening for shots on port {self.listen_port}")
    
    async def _listen_loop(self):
        """Main listening loop for shot data"""
        while self.is_listening:
            try:
                # Non-blocking receive
                data, addr = await asyncio.get_event_loop().sock_recvfrom(self.sock, 4096)
                
                if data:
                    shot_data = self._parse_shot_data(data)
                    
                    if shot_data and self._is_valid_shot(shot_data):
                        logger.info(f"Shot detected: {shot_data.get('BallSpeed', 0)} mph ball speed")
                        await self.shot_queue.put(shot_data)
                        self.last_shot_time = time.time()
                        
            except Exception as e:
                # No data available, continue
                await asyncio.sleep(0.01)
    
    def _parse_shot_data(self, data: bytes) -> Optional[Dict]:
        """
        Parse shot data from MLM2PRO connector
        Format depends on connector type
        """
        try:
            if self.connector_type == "opengolfsim":
                return self._parse_opengolfsim_format(data)
            else:
                return self._parse_springbok_format(data)
        except Exception as e:
            logger.error(f"Error parsing shot data: {e}")
            return None
    
    def _parse_opengolfsim_format(self, data: bytes) -> Dict:
        """
        Parse OpenGolfSim connector format
        Based on their API specification
        """
        # OpenGolfSim sends JSON data
        json_str = data.decode('utf-8')
        shot_data = json.loads(json_str)
        
        # Normalize field names
        normalized = {
            'BallSpeed': shot_data.get('BallData', {}).get('Speed'),
            'LaunchAngle': shot_data.get('BallData', {}).get('VerticalAngle'),
            'LaunchDirection': shot_data.get('BallData', {}).get('HorizontalAngle'),
            'SpinRate': shot_data.get('BallData', {}).get('TotalSpin'),
            'BackSpin': shot_data.get('BallData', {}).get('BackSpin'),
            'SideSpin': shot_data.get('BallData', {}).get('SideSpin'),
            'ClubSpeed': shot_data.get('ClubData', {}).get('Speed'),
            'ClubPath': shot_data.get('ClubData', {}).get('Path'),
            'FaceAngle': shot_data.get('ClubData', {}).get('FaceAngle'),
            'FaceToPath': shot_data.get('ClubData', {}).get('FaceToPath'),
            'CarryDistance': shot_data.get('ShotData', {}).get('CarryDistance'),
            'TotalDistance': shot_data.get('ShotData', {}).get('TotalDistance'),
            'Timestamp': datetime.now().isoformat(),
            'Club': shot_data.get('Club', 'Unknown')
        }
        
        return normalized
    
    def _parse_springbok_format(self, data: bytes) -> Dict:
        """
        Parse springbok connector format
        Uses binary protocol
        """
        # Springbok uses a binary format - struct unpacking
        # Format: Header (4 bytes) + Data fields
        
        if len(data) < 64:
            return None
        
        # Unpack binary data (adjust format string based on actual protocol)
        unpacked = struct.unpack('=4sfffffffffffffff', data[:64])
        
        normalized = {
            'BallSpeed': unpacked[1],
            'LaunchAngle': unpacked[2],
            'LaunchDirection': unpacked[3],
            'SpinRate': unpacked[4],
            'BackSpin': unpacked[5],
            'SideSpin': unpacked[6],
            'ClubSpeed': unpacked[7],
            'ClubPath': unpacked[8],
            'FaceAngle': unpacked[9],
            'FaceToPath': unpacked[10],
            'CarryDistance': unpacked[11],
            'TotalDistance': unpacked[12],
            'Timestamp': datetime.now().isoformat(),
            'Club': 'Unknown'
        }
        
        return normalized
    
    def _is_valid_shot(self, shot_data: Dict) -> bool:
        """
        Validate shot data to filter out noise
        """
        # Check minimum time between shots
        if time.time() - self.last_shot_time < self.min_shot_interval:
            logger.debug("Shot too soon after previous shot, ignoring")
            return False
        
        # Check for valid ball speed (must be > 0)
        ball_speed = shot_data.get('BallSpeed', 0)
        if ball_speed is None or ball_speed <= 0:
            logger.debug("Invalid ball speed, ignoring")
            return False
        
        # Check for reasonable values
        if ball_speed > 250:  # 250+ mph is unrealistic
            logger.debug("Ball speed too high, ignoring")
            return False
        
        return True
    
    async def wait_for_shot(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Wait for the next shot detection
        
        Args:
            timeout: Maximum seconds to wait (None = wait forever)
        
        Returns:
            Shot data dictionary or None if timeout
        """
        try:
            if timeout:
                shot_data = await asyncio.wait_for(self.shot_queue.get(), timeout=timeout)
            else:
                shot_data = await self.shot_queue.get()
            
            return shot_data
        except asyncio.TimeoutError:
            return None
    
    def stop_listening(self):
        """Stop listening and cleanup"""
        self.is_listening = False
        
        if self.sock:
            self.sock.close()
            self.sock = None
        
        if self.connector_process:
            self.connector_process.terminate()
            self.connector_process.wait(timeout=5)
            self.connector_process = None
        
        logger.info("LaunchMonitor listener stopped")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'is_listening': self.is_listening,
            'connector_running': self.connector_process is not None,
            'last_shot_time': self.last_shot_time,
            'pending_shots': self.shot_queue.qsize()
        }


# Alternative: File-based integration if UDP doesn't work
class FileBasedLaunchMonitorListener:
    """
    Alternative approach: Monitor a shared file written by the connector
    More reliable for some connector setups
    """
    
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.is_listening = False
        self.last_modified_time = 0
        self.shot_queue = asyncio.Queue()
    
    def start_listening(self):
        """Start monitoring the data file"""
        self.is_listening = True
        asyncio.create_task(self._monitor_file())
        logger.info(f"Monitoring file: {self.data_file_path}")
    
    async def _monitor_file(self):
        """Monitor file for changes"""
        import os
        
        while self.is_listening:
            try:
                # Check if file was modified
                if os.path.exists(self.data_file_path):
                    modified_time = os.path.getmtime(self.data_file_path)
                    
                    if modified_time > self.last_modified_time:
                        # File was updated, read new data
                        with open(self.data_file_path, 'r') as f:
                            data = json.load(f)
                        
                        await self.shot_queue.put(data)
                        self.last_modified_time = modified_time
                        logger.info("New shot data detected from file")
                
            except Exception as e:
                logger.error(f"Error monitoring file: {e}")
            
            await asyncio.sleep(0.1)  # Check every 100ms
    
    async def wait_for_shot(self, timeout: Optional[float] = None):
        """Wait for next shot"""
        try:
            if timeout:
                return await asyncio.wait_for(self.shot_queue.get(), timeout=timeout)
            else:
                return await self.shot_queue.get()
        except asyncio.TimeoutError:
            return None
    
    def stop_listening(self):
        """Stop monitoring"""
        self.is_listening = False
        logger.info("File monitoring stopped")


# Testing
async def test_listener():
    """Test the launch monitor listener"""
    listener = LaunchMonitorListener(
        connector_path="C:/MLM2PRO-Connector/connector.exe",
        connector_type="opengolfsim"
    )
    
    listener.start_listening()
    
    print("Waiting for shots... (hit a ball)")
    
    # Wait for 3 shots
    for i in range(3):
        shot = await listener.wait_for_shot(timeout=60)
        if shot:
            print(f"\nShot {i+1}:")
            print(f"  Ball Speed: {shot.get('BallSpeed')} mph")
            print(f"  Club Speed: {shot.get('ClubSpeed')} mph")
            print(f"  Launch Angle: {shot.get('LaunchAngle')}°")
            print(f"  Carry: {shot.get('CarryDistance')} yards")
        else:
            print("Timeout waiting for shot")
    
    listener.stop_listening()


if __name__ == "__main__":
    asyncio.run(test_listener())
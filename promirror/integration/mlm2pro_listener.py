"""
MLM2PRO Launch Monitor Integration
Listens for shot data from the MLM2PRO connector and triggers swing analysis
"""

import asyncio
import socket
import json
import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LaunchMonitorListener:
    """
    Listens for shot data from MLM2PRO via the OpenGolfSim connector.
    Automatically detects shots and queues them for analysis.
    """
    
    def __init__(self, listen_port: int = 5555, connector_type: str = "opengolfsim"):
        self.listen_port = listen_port
        self.connector_type = connector_type
        self.sock = None
        self.is_listening = False
        self.shot_queue = asyncio.Queue()
        self.last_shot_time = 0
        self.min_shot_interval = 3.0  # Minimum seconds between shots
        
        logger.info(f"LaunchMonitorListener initialized (port: {listen_port})")
    
    def start_listening(self):
        """Start listening for shot data from the connector"""
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        try:
            # Create UDP socket for receiving shot data
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('127.0.0.1', self.listen_port))
            self.sock.setblocking(False)
            
            self.is_listening = True
            
            # Start async listening loop
            asyncio.create_task(self._listen_loop())
            
            logger.info(f"✓ Listening for shots on port {self.listen_port}")
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            raise
    
    async def _listen_loop(self):
        """Main event loop - waits for shot data from connector"""
        logger.info("Shot detection loop started - waiting for balls...")
        
        while self.is_listening:
            try:
                # Non-blocking receive
                data, addr = await asyncio.get_event_loop().sock_recvfrom(self.sock, 4096)
                
                if data:
                    # Parse the shot data
                    shot_data = self._parse_shot_data(data)
                    
                    # Validate and queue if good
                    if shot_data and self._is_valid_shot(shot_data):
                        logger.info(f"✓ Shot detected: {shot_data.get('ball_speed', 0):.1f} mph")
                        await self.shot_queue.put(shot_data)
                        self.last_shot_time = time.time()
                        
            except Exception as e:
                # No data available, continue
                await asyncio.sleep(0.01)
    
    def _parse_shot_data(self, data: bytes) -> Optional[Dict]:
        """
        Parse shot data from MLM2PRO connector.
        Handles both OpenGolfSim and Springbok formats.
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
        """Parse OpenGolfSim connector JSON format"""
        json_str = data.decode('utf-8')
        shot_data = json.loads(json_str)
        
        # Normalize field names to match your system
        return {
            'ball_speed': shot_data.get('BallData', {}).get('Speed'),
            'club_speed': shot_data.get('ClubData', {}).get('Speed'),
            'launch_angle': shot_data.get('BallData', {}).get('VerticalAngle'),
            'launch_direction': shot_data.get('BallData', {}).get('HorizontalAngle'),
            'spin_rate': shot_data.get('BallData', {}).get('TotalSpin'),
            'club_path': shot_data.get('ClubData', {}).get('Path'),
            'face_angle': shot_data.get('ClubData', {}).get('FaceAngle'),
            'carry_distance': shot_data.get('ShotData', {}).get('CarryDistance'),
            'total_distance': shot_data.get('ShotData', {}).get('TotalDistance'),
            'timestamp': datetime.now().isoformat(),
            'club': shot_data.get('Club', 'Unknown')
        }
    
    def _parse_springbok_format(self, data: bytes) -> Dict:
        """Parse Springbok connector binary format"""
        import struct
        
        if len(data) < 64:
            return None
        
        # Unpack binary data (adjust format based on actual protocol)
        unpacked = struct.unpack('=4sfffffffffffffff', data[:64])
        
        return {
            'ball_speed': unpacked[1],
            'club_speed': unpacked[7],
            'launch_angle': unpacked[2],
            'launch_direction': unpacked[3],
            'spin_rate': unpacked[4],
            'club_path': unpacked[8],
            'face_angle': unpacked[9],
            'carry_distance': unpacked[11],
            'total_distance': unpacked[12],
            'timestamp': datetime.now().isoformat(),
            'club': 'Unknown'
        }
    
    def _is_valid_shot(self, shot_data: Dict) -> bool:
        """
        Validate shot data to filter out noise and bad readings.
        
        Returns:
            True if this looks like a real shot, False otherwise
        """
        # Check minimum time between shots (prevent duplicate detections)
        if time.time() - self.last_shot_time < self.min_shot_interval:
            logger.debug("Shot too soon after previous, ignoring")
            return False
        
        # Check for valid ball speed
        ball_speed = shot_data.get('ball_speed', 0)
        if ball_speed is None or ball_speed <= 0:
            logger.debug("Invalid ball speed, ignoring")
            return False
        
        # Check for reasonable values (no 250+ mph shots!)
        if ball_speed > 250:
            logger.debug(f"Ball speed too high ({ball_speed} mph), ignoring")
            return False
        
        return True
    
    async def wait_for_shot(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Wait for the next shot to be detected.
        
        Args:
            timeout: Maximum seconds to wait (None = wait forever)
            
        Returns:
            Shot data dictionary, or None if timeout
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
        
        logger.info("Launch monitor listener stopped")
    
    def get_status(self) -> Dict:
        """Get current listener status"""
        return {
            'is_listening': self.is_listening,
            'last_shot_time': self.last_shot_time,
            'pending_shots': self.shot_queue.qsize(),
            'port': self.listen_port
        }


class FileBasedListener:
    """
    Alternative: Monitor a file written by connector instead of UDP.
    Use this if the UDP approach doesn't work with your connector setup.
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
                if os.path.exists(self.data_file_path):
                    modified_time = os.path.getmtime(self.data_file_path)
                    
                    if modified_time > self.last_modified_time:
                        # File updated - read new data
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


# Test function
async def test_listener():
    """Test the launch monitor listener"""
    print("Testing Launch Monitor Listener...")
    print("Make sure your MLM2PRO connector is running!")
    print()
    
    listener = LaunchMonitorListener(listen_port=5555)
    listener.start_listening()
    
    print("Waiting for 3 shots... (hit some balls)")
    print()
    
    for i in range(3):
        print(f"Waiting for shot {i+1}...")
        shot = await listener.wait_for_shot(timeout=60)
        
        if shot:
            print(f"✓ Shot {i+1} detected:")
            print(f"  Ball Speed: {shot.get('ball_speed', 0):.1f} mph")
            print(f"  Club Speed: {shot.get('club_speed', 0):.1f} mph")
            print(f"  Carry: {shot.get('carry_distance', 0):.1f} yards")
            print()
        else:
            print(f"✗ Timeout waiting for shot {i+1}")
            break
    
    listener.stop_listening()
    print("Test complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_listener())

import serial
import time
from typing import Optional

class SprinklerCommunication:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600):
        """Initialize the communication with Arduino
        
        Args:
            port (str): Serial port where Arduino is connected
            baudrate (int): Communication speed
        """
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        


    def connect(self) -> bool:
        """Establish connection with the Arduino"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Wait for Arduino to reset
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
            


    def disconnect(self):
        """Close the serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            


    def activate_sprinkler(self, zone: str, duration: int) -> bool:
        """Send command to activate a specific sprinkler
        
        Args:
            zone (str): The sprinkler zone to activate
            duration (int): Duration in seconds
            
        Returns:
            bool: True if command was sent successfully
        """
        if not self.serial or not self.serial.is_open:
            print("No connection to Arduino")
            return False
            
        try:
            # Format: "ZONE:DURATION\n"
            command = f"{zone}:{duration}\n"
            self.serial.write(command.encode())
            
            # Wait for acknowledgment
            response = self.serial.readline().decode().strip()
            return response == "OK"
            
        except serial.SerialException as e:
            print(f"Failed to send command: {e}")
            return False

          
            
    def get_status(self) -> dict:
        """Get the status of all sprinklers
        
        Returns:
            dict: Status of each sprinkler zone
        """
        if not self.serial or not self.serial.is_open:
            return {}
            
        try:
            self.serial.write(b"STATUS\n")
            response = self.serial.readline().decode().strip()
            
            # Parse response format: "zone1:status,zone2:status,..."
            status = {}
            for zone_status in response.split(','):
                if ':' in zone_status:
                    zone, state = zone_status.split(':')
                    status[zone] = state == '1'
            return status
            
        except serial.SerialException as e:
            print(f"Failed to get status: {e}")
            return {} 
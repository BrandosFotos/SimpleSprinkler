import requests
import hashlib
from typing import Dict, List, Optional
import time
import json
import os
import re

class OpenSprinklerAPI:
    @classmethod
    def from_config(cls, config_file: str = "config.json") -> "OpenSprinklerAPI":
        """Create an instance from a config file
        
        Args:
            config_file (str): Path to config file
            
        Returns:
            OpenSprinklerAPI: New instance
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file {config_file} not found")
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        os_config = config.get('opensprinkler', {})
        return cls(
            host=os_config.get('host', '192.168.1.15'),
            password=os_config.get('password', 'opendoor'),
            port=os_config.get('port', 80)
        )

    def __init__(self, host: str, password: str, port: int = 80):
        """Initialize OpenSprinkler API connection
        
        Args:
            host (str): IP address or hostname of OpenSprinkler device
            password (str): Device password
            port (int): Port number (default 80)
        """
        self.host = host
        self.password = password
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
    def _get_password_hash(self) -> str:
        """Get MD5 hash of password for API authentication"""
        return hashlib.md5(self.password.encode()).hexdigest()
        
    def _is_generic_station_name(self, name: str) -> bool:
        """Check if a station name is generic (S + numbers)
        
        Args:
            name (str): Station name to check
            
        Returns:
            bool: True if the name is generic
        """
        # Pattern matches: Starts with 'S' or 's', followed by only numbers
        pattern = r'^[Ss]\d+$'
        return bool(re.match(pattern, name.strip()))
        
    def get_station_names(self) -> List[str]:
        """Get list of all meaningful station names (excluding generic ones)"""
        response = requests.get(f"{self.base_url}/jn?pw={self._get_password_hash()}")
        if response.ok:
            data = response.json()
            all_names = data.get("snames", [])
            # Filter out generic names and empty strings
            return [name for name in all_names 
                   if name.strip() and not self._is_generic_station_name(name)]
        return []
        
    def get_station_status(self) -> List[bool]:
        """Get status of all stations (on/off)"""
        response = requests.get(f"{self.base_url}/js?pw={self._get_password_hash()}")
        if response.ok:
            data = response.json()
            all_status = data.get("sn", [])
            
            # Get all station names to know which ones to filter
            response_names = requests.get(f"{self.base_url}/jn?pw={self._get_password_hash()}")
            if response_names.ok:
                names_data = response_names.json()
                all_names = names_data.get("snames", [])
                
                # Create list of indices for non-generic stations
                valid_indices = [i for i, name in enumerate(all_names) 
                               if name.strip() and not self._is_generic_station_name(name)]
                
                # Return status only for non-generic stations
                return [all_status[i] for i in valid_indices if i < len(all_status)]
            
        return []
        
    def activate_station(self, station_id: int, duration: int) -> bool:
        """Activate a specific station
        
        Args:
            station_id (int): Station ID (0-based)
            duration (int): Duration in seconds
            
        Returns:
            bool: True if successful
        """
        url = f"{self.base_url}/cm?pw={self._get_password_hash()}&sid={station_id}&en=1&t={duration}"
        response = requests.get(url)
        return response.ok
        
    def deactivate_station(self, station_id: int) -> bool:
        """Deactivate a specific station
        
        Args:
            station_id (int): Station ID (0-based)
            
        Returns:
            bool: True if successful
        """
        url = f"{self.base_url}/cm?pw={self._get_password_hash()}&sid={station_id}&en=0"
        response = requests.get(url)
        return response.ok
        
    def get_all_data(self) -> Dict:
        """Get all OpenSprinkler data including settings and status"""
        response = requests.get(f"{self.base_url}/ja?pw={self._get_password_hash()}")
        if response.ok:
            return response.json()
        return {} 
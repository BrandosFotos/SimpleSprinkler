import time
from datetime import datetime
import json
import os
from opensprinkler_api import OpenSprinklerAPI
import requests
import logging
import RPi.GPIO as GPIO

# Set up logging with custom formatter
class CustomFormatter(logging.Formatter):
    """Custom formatter with different colors and separators for different log levels"""
    
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "DEBUG: %(message)s" + reset,
        logging.INFO: blue + "INFO: %(message)s" + reset,
        logging.WARNING: yellow + "WARNING: %(message)s" + reset,
        logging.ERROR: red + "ERROR: %(message)s" + reset,
        logging.CRITICAL: bold_red + "CRITICAL: %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Set up logger
logger = logging.getLogger("SprinklerControl")
logger.setLevel(logging.INFO)

# Create console handler with custom formatter
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

def log_separator(message=""):
    """Print a separator line in the logs"""
    if message:
        logger.info(f"\n{'='*20} {message} {'='*20}\n")
    else:
        logger.info("\n" + "="*60 + "\n")

# GPIO Configuration
BUTTON_PINS = {
    0: 26,  # GPIO 26 (Physical pin 37) - Station 0
    1: 6,   # GPIO 6  (Physical pin 31) - Station 1
    2: 13,  # GPIO 13 (Physical pin 33) - Station 2
    3: 19,  # GPIO 19 (Physical pin 35) - Station 3
}
DEBOUNCE_TIME = 300  # Debounce time in milliseconds
DEFAULT_DURATION = 300  # Default duration in seconds (5 minutes)

class SprinklerControl:
    def __init__(self):
        try:
            log_separator("Initializing Sprinkler Control System")
            
            # Initialize OpenSprinkler API from config
            self.api = OpenSprinklerAPI.from_config()
            
            # Get refresh interval from config
            with open("config.json", 'r') as f:
                config = json.load(f)
                self.refresh_interval = config['opensprinkler'].get('refresh_interval', 1)
                
            # Initialize GPIO
            self.setup_gpio()
            
        except FileNotFoundError:
            logger.error("config.json not found. Please create it with your OpenSprinkler settings.")
            raise
        except json.JSONDecodeError:
            logger.error("config.json is not valid JSON. Please check the format.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize: {str(e)}")
            raise
        
        # Initialize variables
        self.active_sprinklers = {}
        self.station_names = []
        self.station_indices = {}  # Maps display index to actual station index
        self.last_button_press = {pin: 0 for pin in BUTTON_PINS.values()}  # For debouncing
        self.load_stations()
        log_separator("Initialization Complete")

    def setup_gpio(self):
        """Set up GPIO pins"""
        log_separator("Setting up GPIO")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Use BCM numbering
        
        # Set up each button with pull-up resistor
        for station, pin in BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, 
                                callback=self.button_callback, 
                                bouncetime=DEBOUNCE_TIME)
            logger.info(f"Station {station}: GPIO {pin} configured")
        log_separator("GPIO Setup Complete")

    def button_callback(self, channel):
        """Callback function for button press"""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Find which station this button corresponds to
        station = None
        for s, pin in BUTTON_PINS.items():
            if pin == channel:
                station = s
                break
                
        if station is None:
            logger.error(f"Unknown button press on GPIO {channel}")
            return
            
        # Debounce check
        if (current_time - self.last_button_press[channel]) > DEBOUNCE_TIME:
            self.last_button_press[channel] = current_time
            log_separator(f"Button Press - Station {station}")
            
            # Check if station is active
            if station in self.active_sprinklers:
                logger.info(f"Turning OFF station {station}")
                self.toggle_station(station)  # Turn off
            else:
                logger.info(f"Turning ON station {station} for {DEFAULT_DURATION} seconds")
                self.toggle_station(station, DEFAULT_DURATION)  # Turn on with default duration

    def load_stations(self):
        """Load station names from OpenSprinkler"""
        log_separator("Loading Stations")
        # Get all station names to map indices
        response = requests.get(f"{self.api.base_url}/jn?pw={self.api._get_password_hash()}")
        if response.ok:
            all_names = response.json().get("snames", [])
            # Create mapping of display index to actual station index
            display_idx = 0
            for actual_idx, name in enumerate(all_names):
                if name.strip() and not self.api._is_generic_station_name(name):
                    self.station_indices[display_idx] = actual_idx
                    self.station_names.append(name)
                    display_idx += 1
        logger.info("Available stations:")
        for idx, name in enumerate(self.station_names):
            logger.info(f"Station {idx}: {name}")
        log_separator("Stations Loaded")

    def toggle_station(self, display_id, duration=0):
        """Toggle a station on/off"""
        if not 0 <= display_id < len(self.station_names):
            logger.error(f"Invalid station ID: {display_id}")
            return False

        station_name = self.station_names[display_id]
        station_id = self.station_indices[display_id]

        if display_id in self.active_sprinklers:
            # Turn off the station
            if self.api.deactivate_station(station_id):
                del self.active_sprinklers[display_id]
                logger.info(f"Successfully turned off {station_name}")
                return True
        else:
            # Turn on the station
            if duration <= 0:
                logger.error("Please provide a duration greater than 0 seconds")
                return False
                
            if self.api.activate_station(station_id, duration):
                self.active_sprinklers[display_id] = time.time() + duration
                logger.info(f"Successfully activated {station_name} for {duration} seconds")
                return True
        return False

    def get_station_status(self):
        """Get the current status of all stations"""
        log_separator("Station Status")
        try:
            status = self.api.get_station_status()
            for display_idx, name in enumerate(self.station_names):
                if display_idx < len(status):
                    state = "ON" if status[display_idx] else "OFF"
                    logger.info(f"Station {display_idx} ({name}): {state}")
            return status
        except Exception as e:
            logger.error(f"Error getting station status: {e}")
            return None

def main():
    try:
        controller = SprinklerControl()
        log_separator("System Ready")
        logger.info("Button configuration:")
        for station, pin in BUTTON_PINS.items():
            logger.info(f"Station {station}: GPIO {pin}")
        logger.info(f"Default duration: {DEFAULT_DURATION} seconds")
        log_separator("Running")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        log_separator("Shutdown Initiated")
        logger.info("Shutting down Sprinkler Control System")
        GPIO.cleanup()
        log_separator("Shutdown Complete")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        GPIO.cleanup()

if __name__ == "__main__":
    main() 
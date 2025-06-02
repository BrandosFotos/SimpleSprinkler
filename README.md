# OpenSprinkler Control System

**What is it?**
A Python-based control system for OpenSprinkler irrigation controllers with a user-friendly GUI interface.



**Why create this, when you can just use the opensprinkler web gui?**
I made this for my parents and grandparents who love to garden in thier off-time and want a simple, physical button(s), to water their garden. 

## Features

- Control multiple irrigation zones concurrently
- Real-time status monitoring with visual feedback
- Easy configuration via JSON file
- Color-coded zone status (green for active)
- Adjustable watering duration via slider
- Configurable refresh rate for status updates

## Project Structure

```
.
├── opensprinkler_api.py    # OpenSprinkler API communication
├── sprinkler_control.py    # Main GUI application
├── requirements.txt        # Python dependencies
├── setup.sh               # Installation script
└── config.json            # Your local configuration (not in git)
```

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- tkinter (usually comes with Python)
- Network access to your OpenSprinkler device

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Run the setup script (Linux/Mac):
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install required dependencies
   - Set up necessary permissions
   - Create a run script

3. For manual installation (Windows or if not using setup.sh):
   ```bash
   python -m venv sprinkler_env
   source sprinkler_env/bin/activate  # On Windows: sprinkler_env\Scripts\activate
   pip install -r requirements.txt
   ```

## Configuration

Create a `config.json` file in the project root with your OpenSprinkler settings:

```json
{
    "opensprinkler": {
        "host": "192.168.1.15",
        "port": 8080,
        "password": "your_password_here", // Default 'opendoor'
        "refresh_interval": 1
    }
}
```

### Configuration Options

- `host`: IP address or hostname of your OpenSprinkler device
- `port`: Port number (default: 8080)
- `password`: Your OpenSprinkler device password
- `refresh_interval`: Status update frequency in seconds

## Running the Application

### Using the Run Script (Linux/Mac)
```bash
./run_sprinkler.sh
```

### Manual Start
```bash
source sprinkler_env/bin/activate  # On Windows: sprinkler_env\Scripts\activate
python sprinkler_control.py
```

## Usage

1. Set the watering duration using the slider (0-180 seconds)
2. Click a zone button to activate that zone
3. Active zones will be highlighted in green
4. Click an active zone again to deactivate it
5. Multiple zones can run simultaneously

## Development

### Version Control

The following files are ignored by git:
- `config.json` (contains sensitive data)
- `run_sprinkler.sh` (system-specific)
- `sprinkler_env/` (virtual environment)
- Python cache files (`__pycache__/`)
- IDE settings and system files

When contributing:
1. Never commit sensitive information
2. Test your changes with different OpenSprinkler configurations
3. Update requirements.txt if you add new dependencies

## Troubleshooting

1. Connection Issues:
   - Verify OpenSprinkler IP address and port
   - Check network connectivity
   - Ensure OpenSprinkler is powered on

2. Authentication Errors:
   - Verify your password in config.json
   - Check if MD5 password encryption is enabled on OpenSprinkler

3. GUI Issues:
   - Ensure tkinter is properly installed
   - Check Python version compatibility
   - Verify virtual environment activation

## Support

For issues and feature requests, please:
1. Check the troubleshooting section
2. Verify your configuration
3. Open an issue with:
   - Your OpenSprinkler firmware version
   - Python version
   - Error messages
   - Steps to reproduce 
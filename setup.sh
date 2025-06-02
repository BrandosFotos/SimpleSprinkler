#!/bin/bash

echo "Starting Sprinkler Control System Setup..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python 3.6 or higher
if ! command_exists python3; then
    echo "Python 3 is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-full
fi

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 6), 'Python 3.6 or higher is required'" || {
    echo "Python 3.6 or higher is required"
    exit 1
}

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-tk \
    python3-venv \
    python3-pip

# Create virtual environment if it doesn't exist
if [ ! -d "sprinkler_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv sprinkler_env
fi

# Activate virtual environment and install requirements
echo "Installing Python dependencies..."
source sprinkler_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup udev rules for Arduino access
echo "Setting up Arduino permissions..."
if [ ! -f "/etc/udev/rules.d/50-arduino.rules" ]; then
    echo 'KERNEL=="ttyUSB[0-9]*",MODE="0666"' | sudo tee /etc/udev/rules.d/50-arduino.rules
    echo 'KERNEL=="ttyACM[0-9]*",MODE="0666"' | sudo tee -a /etc/udev/rules.d/50-arduino.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

# Create a convenience script to run the program
echo "Creating run script..."
cat > run_sprinkler.sh << 'EOL'
#!/bin/bash
source sprinkler_env/bin/activate
python sprinkler_control.py
EOL
chmod +x run_sprinkler.sh

echo "Setup complete!"
echo "To run the program, use: ./run_sprinkler.sh"
echo "Note: You may need to reconnect your Arduino for the permission changes to take effect." 
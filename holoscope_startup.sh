#!/bin/bash

# Define project-specific variables
PROJECT_DIR="$HOME/HoloScope"
VENV_DIR="$PROJECT_DIR/venv"
WHL_FILE="adafruit_circuitpython_bme680-3.7.13-py3-none-any.whl"
PACKAGE_NAME="adafruit-circuitpython-bme680"
SERVICE_NAME="holoscope.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

# Get the current user for the service file
CURRENT_USER=$(whoami)
echo "Starting setup for HoloScope project..."

# Check if the virtual environment directory already exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating a new one..."
    # Change to the project directory
    cd "$HOME/HoloScope" || exit
    # Create the virtual environment with system site packages
    python3 -m venv --system-site-packages venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# activate the virtual environment and install the BME680 library
source ~/HoloScope/venv/bin/activate

# Install core dependencies like adafruit-blinka for the 'board' module
echo "Checking and installing 'adafruit-blinka'..."
if ! pip list | grep -q "adafruit-blinka"; then
    pip install adafruit-blinka
    echo "'adafruit-blinka' installed successfully."
else
    echo "'adafruit-blinka' is already installed."
fi

# Check if the package is already installed
# The 'pip show' command returns a non-zero exit code if the package is not found.
# The `>` redirects stdout to /dev/null to keep the output clean.
if ! pip show "$PACKAGE_NAME" > /dev/null; then
    echo "Package '$PACKAGE_NAME' not found. Installing now..."
    # The --no-index flag prevents pip from checking PyPI, ensuring it installs the local file
    pip install --no-index --find-links . "$WHL_FILE"
    echo "Successfully installed '$PACKAGE_NAME'."
else
    echo "Package '$PACKAGE_NAME' is already installed. No action needed."
fi

# Deactivate the virtual environment
deactivate
echo "Virtual environment deactivated."

# Define the target directory path within the home directory
dir="$HOME/capture_image"

# Check if the directory does not exist
if [ ! -d "$dir" ]; then
    # Create the directory
    mkdir -p "$dir"
    echo "Directory '$dir' created successfully."
else
    # The directory already exists
    echo "Directory '$dir' already exists."
fi

# Set up hotspot to be use
HOTSPOT_NAME="Hotspot"
SSID="HoloScopeAP"
PASSWORD="fishystuff"
INTERFACE="wlan0"

nmcli con show "$HOTSPOT_NAME" &> /dev/null

if [ $? -eq 0 ]; then
  # Check if the hotspot is active
  ACTIVE=$(nmcli -t -f NAME,TYPE,DEVICE con show --active | grep "^$HOTSPOT_NAME:wifi")
  if [ -n "$ACTIVE" ]; then
    echo "Hotspot '$HOTSPOT_NAME' is already active."
  else
    echo "Starting existing hotspot..."
    sudo nmcli con up "$HOTSPOT_NAME"
  fi
else
  echo "Creating new hotspot..."
  nmcli con add type wifi ifname "$INTERFACE" con-name "$HOTSPOT_NAME" autoconnect yes ssid "$SSID"
  nmcli con modify "$HOTSPOT_NAME" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
  nmcli con modify "$HOTSPOT_NAME" wifi-sec.key-mgmt wpa-psk
  nmcli con modify "$HOTSPOT_NAME" wifi-sec.psk "$PASSWORD"
  nmcli con up "$HOTSPOT_NAME"
fi

# --- Step 2: Create the systemd Service File ---
echo "Creating systemd service file: $SERVICE_FILE"

# The command that will be run by systemd
# NOTE: Replace 'main.py' with the name of your Flask app's entry point file
EXEC_START_CMD="$VENV_DIR/bin/python $PROJECT_DIR/run.py"

# Use 'tee' with 'sudo' to write to the system directory
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=HoloScope Flask Web Server
After=network.target

[Service]
Type=simple
ExecStart=$EXEC_START_CMD
WorkingDirectory=$PROJECT_DIR
User=$CURRENT_USER
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created."

# --- Step 3: Enable and Start the Service ---
echo "Enabling and starting the service..."

# Reload the systemd daemon to recognize the new service file
sudo systemctl daemon-reload

# Enable the service to start automatically on boot
sudo systemctl enable "$SERVICE_NAME"

# Start the service immediately
sudo systemctl start "$SERVICE_NAME"

echo "Service started successfully!"

# --- Step 4: Check Service Status ---
echo "Checking the status of the service..."
sudo systemctl status "$SERVICE_NAME" --no-pager
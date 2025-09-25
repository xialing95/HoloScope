#!/bin/bash

# create virtual environment and install required packages
# python3 -m venv --system-site-packages venv

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

# A bash script to check for and install the libcamera-dev package on Debian-based systems.

# Function to check if a package is installed.
# We use dpkg-query for this which is a more reliable way than just checking apt.
is_package_installed() {
  dpkg-query -W --showformat='${Status}\n' "$1" 2>/dev/null | grep "install ok installed"
}

# activate the virtual environment and install the BME680 library
source ~/HoloScope/venv/bin/activate
# Define the package name we are checking for
PACKAGE_NAME="adafruit-circuitpython-bme680"

# Define the filename of the .whl file to install if needed
WHL_FILE="adafruit_circuitpython_bme680-3.7.13-py3-none-any.whl"

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


HOTSPOT_NAME="Hotspot"
SSID="HoloScopeAP"
PASSWORD="fishystuff"
INTERFACE="wlan0"

# Check if the hotspot connection exists
nmcli con show "$HOTSPOT_NAME" &> /dev/null

if [ $? -eq 0 ]; then
  # Check if the hotspot is active
  ACTIVE=$(nmcli -t -f NAME,TYPE,DEVICE con show --active | grep "^$HOTSPOT_NAME:wifi")
  if [ -n "$ACTIVE" ]; then
    echo "Hotspot '$HOTSPOT_NAME' is already active."
    exit 0
  else
    echo "Starting existing hotspot..."
    sudo nmcli con up "$HOTSPOT_NAME"
    exit 0
  fi
else
  echo "Creating new hotspot..."
  nmcli con add type wifi ifname "$INTERFACE" con-name "$HOTSPOT_NAME" autoconnect yes ssid "$SSID"
  nmcli con modify "$HOTSPOT_NAME" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
  nmcli con modify "$HOTSPOT_NAME" wifi-sec.key-mgmt wpa-psk
  nmcli con modify "$HOTSPOT_NAME" wifi-sec.psk "$PASSWORD"
  nmcli con up "$HOTSPOT_NAME"
  exit 0
fi

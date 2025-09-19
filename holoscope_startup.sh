#!/bin/bash

# A bash script to check for and install the libcamera-dev package on Debian-based systems.

# Function to check if a package is installed.
# We use dpkg-query for this which is a more reliable way than just checking apt.
is_package_installed() {
  dpkg-query -W --showformat='${Status}\n' "$1" 2>/dev/null | grep "install ok installed"
}

# Check if libcamera-dev is already installed.
if is_package_installed "libcamera-dev"; then
  echo "libcamera-dev is already installed. No action needed."
else
  # If not installed, prompt the user for confirmation and then install.
  echo "libcamera-dev is not found. We will now install it."
  read -p "Do you want to continue with the installation? (y/n) " -n 1 -r
  echo    # Add a newline for better readability
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting installation..."

    # Update package lists
    echo "Updating package lists..."
    sudo apt-get update

    # Install the package
    echo "Installing libcamera-dev..."
    sudo apt-get install -y libcamera-dev

    echo "Installation complete. The libcamera-dev package is now installed."
  else
    echo "Installation aborted."
  fi
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

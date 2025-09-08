#!/bin/bash

SSID=$1
PASSWORD=$2

WPA_CONF="/etc/wpa_supplicant/wpa_supplicant.conf"

if [ -z "$SSID" ] || [ -z "$PASSWORD" ]; then
  echo "Usage: $0 <SSID> <Password>"
  exit 1
fi

# Backup existing wpa_supplicant.conf
sudo cp $WPA_CONF ${WPA_CONF}.bak

# Create new wpa_supplicant.conf with provided SSID and password
sudo bash -c "cat > $WPA_CONF" << EOF
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
    ssid=\"$SSID\"
    psk=\"$PASSWORD\"
    key_mgmt=WPA-PSK
}
EOF

# Restart wlan0 interface and wpa_supplicant service
sudo wpa_cli -i wlan0 reconfigure

# Bring wlan0 up and down to reset connection
sudo ip link set wlan0 down
sleep 2
sudo ip link set wlan0 up
sleep 5

echo "WiFi connection attempt initiated for SSID: $SSID"

#!/bin/bash

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

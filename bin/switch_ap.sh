#!/bin/bash

# Stop Wi-Fi client service to free wlan0
sudo systemctl stop wpa_supplicant.service

# Bring down wlan0 interface
sudo ip link set wlan0 down

# Assign static IP address to wlan0 for AP
sudo ip addr add 192.168.4.1/24 dev wlan0

# Bring wlan0 back up
sudo ip link set wlan0 up

# Start DHCP and DNS server (dnsmasq)
sudo systemctl restart dnsmasq.service

# Unmask, enable and start the AP service (hostapd)
sudo systemctl unmask hostapd.service
sudo systemctl enable hostapd.service
sudo systemctl start hostapd.service

echo "Access Point started with SSID from /etc/hostapd/hostapd.conf"

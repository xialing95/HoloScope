#!/bin/bash

set -e

AP_SSID="HoloScopeAP"
AP_PASSWORD="holoscopepassword"  # Change this to a strong password or leave blank for open network
INTERFACE="wlan0"
STATIC_IP="192.168.50.1"
DHCP_RANGE_START="192.168.50.10"
DHCP_RANGE_END="192.168.50.50"
DHCP_LEASE_TIME="12h"

echo "Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

echo "Installing hostapd and dnsmasq..."
sudo apt-get install -y hostapd dnsmasq

echo "Stopping services to configure..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

echo "Configuring static IP for $INTERFACE..."
sudo bash -c "cat >> /etc/dhcpcd.conf" << EOF

interface $INTERFACE
    static ip_address=$STATIC_IP/24
    nohook wpa_supplicant
EOF

echo "Restarting dhcpcd service..."
sudo service dhcpcd restart

echo "Backing up existing dnsmasq.conf..."
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig

echo "Creating dnsmasq.conf..."
sudo bash -c "cat > /etc/dnsmasq.conf" << EOF
interface=$INTERFACE
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,$DHCP_LEASE_TIME
EOF

echo "Creating hostapd configuration..."
sudo bash -c "cat > /etc/hostapd/hostapd.conf" << EOF
interface=$INTERFACE
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF

if [ -n "$AP_PASSWORD" ]; then
  sudo bash -c "cat >> /etc/hostapd/hostapd.conf" << EOF
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
fi

echo "Setting DAEMON_CONF in /etc/default/hostapd..."
sudo sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "Enabling IPv4 forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -w net.ipv4.ip_forward=1

echo "Setting up NAT with iptables..."
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

echo "Saving iptables rules..."
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"

echo "Create script to restore iptables on reboot..."
sudo bash -c "cat > /etc/network/if-up.d/iptables" << 'EOF'
#!/bin/sh
iptables-restore < /etc/iptables.ipv4.nat
EOF
sudo chmod +x /etc/network/if-up.d/iptables

# uncomment to start AP services automatically:
#echo "Unmasking and enabling hostapd service..."
#sudo systemctl unmask hostapd
#sudo systemctl enable hostapd

#echo "Starting services..."
#sudo systemctl restart hostapd
#sudo systemctl restart dnsmasq

echo "Setup complete. The access point '$AP_SSID' is configured but not started."

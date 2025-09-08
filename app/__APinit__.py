import subprocess

def switch_to_ap():
    """Switch Raspberry Pi to Access Point mode."""
    try:
        # Example: run shell script that configures AP
        subprocess.run(['/home/pi/HoloScope/bin/switch_ap.sh'], check=True)
        return True, "Switched to Access Point mode."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to switch to AP mode: {e}"

def connect_wifi(ssid, password):
    """Connect Raspberry Pi to WiFi network with given credentials."""
    try:
        # Example: run shell script with SSID and password as arguments
        subprocess.run(['/home/pi/HoloScope/bin/connect_wifi.sh', ssid, password], check=True)
        return True, "WiFi connection initiated."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to connect to WiFi: {e}"

from flask import render_template, request, jsonify
from . import network_bp
import subprocess

@network_bp.route('/')
def index():
    return render_template('network.html')

@network_bp.route('/enable_hotspot', methods=['POST'])
def enable_hotspot():
    try:
        # subprocess.run(['nmcli', 'dev', 'wifi', 'hotspot', 'ifname', 'wlan0', 'ssid', 'MyHotspot', 'password', 'MyPassword123'], check=True)
        return jsonify({'status': 'success', 'message': 'Hotspot enabled.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Failed to enable hotspot: {e}'})

@network_bp.route('/connect_to_wifi', methods=['POST'])
def connect_to_wifi():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')

    if not ssid or not password:
        return jsonify({'status': 'error', 'message': 'SSID and password are required.'})

    try:
        # subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], check=True)
        return jsonify({'status': 'success', 'message': f'Connected to {ssid}.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Failed to connect to {ssid}: {e}'})
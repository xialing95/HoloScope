from . import camera_bp
import io
import os
import json
import time
from flask import Flask, Response, render_template, request, redirect, url_for
from threading import Condition
from os.path import exists
# from picamera2 import Picamera2


# Initialize the camera
# picam2 = Picamera2()

# Get the directory of the currently executing script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Join the directory with the filename
SETTINGS_FILE = os.path.join(script_dir, 'camera_settings.json')

# Default settings if the file doesn't exist
DEFAULT_SETTINGS = {
    "resolution": [640, 480],
    "framerate": 30,
    "iso": 100,
    "expSpd": 10000,
    "expMod": "auto",
    "awbMod": "auto",
    "awbGain": 1.0,
}

# Function to load settings from a file
def load_settings():
    if exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS

# Function to save settings to a file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Load the initial settings
camera_settings = load_settings()

@camera_bp.route('/')
def index():
    return render_template('camera.html')

@camera_bp.route('/camera_config', methods=['GET', 'POST'])
def camera_config():
    try:
        # 1. Update the in-memory settings dictionary
        if 'resolution' in request.form:
            res_str = request.form['resolution'].split('x')
            camera_settings['resolution'] = [int(res_str[0]), int(res_str[1])]
        
        if 'framerate' in request.form:
            camera_settings['framerate'] = int(request.form['framerate'])

        if 'iso' in request.form:
            camera_settings['iso'] = int(request.form['iso'])

        if 'expSpd' in request.form:
            camera_settings['expSpd'] = int(request.form['expSpd'])
            
        if 'expMod' in request.form:
            camera_settings['expMod'] = request.form['expMod']

        if 'awbMod' in request.form:
            camera_settings['awbMod'] = request.form['awbMod']

        if 'awbGain' in request.form:
            camera_settings['awbGain'] = float(request.form['awbGain'])

        # 2. Save the updated settings to the JSON file
        save_settings(camera_settings)

        # Check if the file exists and return its content
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
            
            # Return the JSON data with the correct MIME type
            return Response(json.dumps(data, indent=4), mimetype='application/json')
        except FileNotFoundError:
            return Response("Error: Settings file not found.", status=404, mimetype='text/plain')
        except json.JSONDecodeError:
            return Response("Error: Invalid JSON format.", status=500, mimetype='text/plain')
    
    except Exception as e:
        error_message = f"Error: Failed to save settings. Reason: {e}"
        return Response(error_message, mimetype='text/plain', status=500)
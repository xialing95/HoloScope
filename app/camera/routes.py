from . import camera_bp
import io
import os
import json
import time
from flask import Flask, Response, render_template, request, send_file
from threading import Condition
from os.path import exists

from picamera2 import Picamera2
import time
import threading

'''
JSON file handling for camera settings
'''
# Get the directory of the currently executing script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Join the directory with the filename
SETTINGS_FILE = os.path.join(script_dir, 'camera_settings.json')
PREVIEW_FILE = os.path.join(script_dir, 'preview.jpg')

# Function to load settings from a file
def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default settings if the file does not exist
        return {
            "resolution": [1920, 1080],
            "framerate": 30,
            "iso": 100,
            "expSpd": 20000,
            "expMod": "Manual",
            "ExposureTimeMode": 1,
            "ExposureTime": 20000,
            "ExposureValue": 0,
            "AnalogueGainMode": 1,
            "AnalogueGain": 1.0,
            "AwbEnable": "True",
            "awbGain": 1.0,
            "Brightness": 0.0,
            "Contrast": 1.0
        }

# Function to save settings to a file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Load the initial settings
camera_settings = load_settings()

'''
Camera Picamera2 function
'''
# Global variables for the camera object and its settings
camera = None
preview_config = None
capture_config = None

def initialize_config_camera():
    global camera, preview_config, capture_config
    print("Attempting to initialize and configure camera...")

    if camera:
        print("Deleting existing camera object...")
        delete_camera_object()

    camera = Picamera2()

    capture_config = camera.create_still_configuration(
                main={"size": tuple(camera_settings['resolution'])},  
                raw={'size': tuple(camera_settings['resolution'])}, 
                controls={
                    'ExposureTimeMode': camera_settings['ExposureTimeMode'],
                    'ExposureTime': camera_settings['ExposureTime'],
                    'ExposureValue': camera_settings['ExposureValue'],
                    'AnalogueGainMode': camera_settings['AnalogueGainMode'],
                    'AnalogueGain': camera_settings['AnalogueGain'],
                    'Brightness': camera_settings['Brightness'],
                    'Contrast': camera_settings['Contrast'],
                },
                display=None
                )
    
    camera.configure(capture_config)
    # Switch mode, take the picture, and get a request object
    request_object = camera.switch_mode_capture_request_and_stop(capture_config)

    # Save the main frame as a JPEG
    request_object.save("main", PREVIEW_FILE)

    # Save the raw frame as a DNG file (for RAW data)
    request_object.save_dng(PREVIEW_FILE.replace('.jpg', '.dng'))
    print("Camera object created and configured.")


def delete_camera_object():
    global camera
    if camera:
        try:
            # 1. Stop the camera to halt any streams
            if camera.started:
                camera.stop()
                print("Camera stopped.")

            # 2. Close the camera to release hardware resources
            camera.close()
            print("Camera closed.")
            
            # 3. Explicitly remove the reference to the object
            camera = None
            print("Camera object reference deleted.")
        except Exception as e:
            print(f"Error while trying to delete camera object: {e}")
    else:
        print("No camera object to delete.")

def get_camera_metadata():
    if camera:
        return camera.capture_metadata()
    return {}
    
'''
Flask routes for camera settings
https://libcamera.org/api-html/namespacelibcamera_1_1controls.html
'''
@camera_bp.route('/')
def index():
    return render_template('camera.html')
    
@camera_bp.route('/camera_init_config', methods=['GET', 'POST'])
def camera_init_config():
    try:
        # Update in-memory settings dictionary from request.form
        # Note: All values from request.form are strings.

        # Update resolution
        if 'resolution' in request.form:
            res_str = request.form['resolution'].split('x')
            camera_settings['resolution'] = [int(res_str[0]), int(res_str[1])]
        
        # Update Exposure and Gain
        if 'ExposureTimeMode' in request.form:
            camera_settings['ExposureTimeMode'] = int(request.form['ExposureTimeMode'])

        if 'ExposureTime' in request.form:
            camera_settings['ExposureTime'] = int(request.form['ExposureTime'])

        if 'ExposureValue' in request.form:
            camera_settings['ExposureValue'] = float(request.form['ExposureValue'])
        
        if 'AnalogueGainMode' in request.form:
            camera_settings['AnalogueGainMode'] = int(request.form['AnalogueGainMode'])

        if 'AnalogueGain' in request.form:
            camera_settings['AnalogueGain'] = float(request.form['AnalogueGain'])

        # Update White Balance and Color
        if 'AwbEnable' in request.form:
            camera_settings['AwbEnable'] = request.form['AwbEnable']

        if 'Brightness' in request.form:
            camera_settings['Brightness'] = float(request.form['Brightness'])

        if 'Contrast' in request.form:
            camera_settings['Contrast'] = float(request.form['Contrast'])

        if 'colorspace' in request.form:
            camera_settings['colorspace'] = request.form['colorspace']

        # 2. Save the updated settings to the JSON file
        save_settings(camera_settings)

        # --- Stop, re-configure, and start the camera ---
        # Stop the camera if it's currently running
        if camera and camera.started:
            print("Stopping existing camera instance...")
            camera.stop()
            initialize_config_camera()
        else:
            initialize_config_camera()

        # Check if the file was created successfully
        if os.path.exists(PREVIEW_FILE):
            # Return the image file as a response
            return send_file(PREVIEW_FILE, mimetype='image/jpeg')
        else:
            return Response("Error: Could not capture image.", mimetype='text/plain', status=500)
    
    except Exception as e:
        error_message = f"Error: Failed to initialize camera. Reason: {e}"
        print(f"Server-side error caught: {error_message}")
        return Response(error_message, mimetype='text/plain', status=500)
    
from . import camera_bp
import io
import os
import json
import time
from flask import Flask, Response, render_template, request, jsonify, current_app, send_from_directory
from os.path import exists
import multiprocessing
import signal
from datetime import datetime
import app.epaper_display.epaper_service as epd_service

import sys
from picamera2 import Picamera2
from libcamera import controls

# Get the path to the user's home directory.
home_dir = os.path.expanduser('~')
# Define the full path for the new directory.
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")
# Create the directories if they do not exist
os.makedirs(capture_image_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Join the directory with the filename
SETTINGS_FILE = os.path.join(static_dir, 'camera_settings.json')
PREVIEW_FILE = os.path.join(capture_image_dir, 'preview.jpg')

# --- Multiprocessing Setup ---
# A queue to send commands to the timelapse process
command_queue = multiprocessing.Queue()
# A value to store the current status of the timelapse
status_value = multiprocessing.Value('i', 0)
# A value to store the current photo count
photo_count_value = multiprocessing.Value('i', 0)
# A value to store the number of photos to take
total_photos_value = multiprocessing.Value('i', 0)
# A process object to manage the timelapse process
timelapse_process = None

# Function to load settings from a file
def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Settings file not found. Loading default settings.")
        # A set of default settings
        return {
            "resolution": [1920, 1080],
            "ExposureTimeMode": 0,
            "ExposureTime": 10000,
            "ExposureValue": 0.0,
            "AnalogueGainMode": 0,
            "AnalogueGain": 1.0,
            "Brightness": 0.0,
            "Contrast": 1.0,
            # "colorspace": "sRGB"
        }

# Function to save settings to a file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def delete_camera_object(picam2):
    """Safely stops and closes a Picamera2 object."""
    try:
        if picam2 and picam2.started:
            print("Stopping existing camera instance...")
            picam2.stop()
            print("Camera stopped.")
        
        if picam2:
            picam2.close()
            print("Camera closed.")
        return None
    except Exception as e:
        print(f"Error while trying to delete camera object: {e}")
        return picam2

def initialize_camera(settings):
    """Initializes and returns a Picamera2 object with given settings."""
    try:
         # Check if a camera object already exists and close it before creating a new one
        global picam2
        if picam2:
            picam2 = delete_camera_object(picam2)

        picam2 = Picamera2()
        capture_config = picam2.create_still_configuration(
            main={"size": tuple(settings['resolution'])},
            raw={'size': tuple(settings['resolution'])},
            display=None
        )
        picam2.configure(capture_config)
        
        # Apply controls
        camera_controls = {
            'ExposureTimeMode': settings['ExposureTimeMode'],
            'ExposureTime': settings['ExposureTime'],
            'ExposureValue': settings['ExposureValue'],
            'AnalogueGainMode': settings['AnalogueGainMode'],
            'AnalogueGain': settings['AnalogueGain'],
            'Brightness': settings['Brightness'],
            'Contrast': settings['Contrast'],
        }
        picam2.set_controls(camera_controls)
        
        print("Camera object created and configured.")
        return picam2
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return None

def take_picture(picam2, filename_dir):
    """Initializes, captures a single JPG preview, and closes a Picamera2 object."""
    picam2_local = None # Local instance for the preview
    
    """Captures and saves a picture in both JPG and DNG formats."""
    if not picam2:
        print("Camera object not provided. Cannot take picture.")
        return False
    
    try:
        # Start the camera to prepare for capture
        picam2.start()
        
        # Capture buffers from both main (JPG) and raw (DNG) streams
        buffers, metadata = picam2.switch_mode_and_capture_buffers(picam2.camera_config, ["main", "raw"])
        
        # Save the main (JPG) stream
        jpg_filepath = filename_dir.replace('.dng', '.jpg')
        # Use the camera's configured stream to save the image
        picam2.helpers.save(picam2.helpers.make_image(buffers[0], picam2.camera_config["main"]), metadata, jpg_filepath)
        
        # Save the raw (DNG) stream
        dng_filepath = filename_dir.replace('.jpg', '.dng')
        # Use the camera's configured stream to save the DNG file
        picam2.helpers.save_dng(buffers[1], metadata, picam2.camera_config["raw"], dng_filepath)
        
        print(f"Picture taken and saved to {jpg_filepath} and {dng_filepath}.")
        return True
    except Exception as e:
        print(f"Error taking picture: {e}")
        return False
    finally:
        # Always stop the camera after the operation is complete
        if picam2 and picam2.started:
            picam2.stop()
            picam2 = None

# --- PiCamera Logic (Runs in a separate process) ---
    """
    Main function for the time-lapse process.
    This runs in a separate process and is independent of the Flask server.
    """

def take_preview(settings, filename_dir):
    """Initializes, captures a single JPG preview, and closes a Picamera2 object."""
    picam2_local = None # Local instance for the preview
    try:
        picam2_local = Picamera2()
        
        # NOTE: Using create_still_configuration with main only for speed
        preview_config = picam2_local.create_still_configuration(
            main={"size": tuple(settings['resolution'])},
            display=None
        )
        picam2_local.configure(preview_config)

        # Apply controls
        # ... (Same logic as in initialize_camera, but simplified for preview) ...
        camera_controls = {
            'ExposureTimeMode': settings['ExposureTimeMode'],
            'ExposureTime': settings['ExposureTime'],
            'ExposureValue': settings['ExposureValue'],
            'AnalogueGainMode': settings['AnalogueGainMode'],
            'AnalogueGain': settings['AnalogueGain'],
            'Brightness': settings['Brightness'],
            'Contrast': settings['Contrast'],
        }
        picam2_local.set_controls(camera_controls)
        
        picam2_local.start()

        # Capture buffers from both main (JPG) and raw (DNG) streams
        buffers, metadata = picam2_local.switch_mode_and_capture_buffers(picam2_local.camera_config, ["main", "raw"])
        
        # Save the main (JPG) stream
        jpg_filepath = filename_dir.replace('.dng', '.jpg')
        # Use the camera's configured stream to save the image
        picam2_local.helpers.save(picam2_local.helpers.make_image(buffers[0], picam2_local.camera_config["main"]), metadata, jpg_filepath)
        
        # Save the raw (DNG) stream
        dng_filepath = filename_dir.replace('.jpg', '.dng')
        # Use the camera's configured stream to save the DNG file
        picam2_local.helpers.save_dng(buffers[1], metadata, picam2_local.camera_config["raw"], dng_filepath)

        print(f"Preview taken and saved to {filename_dir}.")
        return True
    except Exception as e:
        print(f"Error taking preview: {e}")
        return False
    finally:
        # Crucially, always stop and close the local object
        if picam2_local:
            if picam2_local.started:
                picam2_local.stop()
            picam2_local.close()

# --- PiCamera Logic (Runs in a separate process) ---
def run_timelapse(command_queue, status_value, photo_count_value, total_photos_value):
    """
    Main function for the time-lapse process.
    This runs in a separate process and is independent of the Flask server.
    """
    picam2 = None
    
    def signal_handler(signum, frame):
        # Gracefully shut down the camera on SIGTERM
        if picam2 and picam2.started:
            print("Received shutdown signal. Stopping camera...")
            picam2.stop()
        exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)

    print("Timelapse process started. Waiting for commands...")
    
    while True:
        try:
            # Check for commands from the main process without blocking
            if not command_queue.empty():
                command = command_queue.get_nowait()
                
                if command['action'] == 'start':
                    settings = command['settings']
                    
                    # Initialize the camera object within this process
                    picam2 = initialize_camera(settings['camera_settings'])
                    if not picam2:
                        status_value.value = -1 # -1: Error
                        print("Initialization of camera failed in timelapse process.")
                        return # Exit if camera initialization fails

                    picam2.start()
                        
                    print(f"Starting time-lapse with settings: {settings}")
                    status_value.value = 1  # 1: Running
                    
                    # Run the time-lapse loop
                    start_time = time.time()
                    for i in range(settings['num_photos']):
                        if status_value.value == 0:  # Check for stop command
                            print("Timelapse stopped by user command.")
                            break
                        
                        photo_count_value.value = i + 1
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        filename_base = settings['filename_base'] + f"_{timestamp}"
                        filepath = os.path.join(capture_image_dir, filename_base + ".dng")
                        print(f"Capturing photo {i+1} of {settings['num_photos']} as {filepath}")
                        
                        # Capture and save both DNG and JPG files
                        buffers, metadata = picam2.switch_mode_and_capture_buffers(picam2.camera_config, ["main", "raw"])
                        
                        jpg_filepath = filepath.replace('.dng', '.jpg')
                        picam2.helpers.save(picam2.helpers.make_image(buffers[0], picam2.camera_config["main"]), metadata, jpg_filepath)
                        picam2.helpers.save_dng(buffers[1], metadata, picam2.camera_config["raw"], filepath)
                        
                        print(f"Picture taken and saved to {jpg_filepath} and {filepath}.")

                        # Wait for the next interval, accounting for capture time
                        elapsed = time.time() - start_time
                        if elapsed < settings['interval']:
                            time.sleep(settings['interval'] - elapsed)
                        start_time = time.time()
                    
                    status_value.value = 0  # 0: Idle
                    print("Timelapse finished successfully.")
                    
                elif command['action'] == 'stop':
                    status_value.value = 0  # 0: Idle
                    print("Received stop command. Stopping.")
            
            # The process should always keep the camera running to be ready for the next command
            time.sleep(1)

        except Exception as e:
            print(f"Error in timelapse process: {e}")
            status_value.value = -1 # -1: Error
            if picam2 and picam2.started:
                picam2.stop()
            time.sleep(5) # Wait before retrying

def get_camera_metadata(picam2):
    if picam2 and picam2.started:
        return picam2.capture_metadata()
    return {}

def get_camera_controls():
    if picam2 and picam2.started:
        return picam2.camera_controls
    return {}

# # Global variable for the camera object
picam2 = None
# The global picam2 variable is now only for cleanup of any old state
# or to signal to other functions that the camera is NOT available
# picam2 = None
# global picam2
picam2 = delete_camera_object(picam2) # Ensure the global is clean at startup.

# --- Flask routes for camera settings ---
@camera_bp.route('/')
def index():
    return render_template('camera.html')

@camera_bp.route('/<path:filename>')
def serve_holoscope_images(filename):
    return send_from_directory(capture_image_dir, filename)

@camera_bp.route('/init_config', methods=['GET', 'POST'])
def camera_init_config():
    try:
        camera_settings = load_settings()
        
        # Apply any updates from the form
        if 'resolution' in request.form:
            res_str = request.form['resolution'].split('x')
            camera_settings['resolution'] = [int(res_str[0]), int(res_str[1])]
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
        if 'Brightness' in request.form:
            camera_settings['Brightness'] = float(request.form['Brightness'])
        if 'Contrast' in request.form:
            camera_settings['Contrast'] = float(request.form['Contrast'])
        # if 'colorspace' in request.form:
        #     camera_settings['colorspace'] = request.form['colorspace']

        save_settings(camera_settings)
        
        # picam2 = initialize_camera(camera_settings)
        # if picam2 and take_picture(picam2, PREVIEW_FILE):
        #     return jsonify({
        #         'camera_settings': camera_settings,
        #         'image_url': f'/camera/preview.jpg?t={int(time.time())}'
        #     })
        # else:
        #     return jsonify({'error': 'Failed to capture image.'}), 500

        # The main process now uses a self-contained function for preview
        if take_preview(camera_settings, PREVIEW_FILE): # Pass the settings for configuration
            return jsonify({
                'camera_settings': camera_settings,
                'image_url': f'/camera/preview.jpg?t={int(time.time())}'
            })
        else:
            return jsonify({'error': 'Failed to capture preview image.'}), 500
 
    except Exception as e:
        error_message = f"Error: Failed to initialize camera. Reason: {e}"
        print(f"Server-side error caught: {error_message}")
        return Response(error_message, mimetype='text/plain', status=500)

@camera_bp.route('/start_timelapse', methods=['POST'])
def camera_start_timelapse():
    global timelapse_process
    
    if timelapse_process and timelapse_process.is_alive():
        return jsonify({'status': 'error', 'message': 'A time-lapse is already running.'})

    try:
        data = request.json
        duration = int(data.get('duration', 60))
        interval = int(data.get('interval', 10))
        filename_base = data.get('filename', 'timelapse_photo')
        
        if interval <= 0:
            return jsonify({'status': 'error', 'message': 'Interval must be greater than 0.'})
        
        num_photos = duration // interval
        
        # Load the settings to be sent to the child process
        settings = load_settings()
        
        photo_count_value.value = 0
        total_photos_value.value = num_photos

        timelapse_process = multiprocessing.Process(
            target=run_timelapse,
            args=(command_queue, status_value, photo_count_value, total_photos_value)
        )
        timelapse_process.start()
        
        command_queue.put({'action': 'start', 'settings': {
            'filename_base': filename_base,
            'duration': duration,
            'interval': interval,
            'num_photos': num_photos,
            'image_dir': capture_image_dir,
            'camera_settings': settings # Explicitly pass the full settings dictionary
        }})
        
        return jsonify({'status': 'success', 'message': f'Time-lapse started. Capturing {num_photos} photos.'})
    
    except Exception as e:
        print(f"Error starting time-lapse: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@camera_bp.route('/stop_timelapse', methods=['POST'])
def camera_stop_timelapse():
    global timelapse_process
    if timelapse_process and timelapse_process.is_alive():
        command_queue.put({'action': 'stop'})
        # Give the process a moment to stop gracefully
        time.sleep(2)
        if timelapse_process.is_alive():
            timelapse_process.terminate()
            timelapse_process = None
        return jsonify({'status': 'success', 'message': 'Time-lapse has been stopped.'})
    return jsonify({'status': 'info', 'message': 'No time-lapse is currently running.'})

@camera_bp.route('/timelapse_status')
def timelapse_status():
    """Returns the current status of the time-lapse."""
    status_map = {0: 'Idle', 1: 'Running', -1: 'Error'}
    current_status = status_map.get(status_value.value, 'Unknown')
    
    return jsonify({
        'status': current_status,
        'current_photo': photo_count_value.value,
        'total_photos': total_photos_value.value
    })

# --- Main process signal handler ---
def shutdown_handler(signum, frame):
    """
    Handles a SIGINT (Ctrl-C) signal to gracefully terminate the child process.
    """
    global timelapse_process
    print("Main process received Ctrl-C. Initiating graceful shutdown of timelapse process...")
    if timelapse_process and timelapse_process.is_alive():
        timelapse_process.terminate()
        timelapse_process.join()
        print("Timelapse process terminated successfully.")
    # timelapse_process.terminate()
    # timelapse_process.join()
    print("Timelapse process terminated successfully.")
    sys.exit(0)

# Register the signal handler for SIGINT (Ctrl-C)
signal.signal(signal.SIGINT, shutdown_handler)
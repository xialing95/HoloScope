from . import camera_bp
import io
import os
import json
import time
from flask import Flask, Response, render_template, request, jsonify, current_app, send_from_directory
from os.path import exists
import multiprocessing
import signal

from picamera2 import Picamera2
import time

'''
JSON file handling for camera settings
'''
# Get the path to the user's home directory.
home_dir = os.path.expanduser('~')
# Define the full path for the new directory.
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")

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
        return {
                "resolution": [
                    1920,
                    1080
                ],
                "ExposureTimeMode": 0,
                "ExposureTime": 20000,
                "ExposureValue": 0.0,
                "AnalogueGainMode": 0,
                "AnalogueGain": 1.0,
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
    # Load the initial settings
    camera_settings = load_settings()
    
    global camera, preview_config, capture_config
    print("Attempting to initialize and configure camera...")

    if camera:
        print("Deleting existing camera object...")
        delete_camera_object()

    camera = Picamera2()

    capture_config = camera.create_still_configuration(
                main={"size": tuple(camera_settings['resolution'])},  
                raw={'size': tuple(camera_settings['resolution'])}, 
                display=None
                )
    
    controls={
        'ExposureTimeMode': camera_settings['ExposureTimeMode'],
        'ExposureTime': camera_settings['ExposureTime'],
        'ExposureValue': camera_settings['ExposureValue'],
        'AnalogueGainMode': camera_settings['AnalogueGainMode'],
        'AnalogueGain': camera_settings['AnalogueGain'],
        'Brightness': camera_settings['Brightness'],
        'Contrast': camera_settings['Contrast'],
    }

    camera.configure(capture_config)
    camera.start()
    time.sleep(2)
    camera.set_controls(controls)
    time.sleep(1)
    print("Camera object created and configured.")

def take_preview_picture():
    global camera
    if not camera:
        print("Camera not initialized. Initializing now...")
        initialize_config_camera()
    else:
        print("Camera already initialized. Taking preview picture...")

    if camera and camera.started:
        try:
            # Switch mode, take the picture, and get a request object
            request_object = camera.switch_mode_capture_request_and_stop(capture_config)

            # Save the main frame as a JPEG
            request_object.save("main", PREVIEW_FILE)

            # Save the raw frame as a DNG file (for RAW data)
            request_object.save_dng(PREVIEW_FILE.replace('.jpg', '.dng'))
            print("Preview picture taken and saved.")
        except Exception as e:
            print(f"Error taking preview picture: {e}")
    else:
        print("Camera is not started. Cannot take picture.")

# --- PiCamera Logic (Runs in a separate process) ---
def run_timelapse(command_queue, status_value, photo_count_value, total_photos_value):
    """
    Main function for the time-lapse process.
    This runs in a separate process and is independent of the Flask server.
    """
    
    def signal_handler(signum, frame):
        # Gracefully shut down the camera on SIGTERM
        if camera and camera.started:
            print("Received shutdown signal. Stopping camera...")
            camera.stop()
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
                    print(f"Starting time-lapse with settings: {settings}")
                    status_value.value = 1  # 1: Running
                    
                    # # Initialize PiCamera2
                    # picam2 = Picamera2()
                    # config = picam2.create_still_configuration(
                    #     main={"size": settings['resolution']},
                    #     lores={"size": (640, 480)},
                    #     display="lores"
                    # )
                    # picam2.configure(config)
                    camera.start()
                    
                    # Run the time-lapse loop
                    start_time = time.time()
                    for i in range(settings['num_photos']):
                        if status_value.value == 0:  # Check for stop command
                            print("Timelapse stopped by user command.")
                            break
                        
                        photo_count_value.value = i + 1
                        filename = settings['filename_base'] + f"_{i:04d}.dng"
                        filepath = os.path.join(settings['image_dir'], filename)
                        print(f"Capturing photo {i+1} of {settings['num_photos']} as {filepath}")
                        
                        # camera.capture_file(filepath)
                        # request = camera.capture_request()
                        # request.save_dng(filepath.replace('.jpg', '.dng'))
                        # request.save("main", "newest.jpg" )
                        # request.release()

                        buffers, metadata = camera.switch_mode_and_capture_buffers(capture_config, ["main", "raw"])
                        camera.helpers.save(camera.helpers.make_image(buffers[0], capture_config["main"]), metadata, filepath.replace('.dng', '.jpg'))
                        camera.helpers.save_dng(buffers[1], metadata, capture_config["raw"], filepath)
                        
                        # Wait for the next interval, accounting for capture time
                        elapsed = time.time() - start_time
                        if elapsed < settings['interval']:
                            time.sleep(settings['interval'] - elapsed)
                        start_time = time.time()
                    
                    status_value.value = 0  # 0: Idle
                    camera.stop()
                    print("Timelapse finished successfully.")
                    
                elif command['action'] == 'stop':
                    status_value.value = 0  # 0: Idle
                    print("Received stop command. Stopping.")

            # Sleep to prevent high CPU usage when idle
            time.sleep(1)

        except Exception as e:
            print(f"Error in timelapse process: {e}")
            status_value.value = -1 # -1: Error
            if camera and camera.started:
                camera.stop()
            time.sleep(5) # Wait before retrying

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

# This tells Flask to serve files from this directory under the /holoscope_images/ URL
@camera_bp.route('/<path:filename>')
def serve_holoscope_images(filename):
    # Make sure 'capture_image_dir' is defined in your app's configuration
    return send_from_directory(current_app.config['CAPTURE_IMAGE_DIR'], filename)   

@camera_bp.route('/init_config', methods=['GET', 'POST'])
def camera_init_config():
    try:
        if 'resolution' in request.form:
            res_str = request.form['resolution'].split('x')
            camera_settings['resolution'] = [int(res_str[0]), int(res_str[1])]
            print(f"Updated resolution to: {camera_settings['resolution']}")
        
        # Update Exposure and Gain
        if 'ExposureTimeMode' in request.form:
            camera_settings['ExposureTimeMode'] = int(request.form['ExposureTimeMode'])
            print(f"Updated ExposureTimeMode to: {camera_settings['ExposureTimeMode']}")

        if 'ExposureTime' in request.form:
            camera_settings['ExposureTime'] = int(request.form['ExposureTime'])
            print(f"Updated ExposureTime to: {camera_settings['ExposureTime']}")

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

        # Save the updated settings to the JSON file
        save_settings(camera_settings)
        with open(SETTINGS_FILE, 'r') as f:
            settings_data= json.load(f)

        # --- Stop, re-configure, and start the camera ---
        # Stop the camera if it's currently running
        if camera and camera.started:
            print("Stopping existing camera instance...")
            camera.stop()
            initialize_config_camera()
            take_preview_picture()
        else:
            initialize_config_camera()
            take_preview_picture()

        # Add a check to ensure the file exists and has content
        if not os.path.exists(PREVIEW_FILE) or os.path.getsize(PREVIEW_FILE) == 0:
            return jsonify({'error': 'Image file not saved or is empty.'}), 500
        else:
            return jsonify({
                'camera_settings': settings_data,
                'image_url': f'/camera/preview.jpg?t={int(time.time())}'            
            })    
 
    except Exception as e:
        error_message = f"Error: Failed to initialize camera. Reason: {e}"
        print(f"Server-side error caught: {error_message}")
        return Response(error_message, mimetype='text/plain', status=500)

@camera_bp.route('/start_timelapse', methods=['POST'])
def camera_start_timelapse():
    try:
        data = request.json
        duration = int(data.get('duration', 60))
        interval = int(data.get('interval', 10))
        filename_base = data.get('filename', 'timelapse_photo')
        
        # Calculate number of photos
        if interval <= 0:
            num_photos = 0
            message = "Interval must be greater than 0."
            return jsonify({'status': 'error', 'message': message})
        else:
            num_photos = duration // interval
        
        # Placeholder settings. In a real app, these would come from the form.
        settings = {
            'filename_base': filename_base,
            'duration': duration,
            'interval': interval,
            'num_photos': num_photos,
        }

        # Clear shared values
        photo_count_value.value = 0
        total_photos_value.value = num_photos
        
        # Start the new process if one isn't already running
        if timelapse_process is None or not timelapse_process.is_alive():
            timelapse_process = multiprocessing.Process(
                target=run_timelapse,
                args=(command_queue, status_value, photo_count_value, total_photos_value)
            )
            timelapse_process.start()
        
        # Send the start command to the new process via the queue
        command_queue.put({'action': 'start', 'settings': settings})
        
        return jsonify({'status': 'success', 'message': f'Time-lapse started. Capturing {num_photos} photos.'})
    
    except Exception as e:
        print(f"Error starting time-lapse: {e}")
    return jsonify({'status': 'error', 'message': str(e)})


@camera_bp.route('/stop_timelapse', methods=['POST'])
def camera_stop_timelapse():
    return jsonify({'status': 'info', 'message': 'No time-lapse is currently running.'})
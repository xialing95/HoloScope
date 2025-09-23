from flask import Flask, render_template, request, jsonify
from . import dashboard_bp
import os
import time
import multiprocessing
import signal

from picamera2 import Picamera2
import time

# Get the path to the user's home directory.
home_dir = os.path.expanduser('~')

# This finds the user's home directory and appends 'capture_image'.
CAPTURE_IMAGE_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')

# Define the full path for the new directory.
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")

# Join the directory with the filename
SETTINGS_FILE = os.path.join(static_dir, 'camera_settings.json')

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
                    print(f"Starting time-lapse with settings: {settings}")
                    status_value.value = 1  # 1: Running
                    
                    # Initialize PiCamera2
                    picam2 = Picamera2()
                    config = picam2.create_still_configuration(
                        main={"size": settings['resolution']},
                        lores={"size": (640, 480)},
                        display="lores"
                    )
                    picam2.configure(config)
                    picam2.set_controls({'AwbEnable': settings['AwbEnable']})
                    picam2.start()
                    
                    # Run the time-lapse loop
                    start_time = time.time()
                    for i in range(settings['num_photos']):
                        if status_value.value == 0:  # Check for stop command
                            print("Timelapse stopped by user command.")
                            break
                        
                        photo_count_value.value = i + 1
                        filename = settings['filename_base'] + f"_{i:04d}.jpg"
                        filepath = os.path.join(settings['image_dir'], filename)
                        print(f"Capturing photo {i+1} of {settings['num_photos']} as {filepath}")
                        
                        picam2.capture_file(filepath)
                        
                        # Wait for the next interval, accounting for capture time
                        elapsed = time.time() - start_time
                        if elapsed < settings['interval']:
                            time.sleep(settings['interval'] - elapsed)
                        start_time = time.time()
                    
                    status_value.value = 0  # 0: Idle
                    picam2.stop()
                    print("Timelapse finished successfully.")
                    
                elif command['action'] == 'stop':
                    status_value.value = 0  # 0: Idle
                    print("Received stop command. Stopping.")

            # Sleep to prevent high CPU usage when idle
            time.sleep(1)

        except Exception as e:
            print(f"Error in timelapse process: {e}")
            status_value.value = -1 # -1: Error
            if picam2 and picam2.started:
                picam2.stop()
            time.sleep(5) # Wait before retrying


# --- Flask Routes ---
@dashboard_bp.route('/')
def index():
    """Serves the main HTML page."""
    # HTML, CSS, and JavaScript are all in one string for a self-contained app
    return render_template('dashboard.html')

@dashboard_bp.route('/start_timelapse', methods=['POST'])
def start_timelapse():
    """Receives form data and starts the time-lapse."""
    global timelapse_process
    
    # Check if a time-lapse is already running
    if status_value.value != 0:
        return jsonify({'status': 'error', 'message': 'A time-lapse is already in progress.'})

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
            'resolution': (1920, 1080),
            'ExposureTimeMode': 0, # Auto
            'ExposureTime': 10000,
            'AnalogueGain': 1.0,
            'AnalogueGainMode': 0,
            'AwbEnable': True,
            'image_dir': app.config['IMAGE_DIR']
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

@dashboard_bp.route('/stop_timelapse', methods=['POST'])
def stop_timelapse():
    """Stops the time-lapse process."""
    global timelapse_process
    if timelapse_process and timelapse_process.is_alive():
        command_queue.put({'action': 'stop'})
        # Give the process a moment to stop gracefully
        time.sleep(2)
        if timelapse_process.is_alive():
            timelapse_process.terminate()
        return jsonify({'status': 'success', 'message': 'Time-lapse has been stopped.'})
    return jsonify({'status': 'info', 'message': 'No time-lapse is currently running.'})

@dashboard_bp.route('/timelapse_status')
def timelapse_status():
    """Returns the current status of the time-lapse."""
    status_map = {0: 'Idle', 1: 'Running', -1: 'Error'}
    current_status = status_map.get(status_value.value, 'Unknown')
    
    return jsonify({
        'status': current_status,
        'current_photo': photo_count_value.value,
        'total_photos': total_photos_value.value
    })
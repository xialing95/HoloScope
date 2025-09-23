from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for
from . import dashboard_bp
import os
import time
import threading

from picamera2 import Picamera2
import time

# Define the base directory for the images.
# This finds the user's home directory and appends 'capture_image'.
CAPTURE_IMAGE_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')

# Global state to store time-lapse information
timelapse_state = {
    "is_running": False,
    "num_photos": 0,
    "elapse_time": 0
}



# --- Utility Function for Time-Lapse (runs in a separate thread) ---
def _run_timelapse_task(filename, duration, interval):
    """
    This function simulates a time-lapse operation.
    It takes "photos" and saves them to the specified directory.
    """
    try:
        timelapse_state["is_running"] = True
        num_photos = int(duration / interval)
        timelapse_state["num_photos"] = num_photos
        timelapse_state["elapse_time"] = duration
        
        for i in range(num_photos):
            if not timelapse_state["is_running"]: # Allow stopping
                break
            
            # Simulate capturing and saving a photo
            photo_name = f"{filename}_{i + 1:04d}.jpg"
            photo_path = os.path.join(CAPTURE_IMAGE_DIR, photo_name)
            with open(photo_path, 'w') as f:
                f.write(f"This is a placeholder for photo {i + 1}")
                
            print(f"Captured photo: {photo_name}")
            
            time.sleep(interval)
            
    finally:
        timelapse_state["is_running"] = False
        print("Time-lapse finished.")

@dashboard_bp.route('/')
def index():
    return render_template('dashboard.html')

@dashboard_bp.route('/start', methods=['POST'])
def start_timelapse():
    """
    Starts the time-lapse operation.
    """
    if timelapse_state["is_running"]:
        return jsonify({'success': False, 'message': 'Time-lapse is already running.'})

    try:
        filename = request.form.get('filename') or "photo"
        duration = int(request.form.get('duration'))
        interval = int(request.form.get('interval'))

        # Simple input validation
        if duration <= 0 or interval <= 0 or duration < interval:
            return "Invalid input. Duration and interval must be positive and duration must be greater than or equal to interval.", 400

        # Start the time-lapse in a new thread to avoid blocking the server
        timelapse_thread = threading.Thread(
            target=_run_timelapse_task,
            args=(filename, duration, interval)
        )
        timelapse_thread.start()
        
        return redirect(url_for('index'))
    
    except (ValueError, TypeError):
        return "Invalid input. Please provide numbers for duration and interval.", 400
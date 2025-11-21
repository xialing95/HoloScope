from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from . import dashboard_bp
import subprocess
import os
import glob
import time
import signal

# Define the image directory path
home_dir = os.path.expanduser('~')
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")

SCRIPT_NAME = "simple_timelapse.py"
static_dir = os.path.join(home_dir, "HoloScope", "app", SCRIPT_NAME)
PID_FILE = "timelapse.pid"

def is_running():
    """Checks if the timelapse process is currently running."""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # os.kill(pid, 0) doesn't actually kill the process; 
        # it throws an error if the process doesn't exist.
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # Process is dead or PID file is corrupt
        return False

def get_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            return f.read().strip()
    return None

def get_latest_image(directory):
    """
    Finds the path to the newest JPG image in the specified directory.
    Returns None if no JPG files are found.
    """
    # Use glob to find all files ending in .jpg
    list_of_files = glob.glob(os.path.join(directory, '*.jpg'))
    if not list_of_files:
        return None  # Return None if no JPG files are found

    # Find the most recently modified file using os.path.getmtime
    latest_file = max(list_of_files, key=os.path.getmtime)
    
    # Return just the filename, which is the last part of the path
    return os.path.basename(latest_file)

# --- Flask Routes ---
@dashboard_bp.route('/')
def index():
    """Serves the main HTML page."""
    # HTML, CSS, and JavaScript are all in one string for a self-contained app
    return render_template('dashboard.html', running=is_running(), pid=get_pid())

@dashboard_bp.route('/latest_image')
def latest_image():
    """
    A route that serves the latest image from the capture_images directory.
    This is the URL that the <img> tag will point to.
    """
    latest_filename = get_latest_image(capture_image_dir)
    
    # If a file is found, send it from the directory
    if latest_filename:
        # send_from_directory is the secure way to serve files
        return send_from_directory(capture_image_dir, latest_filename)
    else:
        # If no image is found, you could serve a placeholder or return a 404
        return "No image found", 404

# --- Script Execution Route ---
# @dashboard_bp.route('/start_simple_log', methods=['POST'])
# def start_log():
#     """Executes the simple_log_start.sh script."""

#     try:
#         # Use subprocess.run to execute the shell script
#         # check=True will raise an exception if the script returns a non-zero exit code
#         result = subprocess.run(
#             [script_path],
#             capture_output=True,
#             text=True,
#             shell=False # It's safer to avoid shell=True when possible
#         )

# # 2. Success Response
#         return jsonify({
#             "status": "success",
#             "message": "Simple log started successfully!",
#             "output": result.stdout.strip()
#         }), 200 # HTTP 200 OK

#     except subprocess.CalledProcessError as e:
#         # 3. Handle Script Execution Error (non-zero exit code)
#         error_message = f"Error executing script: {e.stderr.strip()}"

#         return jsonify({
#             "status": "error",
#             "message": "Failed to start log.",
#             "error_detail": e.stderr.strip(),
#             "output": e.stdout.strip() # Include stdout in case of partial output
#         }), 500 # HTTP 500 Internal Server Error

#     except FileNotFoundError:
#         # 4. Handle Script Not Found Error
#         error_message = f"Error: Script file not found at {script_path}"

#         return jsonify({
#             "status": "error",
#             "message": "Failed to start log.",
#             "error_detail": "Script file not found."
#         }), 500 # HTTP 500 Internal Server Error

#     except Exception as e:
#         # 5. Handle any other unexpected exceptions
#         error_message = f"An unexpected error occurred: {str(e)}"

#         return jsonify({
#             "status": "error"+ str(e),
#             "message": "An unexpected server error occurred.",
#         }), 500 # HTTP 500 Internal Server Error

# @dashboard_bp.route('/start', methods=['POST'])
# def start():
#     if not is_running():
#         # Ensure we use full path or relative path correctly
#         process = subprocess.Popen(["python3", SCRIPT_NAME])
#         with open(PID_FILE, 'w') as f:
#             f.write(str(process.pid))
#     return redirect(url_for('index'))

# @dashboard_bp.route('/stop', methods=['POST'])
# def stop():
#     if is_running():
#         try:
#             with open(PID_FILE, 'r') as f:
#                 pid = int(f.read().strip())
#             os.kill(pid, signal.SIGTERM)
#             os.remove(PID_FILE)
#         except Exception as e:
#             print(f"Error: {e}")
#     return redirect(url_for('index'))

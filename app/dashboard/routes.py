from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from . import dashboard_bp
import subprocess
import os
import glob
import time

# Define the image directory path
home_dir = os.path.expanduser('~')
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")
script_path = os.path.join(home_dir, "HoloScope", "app", "sensors", "simple_log_start.sh")

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
    return render_template('dashboard.html')

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
@dashboard_bp.route('/start-log', methods=['POST'])
def start_log():
    """Executes the simple_log_start.sh script."""

    try:
        # Use subprocess.run to execute the shell script
        # check=True will raise an exception if the script returns a non-zero exit code
        result = subprocess.run(
            [script_path],
            check=True,
            capture_output=True,
            text=True,
            shell=False # It's safer to avoid shell=True when possible
        )

        # Log successful output and inform the user
        print(f"Script executed successfully. Output:\n{result.stdout}")
        flash('Simple log started successfully!', 'success')

    except subprocess.CalledProcessError as e:
        # Handle errors if the script fails
        error_message = f"Error executing script: {e.stderr}"
        print(error_message)
        flash(f'Failed to start log. Error: {e.stderr.strip()}', 'error')

    except FileNotFoundError:
        # Handle case where the script file is not found
        error_message = f"Error: Script file not found at {script_path}"
        print(error_message)
        flash('Failed to start log. Script file not found.', 'error')

    # Redirect back to the main page
    return redirect(url_for('dashboard_bp.index'))

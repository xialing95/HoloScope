from flask import Flask, render_template, request, jsonify, send_from_directory
from . import dashboard_bp
import os
import glob
import app
import time

# Define the image directory path
home_dir = os.path.expanduser('~')
capture_image_dir = os.path.join(home_dir, "capture_image")
static_dir = os.path.join(home_dir, "HoloScope", "app", "static")

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


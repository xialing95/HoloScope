from flask import Flask, render_template, request, jsonify
from . import dashboard_bp
import os
import time
import multiprocessing
import signal
# from camera_functions import initialize_config_camera, delete_camera_object, load_settings, save_settings

from picamera2 import Picamera2
import time

# --- Flask Routes ---
@dashboard_bp.route('/')
def index():
    """Serves the main HTML page."""
    # HTML, CSS, and JavaScript are all in one string for a self-contained app
    return render_template('dashboard.html')

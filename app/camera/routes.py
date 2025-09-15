from flask import render_template, request, jsonify
from . import camera_bp

@camera_bp.route('/')
def index():
    return render_template('camera.html')
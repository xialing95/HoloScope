from flask import render_template, request, jsonify
from . import sensors_bp

@sensors_bp.route('/')
def index():
    return render_template('sensor.html')
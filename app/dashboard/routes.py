from flask import render_template, request, jsonify
from . import dashboard_bp

@dashboard_bp.route('/')
def index():
    return render_template('dashboard.html')
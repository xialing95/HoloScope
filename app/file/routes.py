from flask import render_template, request, jsonify
from . import file_bp

@file_bp.route('/')
def index():
    return render_template('file.html')
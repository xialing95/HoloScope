from flask import render_template, request, jsonify, send_from_directory
from . import file_bp
import os

# This finds the user's home directory and appends 'capture_image'.
CAPTURE_IMAGE_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')

# Create the directory if it does not exist.
os.makedirs(CAPTURE_IMAGE_DIR, exist_ok=True)

# Route for the main page.
@file_bp.route('/')
def index():
    """
    Renders the main page and passes the list of images to the template.
    """
    # Get all files in the directory that are images (e.g., .jpg, .png, .gif).
    # This list will be passed to the HTML template.
    try:
        images = sorted([f for f in os.listdir(CAPTURE_IMAGE_DIR) if os.path.isfile(os.path.join(CAPTURE_IMAGE_DIR, f))])
    except FileNotFoundError:
        images = []
    return render_template('file.html', images=images)

# Route to download a specific image.
@file_bp.route('/download/<filename>')
def download(filename):
    """
    Allows the user to download a specific file.
    """
    # Use send_from_directory to securely serve the file.
    # The as_attachment=True parameter forces the browser to download the file.
    return send_from_directory(CAPTURE_IMAGE_DIR, filename, as_attachment=True)

# Route to delete a specific image. This is a POST request for security.
@file_bp.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    """
    Deletes a specific image file from the directory.
    """
    file_path = os.path.join(CAPTURE_IMAGE_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            # Return a success message for the JavaScript fetch call.
            return jsonify({'success': True, 'message': f'File {filename} deleted successfully.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error deleting file: {e}'})
    else:
        return jsonify({'success': False, 'message': 'File not found.'})

# Route to get an updated list of images (used by the JavaScript 'update' button).
@file_bp.route('/images', methods=['GET'])
def get_images():
    """
    Returns a JSON list of all images in the directory.
    """
    try:
        images = sorted([f for f in os.listdir(CAPTURE_IMAGE_DIR) if os.path.isfile(os.path.join(CAPTURE_IMAGE_DIR, f))])
        return jsonify(images)
    except FileNotFoundError:
        return jsonify([])
    


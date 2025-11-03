from flask import render_template, request, jsonify, send_from_directory, send_file
from . import file_bp
import os
import zipfile
import io

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
    # Define a set of valid file extensions
    VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif','.dng', '.json', 'csv')

    try:
        images = sorted([
            f for f in os.listdir(CAPTURE_IMAGE_DIR)
            if os.path.isfile(os.path.join(CAPTURE_IMAGE_DIR, f)) and 
            f.lower().endswith(VALID_EXTENSIONS)
        ])
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
    
# New Route: Delete ALL images
@file_bp.route('/delete_all', methods=['POST'])
def delete_all():
    """
    Deletes all image files from the directory.
    """
    try:
        images = [f for f in os.listdir(CAPTURE_IMAGE_DIR) if os.path.isfile(os.path.join(CAPTURE_IMAGE_DIR, f))]
        for image in images:
            os.remove(os.path.join(CAPTURE_IMAGE_DIR, image))
        return jsonify({'success': True, 'message': 'All images deleted successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting all files: {e}'})

# New Route: Delete selected images
@file_bp.route('/delete_selected', methods=['POST'])
def delete_selected():
    """
    Deletes selected image files from the directory.
    """
    data = request.get_json()
    filenames = data.get('filenames', [])
    deleted_count = 0
    errors = []

    for filename in filenames:
        file_path = os.path.join(CAPTURE_IMAGE_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                errors.append(f'Failed to delete {filename}: {e}')
    
    if errors:
        return jsonify({'success': False, 'message': f'Some files could not be deleted. Errors: {", ".join(errors)}'})
    
    return jsonify({'success': True, 'message': f'Successfully deleted {deleted_count} file(s).'})

# New Route: Download ALL images as a ZIP file
@file_bp.route('/download_all', methods=['GET'])
def download_all():
    """
    Downloads all image files as a single ZIP file.
    """
    try:
        images = [f for f in os.listdir(CAPTURE_IMAGE_DIR) if os.path.isfile(os.path.join(CAPTURE_IMAGE_DIR, f))]
        
        # Create a in-memory ZIP file
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image in images:
                file_path = os.path.join(CAPTURE_IMAGE_DIR, image)
                zipf.write(file_path, arcname=image)
        
        memory_file.seek(0)
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='all_images.zip')
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating ZIP file: {e}'})

# New Route: Download selected images as a ZIP file
@file_bp.route('/download_selected', methods=['POST'])
def download_selected():
    """
    Downloads selected image files as a single ZIP file.
    """
    data = request.get_json()
    filenames = data.get('filenames', [])
    
    if not filenames:
        return jsonify({'success': False, 'message': 'No files selected for download.'})

    try:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in filenames:
                file_path = os.path.join(CAPTURE_IMAGE_DIR, filename)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    zipf.write(file_path, arcname=filename)
        
        memory_file.seek(0)
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='selected_images.zip')
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating ZIP file: {e}'})

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
    


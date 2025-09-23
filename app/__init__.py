from flask import Flask, render_template, send_from_directory, current_app
import os

def create_app(config_class=None):
    app = Flask(__name__)

    # Define the image directory path
    home_dir = os.path.expanduser('~')
    capture_image_dir = os.path.join(home_dir, "capture_image")

    # Store the path in the app configuration
    app.config['CAPTURE_IMAGE_DIR'] = capture_image_dir

    # Import and register blueprints
    from .network import network_bp
    from .camera import camera_bp
    from .file import file_bp
    from .sensors import sensors_bp
    from .dashboard import dashboard_bp

    app.register_blueprint(network_bp, url_prefix='/network')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(camera_bp, url_prefix='/camera')
    app.register_blueprint(sensors_bp, url_prefix='/sensors')
    app.register_blueprint(file_bp, url_prefix='/file')

    # Example homepage
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
from flask import Flask, render_template

def create_app(config_class=None):
    app = Flask(__name__)

    # Import and register blueprints
    from .network import network_bp
    from .camera import camera_bp
    from .file import file_bp
    from .sensors import sensors_bp
    from .dashboard import dashboard_bp


    # app.register_blueprint(network_bp, url_prefix='/network')
    # app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    # app.register_blueprint(camera_bp, url_prefix='/camera')
    # app.register_blueprint(sensors_bp, url_prefix='/sensors')
    # app.register_blueprint(file_bp, url_prefix='/file')

    # avoid network prefix for example use /enable_ap instead of /network/enable_ap
    app.register_blueprint(network_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(file_bp)

    # Example homepage
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
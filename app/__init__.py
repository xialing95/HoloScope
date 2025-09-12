from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import and register blueprints or routes here
    from .routes import main_bp
    app.register_blueprint(main_bp) # If using blueprints

    return app

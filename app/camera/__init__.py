from flask import Blueprint

camera_bp = Blueprint('camera', __name__, template_folder='templates')

from . import routes
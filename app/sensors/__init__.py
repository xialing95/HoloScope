from flask import Blueprint

sensors_bp = Blueprint('sensors', __name__, template_folder='templates')

from . import routes
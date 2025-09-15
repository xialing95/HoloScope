from flask import Blueprint

network_bp = Blueprint('network', __name__, template_folder='templates')

from . import routes
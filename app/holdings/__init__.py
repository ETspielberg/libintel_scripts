from flask import Blueprint

holdings_blueprint = Blueprint('holdings', __name__, template_folder='templates')

from . import holdings_routes

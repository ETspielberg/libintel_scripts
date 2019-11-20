from flask import Blueprint
from . import holdings_routes

holdings_blueprint = Blueprint('holdings', __name__, template_folder='templates')

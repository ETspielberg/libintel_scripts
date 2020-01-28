from flask import Blueprint

stockmanagement_blueprint = Blueprint('stockmanagement', __name__, template_folder='templates')

from . import stockmanagement_routes

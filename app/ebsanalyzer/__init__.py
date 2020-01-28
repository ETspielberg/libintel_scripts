from flask import Blueprint

ebs_analyzer_blueprint = Blueprint('ebs_analyzer', __name__, template_folder='templates')

from . import ebs_analyzer_routes

from flask import Flask
from flask_cors import CORS

from app.facettes import facettes_blueprint


def create_app(config_filename=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_envvar("LIBINTEL_SETTINGS")
    CORS(app)
    register_blueprints(app)
    return app

def register_blueprints(app):
    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    from app.budget import budget_blueprint


    app.register_blueprint(budget_blueprint, url_prefix='/budget')

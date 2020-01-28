import os

from flask import Flask
from flask_cors import CORS


def create_app(config_filename=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_envvar("LIBINTEL_SETTINGS")
    CORS(app)
    register_blueprints(app)
    base_location = app.config.get("LIBINTEL_DATA_DIR")
    create_folders(base_location)
    return app


def register_blueprints(app):
    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    from app.budget import budget_blueprint
    from app.stockmanagement import stockmanagement_blueprint
    from app.ebsanalyzer import ebs_analyzer_blueprint
    from app.holdings import holdings_blueprint

    # app.register_blueprint(budget_blueprint, url_prefix='/budget')
    app.register_blueprint(stockmanagement_blueprint, url_prefix='/stockmanagement')
    app.register_blueprint(ebs_analyzer_blueprint, url_prefix='/ebs')
    app.register_blueprint(holdings_blueprint, url_prefix='/holdings')


def create_folders(base_location):
    if not os.path.exists(base_location):
        os.makedirs(base_location)
    ebs_folder = base_location + '/ebslists/'
    stockmanagement_folder = base_location + '/uploads/public/stockmanagement/'
    if not os.path.exists(ebs_folder):
        os.makedirs(ebs_folder)
    if not os.path.exists(stockmanagement_folder):
        os.makedirs(stockmanagement_folder)


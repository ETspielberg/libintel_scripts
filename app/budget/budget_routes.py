from flask import request
import psycopg2 as psycopg2

import app.BudgetCalculator as bd
from app.budget import budget_blueprint
from flask import current_app as app

# finance_connection = psycopg2.connect(database=app.config.get("LIBINTEL_FINANCE_DATASOURCE_DBNAME"),
#                                       host=app.config.get("LIBINTEL_FINANCE_DATASOURCE_HOST"),
#                                       port=app.config.get("LIBINTEL_FINANCE_DATASOURCE_PORT"),
#                                       user=app.config.get("LIBINTEL_FINANCE_DATASOURCE_USERNAME"),
#                                       password=app.config.get("LIBINTEL_FINANCE_DATASOURCE_PASSWORD")
#                                       )

# calculator = bd.BudgetCalculator(app.config.get("LIBINTEL_DATA_DIR"), finance_connection,
#                                  app.config.get("LIBINTEL_DATA_URL"))


@budget_blueprint.route("/prepare_collection_lists/<year>")
def generate_collection_lists_for_year(year):
#    calculator.generate_collection_lists(year)
    return 'done'


@budget_blueprint.route("/calculate_costs_for collection/<collection>", methods=['POST'])
def calculate_usage_fraction_for_collection_and_year(collection):
    year = request.args.get('year')
    total_costs = request.args.get('totalCosts')
    # calculator.set_journal_collection(collection, year)
    # calculator.read_issn_list()
    # calculator.analyze_usage(total_costs)
    # calculator.distribute_costs()
    # return 'done'

from urllib.error import URLError

import psycopg2 as psycopg2
from flask import Flask, Response

# set namespaces of scopus export
from py_eureka_client import eureka_client

from budget_calculator.BudgetCalculator import BudgetCalculator
from network.NetworkBuilder import NetworkBuilder
from query.QueryExecutor import QueryExecutor
from text_analyzer.TextAnalyzer import TextAnalyzer

app = Flask(__name__)

# define configuration file
app.config.from_envvar("LIBINTEL_SETTINGS")
your_rest_server_port = 5000


# eureka client setup
try:
    eureka_client.init_registry_client(eureka_server="http://localhost:8761/eureka", app_name="scripts",
                                       instance_port=your_rest_server_port)
except URLError:
    print('Could not connect to eureka server')

# define root directory of application
builder = NetworkBuilder(app.config.get("LIBINTEL_DATA_DIR"),
                         app.config.get("LIBINTEL_NEO4J_SERVER"),
                         app.config.get("LIBINTEL_NEO4J_PORT"),
                         app.config.get("LIBINTEL_NEO4J_USERNAME"),
                         app.config.get("LIBINTEL_NEO4J_PASSWORD"))


connection = psycopg2.connect(database=app.config.get("LIBINTEL_DATASOURCE_DBNAME"),
                              host=app.config.get("LIBINTEL_DATASOURCE_HOST"),
                              port=app.config.get("LIBINTEL_DATASOURCE_PORT"),
                              user=app.config.get("LIBINTEL_DATASOURCE_USERNAME"),
                              password=app.config.get("LIBINTEL_DATASOURCE_PASSWORD")
                              )


query_executor = QueryExecutor(app.config.get("ALTMETRIC_API_KEY"),
                               app.config.get("LIBINTEL_USER_EMAIL"),
                               app.config.get("LIBINTEL_DATA_DIR"),
                               connection)

text_analyzer = TextAnalyzer(app.config.get("LIBINTEL_DATA_DIR"), connection)

budget_calculator = BudgetCalculator(app.config.get("LIBINTEL_DATA_DIR"), connection,
                                     app.config.get("LIBINTEL_USAGE_URL"))


# extract zip files in directory
@app.route('/extract_zip_files/<project_id>', methods=['POST'])
def extract_zipfiles(project_id):
    builder.set_project_id(project_id)
    builder.extract_zipfiles()
    return Response("OK", status=204)


# read the classification.csv to enter all classification nodes
@app.route('/read_classifications/<project_id>', methods=['POST'])
def read_classifications(project_id):
    builder.set_project_id(project_id)
    builder.read_classifications()
    return Response("OK", status=204)


# read the institutions.csv to enter all institution nodes and to get a set of institutions
@app.route('/read_institutions/<project_id>', methods=['POST'])
def read_institutions(project_id):
    builder.set_project_id(project_id)
    builder.read_institutions()
    return Response("OK", status=204)


# builds the network of documents and institutions
@app.route('/read_network/<project_id>', methods=['POST'])
def read_network(project_id):
    builder.set_project_id(project_id)
    builder.read_institutions()
    builder.read_network()
    return Response("OK", status=204)


@app.route('/query_execution/<query_id>', methods=['POST'])
def query_execution(query_id):
    query_executor.initalize_query(project_id=query_id)
    query_executor.execute_query()
    query_executor.collect_data('fresh')


@app.route('/restart_query_execution/<query_id>', methods=['POST'])
def restart_query_execution(query_id):
    query_executor.initalize_query(project_id=query_id)
    query_executor.collect_data('restart')


@app.route("/calculateTextrank/<query_id>", method=['POST'])
def calculate_textrank(query_id):
    text_analyzer.initalize_analyzer(query_id)
    text_analyzer.calculate_text_rank()


@app.route("/prepareDataForML/<query_id>", method=['POST'])
def calculate_textrank(query_id):
    text_analyzer.initalize_analyzer(query_id)
    text_analyzer.prepare_machine_learning_data()


@app.route("/getEids/<query_id>", method=['GET'])
def get_eids(query_id):
    query_executor.initalize_query(query_id)
    return query_executor.read_eids('')


@app.route("/getMissedEids/<query_id>", method=['POST'])
def get_missed_eids(query_id):
    query_executor.initalize_query(query_id)
    return query_executor.read_eids('restart')


@app.route("calculate_costs_for collection/<collection>", method=['POST'])
def calculate_usage_fraction_for_collection_and_year(collection, year):
    budget_calculator.set_journal_collection(collection, year)
    budget_calculator.read_issn_list()
    budget_calculator.analyze_usage()

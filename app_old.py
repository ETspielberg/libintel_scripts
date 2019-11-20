from app import create_app

app = create_app()

import psycopg2 as psycopg2
from flask import Flask, Response

# set namespaces of scopus export

from app.NetworkBuilder import NetworkBuilder
from text_analyzer.TextAnalyzer import TextAnalyzer

app = Flask(__name__)
# define configuration file
app.config.from_envvar("LIBINTEL_SETTINGS")

your_rest_server_port = 5000


# eureka client setup
# try:
#     eureka_client.init_registry_client(eureka_server="http://localhost:8761/eureka", app_name="scripts",
#                                        instance_port=your_rest_server_port)
# except URLError:
#     print('Could not connect to eureka server')

# define root directory of application
builder = NetworkBuilder(app.config.get("LIBINTEL_DATA_DIR"),
                         app.config.get("LIBINTEL_NEO4J_SERVER"),
                         app.config.get("LIBINTEL_NEO4J_PORT"),
                         app.config.get("LIBINTEL_NEO4J_USERNAME"),
                         app.config.get("LIBINTEL_NEO4J_PASSWORD"))



data_connection = psycopg2.connect(database=app.config.get("LIBINTEL_DATA_DATASOURCE_DBNAME"),
                              host=app.config.get("LIBINTEL_DATA_DATASOURCE_HOST"),
                              port=app.config.get("LIBINTEL_DATA_DATASOURCE_PORT"),
                              user=app.config.get("LIBINTEL_DATA_DATASOURCE_USERNAME"),
                              password=app.config.get("LIBINTEL_DATA_DATASOURCE_PASSWORD")
                              )


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


@app.route("/calculateTextrank/<query_id>", methods=['POST'])
def calculate_textrank(query_id):
    text_analyzer.initalize_analyzer(query_id)
    text_analyzer.calculate_text_rank()


@app.route("/prepareDataForML/<query_id>", methods=['POST'])
def prepare_data_for_ml(query_id):
    text_analyzer.initalize_analyzer(query_id)
    text_analyzer.prepare_machine_learning_data()


@app.route("/getEids/<query_id>", methods=['GET'])
def get_eids(query_id):
    query_executor.initalize_query(query_id)
    return query_executor.read_eids('')


@app.route("/getMissedEids/<query_id>", methods=['POST'])
def get_missed_eids(query_id):
    query_executor.initalize_query(query_id)
    return query_executor.read_eids('restart')



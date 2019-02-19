import os

from elasticsearch import Elasticsearch

from query.model.AbstractText import AbstractText
from query.model.Project import Project


class TextAnalyzer:
    # first initialization, reading of standard parameters, preparing connections.
    def __init__(self, data_dir, connection):
        self.project_id = ''
        self.path = ''
        self.data_dir = data_dir
        self.es = Elasticsearch()
        self.connection = connection

    def initalize_analyzer(self, project_id):
        self.project_id = project_id
        self.path = self.data_dir + '/query_execution/' + project_id + '/'
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def prepare_machine_learning_data(self):
        project = Project(self.project_id)
        # retrieve list of hits from the index and prepare data for machine learning
        result = self.es.search(index=project.identifier, doc_type='all_data',
                                filter_path=["hits.hits._source.scopus_abtract_retrieval", "hits.hits._id"],
                                request_timeout=600)
        for hit in result["hits"]["hits"]:
            AbstractText(hit['_id'], self.project_id, hit["_source"]["scopus_abtract_retrieval"]["abstract"],
                         hit["_source"]["scopus_abtract_retrieval"]["title"],
                         hit["_source"]["scopus_abtract_retrieval"]["authkeywords"]).save()

    def calculate_text_rank(self):
        print('calculating text rank....')
        path_to_file = self.path + '/abstracts.json'
        return path_to_file
    #     for graf in pytextrank.parse_doc(pytextrank.json_iter(path_to_file)):
    #         print(pytextrank.pretty_print(graf))
    #     return "ok"

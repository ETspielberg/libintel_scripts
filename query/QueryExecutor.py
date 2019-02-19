import json
import os

from query import scopus
from query.altmetric.Altmetric import Altmetric
from query.model.AllResponses import AllResponses
from query.model.Project import Project
from query.model.Query import Query
from query.model.RelevanceMeasures import RelevanceMeasure
from query.model.Status import Status
from query.model.UpdateContainer import UpdateContainer
from elasticsearch import Elasticsearch

from query.scival.Scival import Scival
from query.unpaywall.Unpaywall import Unpaywall


class QueryExecutor:

    # first initialization, reading of standard parameters, preparing connections.
    def __init__(self, scopus_api_key, email, data_dir, connection):
        self.scopus_api_key = scopus_api_key
        self.email = email
        self.project_id = ''
        self.path = ''
        self.data_dir = data_dir
        self.es = Elasticsearch()
        self.connection = connection

    # setting the project id and the corresponding path, initializing for specific run
    def initalize_query(self, project_id):
        self.project_id = project_id
        self.path = self.data_dir + '/query_execution/' + project_id + '/'
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    # execute the query and save the resulting EIDs
    def execute_query(self):
        if self.path == '':
            raise ValueError('no project id given!')

        # collects the project and the query.
        project = Project(self.project_id)
        query = Query(self.project_id)

        # prepares the status file and sets status to running
        status = Status(self.project_id)
        status.set_status("QUERYING")

        # perform the search in Scopus
        search = scopus.ScopusSearch(query.scopus_query, refresh=True, query_id=self.project_id)

        # retrieve the EIDs
        eids = search.EIDS
        print('found ' + str(eids.__len__()) + ' in Scopus')

        # calculate the relevance measures (details only if test data are given)
        relevance_measure = RelevanceMeasure(self.project_id)
        relevance_measure.total_number_of_query_results = eids.__len__()
        status.set_total(relevance_measure.total_number_of_query_results)
        if project.is_testdata:
            with open(self.path + 'test_data.txt') as f:
                test_eids = f.readlines()
                f.close()
                test_eids = [x.strip() for x in test_eids]
            for test_eid in test_eids:
                relevance_measure.number_of_test_entries = test_eids.__len__()
                if test_eid in eids:
                    relevance_measure.true_positives = relevance_measure.true_positives + 1
                relevance_measure.false_positives = relevance_measure.total_number_of_query_results \
                                                    - relevance_measure.true_positives
                relevance_measure.false_negatives = relevance_measure.number_of_test_entries \
                                                    - relevance_measure.true_positives
                if relevance_measure.total_number_of_query_results > 0:
                    relevance_measure.precision = relevance_measure.true_positives / \
                                                  relevance_measure.total_number_of_query_results
                else:
                    relevance_measure.precision = 0
                if relevance_measure.recall > 0:
                    relevance_measure.recall = relevance_measure.true_positives / \
                                               relevance_measure.number_of_test_entries
                else:
                    relevance_measure.recall = 0
        relevance_measure.save()

        # persist EIDs to file to be uploaded to Scival
        self.save_eids_to_file(eids, '')

        status.set_status('EIDS_COLLECTED')

        # store in project that eids have been obtained and saved
        project.set_is_eids_list(True)

    def collect_data(self, mode):
        # prepare mode for further descision, default value to restart
        if mode == '':
            mode = 'restart'
        else:
            mode = mode

        # initialize project and status
        project = Project(self.project_id)
        status = Status(self.project_id)
        status.set_status("COLLECTING")

        # prepare list of missed EIDs
        missed_eids = []

        # read the eids (missed in case of restart, else the ones obtained by the query execution)
        eids = self.read_eids(mode)

        number = eids.__len__()
        if number > 0:
            # if a fresh run is performed, delete the old index.
            if mode == 'fresh':
                self.es.indices.delete(project.identifier, ignore=[400, 404])

            # cycle through all eids and collect the full data from scopus
            for idx, eid in enumerate(eids):
                status.set_progress(idx + 1)

                # print progress
                print('processing entry ' + str(idx) + 'of ' + str(number) + ' entries: ' +
                      str(idx / number * 100) + '%')

                # retrieve data from scopus
                try:
                    scopus_abstract = scopus.ScopusAbstract(eid, view="FULL")
                except:
                    missed_eids.append(eid)
                    continue

                # create new AllResponses object to hold the individual information
                response = AllResponses(eid, project.name, project.identifier)

                # add scopus abstract to AllResponses object
                response.scopus_abtract_retrieval = scopus_abstract

                # get doi and collect unpaywall data and Altmetric data
                doi = scopus_abstract.doi
                if doi is not None:
                    if doi is not "":
                        response.unpaywall_response = Unpaywall(self.email, doi)
                        response.altmetric_response = Altmetric('', doi)
                        response.scival_data = Scival([])

                # send response to elastic search index
                self.send_to_index(response, project.identifier)
        self.save_eids_to_file(eids, 'missed_')
        status.set_status("FINISHED")
        project.set_is_query_run(True)

    def read_eids(self, mode):
        # read the list of EIDs to collect if
        if mode == 'restart':
            path_to_eids = self.path + 'missed_eids_list.txt'
        else:
            path_to_eids = self.path + 'eids_list.txt'
        with open(path_to_eids) as file:
            eids = file.readlines()
            file.close()
            eids = [x.strip() for x in eids]
        return eids

    def save_eids_to_file(self, eids, prefix):
        with open(self.path + prefix + 'eids_list.txt', 'w') as list_file:
            for eid in eids:
                list_file.write(eid + '\n')
            list_file.close()
        print('saved results to disk')

    def send_to_index(self, all_responses: AllResponses, query_id):
        all_responses_json = json.dumps(all_responses, cls=HiddenEncoder)
        res = self.es.index(query_id, 'all_data', all_responses_json, all_responses.id, request_timeout=600)
        print('saved to index ' + query_id)
        return res

    def append_to_index(self, document, eid):
        update_container = UpdateContainer(document)
        update_json = json.dumps(update_container, cls=HiddenEncoder)
        res = self.es.update(index=self.project_id, doc_type="all_data", id=eid, body=update_json)
        print('saved to index ' + self.project_id)
        return res


class HiddenEncoder(json.JSONEncoder):
    def default(self, o):
        return {k.lstrip('_'): v for k, v in o.__getstate__().items()}

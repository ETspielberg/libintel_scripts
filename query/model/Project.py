import json

import requests


class Project:
    project_url = '/api/bibliometrics/project/'

    def __init__(self, project_id):
        self.identifier = project_id
        url = self.project_url + '/' + project_id
        r = requests.get(url)
        if r.status_code == 200:
            self.json = r.json()
            try:
                self.name = self.json['name']
            except KeyError:
                self.name = ''
            try:
                self.is_query_defined = self.json['isQueryDefined']
            except KeyError:
                self.is_query_defined = False
            try:
                self.is_query_run = self.json['isQueryRun']
            except KeyError:
                self.is_query_run = False
            try:
                self.is_testdata = self.json['isTestdata']
            except KeyError:
                self.is_testdata = False
            try:
                self.is_scivaldata_uploaded = self.json['isScivaldataUploaded']
            except KeyError:
                self.is_scivaldata_uploaded = False
            try:
                self.is_eidslist = self.json['isEidslist']
            except KeyError:
                self.is_eidslist = False
            try:
                self.is_index_present = self.json['isIndexPresent']
            except KeyError:
                self.is_index_present = False
            try:
                self.is_data_prepared_for_machine_learning = self.json['isDataPreparedForMachineLearning']
            except KeyError:
                self.is_data_prepared_for_machine_learning = False
        else:
            self.name = ''
            self.is_query_defined = False
            self.is_eidslist = False
            self.is_query_run = False
            self.is_testdata = False
            self.is_index_present = False
            self.is_scivaldata_uploaded = False
            self.is_data_prepared_for_machine_learning = False

    def set_is_query_run(self, is_query_run):
        self.is_query_run = is_query_run
        self.save()

    def set_is_eids_list(self, is_eids_list):
        self.is_eidslist = is_eids_list
        self.save()

    def set_is_data_prepared_for_machine_learning(self, is_data_prepared_for_machine_learning):
        self.is_data_prepared_for_machine_learning = is_data_prepared_for_machine_learning
        self.save()

    def save(self):
        payload = json.dumps(self)
        headers = {'content-type': 'application/json'}
        post = requests.post(self.project_url, data=payload, headers=headers)
        print('saved project with status code ' + post.status_code)

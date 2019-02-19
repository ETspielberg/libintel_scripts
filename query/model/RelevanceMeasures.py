import json

import requests


class RelevanceMeasure:
    relevance_measure_url = '/api/bibliometrics/relevanceMeasure/'

    def __init__(self, project_id):
        self.identifier = project_id
        url = self.relevance_measure_url + '/' + project_id
        r = requests.get(url)
        if r.status_code == 200:
            self.json = r.json()
            try:
                self.recall = self.json['recall']
            except KeyError:
                self.recall = 0
            try:
                self.precision = self.json['precision']
            except KeyError:
                self.precision = 0
            try:
                self.true_positives = self.json['true_positives']
            except KeyError:
                self.true_positives = 0
            try:
                self.false_negatives = self.json['false_negatives']
            except KeyError:
                self.false_negatives = 0
            try:
                self.false_positives = self.json['false_positives']
            except KeyError:
                self.false_positives = 0
            try:
                self.number_of_test_entries = self.json['number_of_test_entries']
            except KeyError:
                self.number_of_test_entries = 0
            try:
                self.total_number_of_query_results = self.json['total_number_of_query_results']
            except KeyError:
                self.total_number_of_query_results = 0

        else:
            self.recall = 0
            self.precision = 0
            self.true_positives = 0
            self.false_negatives = 0
            self.false_positives = 0
            self.number_of_test_entries = 0
            self.total_number_of_query_results = 0

    def save(self):
        payload = json.dumps(self)
        headers = {'content-type': 'application/json'}
        post = requests.post(self.relevance_measure_url, data=payload, headers=headers)
        print('saved project with status code ' + post.status_code)

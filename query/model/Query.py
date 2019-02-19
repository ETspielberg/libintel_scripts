import json

import requests


class Query:
    query_url = '/api/bibliometrics/query/'

    def __init__(self, project_id):
        self.identifier = project_id
        url = self.query_url + '/' + project_id
        r = requests.get(url)
        if r.status_code == 200:
            self.json = r.json()
            try:
                self.affiliation_id = self.json['affiliationId']
            except KeyError:
                self.affiliation_id = ''
            try:
                self.author_id = self.json['authorId']
            except KeyError:
                self.author_id = ''
            try:
                self.author_name = self.json['authorName']
            except KeyError:
                self.author_name = ''
            try:
                self.subject = self.json['subject']
            except KeyError:
                self.subject = ''
            try:
                self.title = self.json['title']
            except KeyError:
                self.title = ''
            try:
                self.topic = self.json['topic']
            except KeyError:
                self.topic = ''
            try:
                self.start_year = self.json['startYear']
            except KeyError:
                self.start_year = ''
            try:
                self.end_year = self.json['endYear']
            except KeyError:
                self.end_year = ''
            try:
                self.scopus_query = self.json['scopusQuery']
            except KeyError:
                self.scopus_query = ''

        else:
            self.affiliation_id = ""
            self.author_id = ""
            self.author_name = ""
            self.subject = ""
            self.title = ""
            self.topic = ""
            self.start_year = 0
            self.end_year = 0
            self.scopus_query = ""

    def save(self):
        payload = json.dumps(self)
        headers = {'content-type': 'application/json'}
        post = requests.post(self.query_url, data=payload, headers=headers)
        print('saved query with status code ' + post.status_code)

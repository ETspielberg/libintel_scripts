import json

import requests


class Status:
    status_url = '/api/bibliometrics/status/'

    def __init__(self, project_id):
        self.identifier = project_id
        url = self.status_url + '/' + project_id
        r = requests.get(url)
        if r.status_code == 200:
            self.json = r.json()
            try:
                self.status = self.json['status']
            except KeyError:
                self.status = 0
            try:
                self.progress = self.json['progress']
            except KeyError:
                self.progress = 0
            try:
                self.total = self.json['total']
            except KeyError:
                self.total = 0
        else:
            self.status = "CREATED"
            self.progress = 0
            self.total = 0

    def set_status(self, status):
        self.status = status
        self.save()

    def set_total(self, total):
        self.total = total
        self.save()

    def set_progress(self, progress):
        self.progress = progress
        self.save()

    def save(self):
        payload = json.dumps(self)
        headers = {'content-type': 'application/json'}
        post = requests.post(self.status_url, data=payload, headers=headers)
        print('saved status with status code ' + post.status_code)

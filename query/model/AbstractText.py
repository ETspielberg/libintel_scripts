import json

import requests


class AbstractText:
    abstract_url = '/api/bibliometrics/abstractText'

    def __init__(self, identifier, eid, title, keywords, text):
        self.identifier = identifier
        self.id = eid
        self.title = title
        self.keywords = keywords
        self.text = text

    def save(self):
        payload = json.dumps(self)
        headers = {'content-type': 'application/json'}
        post = requests.post(self.abstract_url, data=payload, headers=headers)
        print('saved abstract text with status code ' + post.status_code)

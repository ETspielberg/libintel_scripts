import os
import zipfile
import pathlib
import csv

import xml.etree.ElementTree as ET
from neomodel import config

from app.network.model.document import Classification, Document, Institution


class NetworkBuilder:

    def __init__(self, upload_dir, server, port, username, password):
        config.DATABASE_URL = 'bolt://' + username + ':' + password + '@' + server + ':' + port
        self.institutions_set = set()
        self.upload_dir = upload_dir
        self.project_id = ''
        self.path = ''

    def set_project_id(self, project_id):
        self.project_id = project_id
        self.path = self.upload_dir + '/network_builder/' + project_id + '/'

    def extract_zipfiles(self):
        for path, subdirs, files in os.walk(self.path):
            for name in files:
                if name.endswith('.zip'):
                    print('extracting file ' + name)
                    zipfile_obj = zipfile.ZipFile(path + "\\" + name)
                    zipfile_obj.extractall(path)
        print('finished extracting zip files')
        return True

    def read_classifications(self):
        print('reading classifications csv')
        with open(pathlib.PurePath(self.path, 'classifications.csv'), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in spamreader:
                print('reading classification ' + row[0])
                Classification(short=row[0], name=row[1], source=row[2], project_id=self.project_id).save()

    def read_institutions(self):
        institutions_set = set()
        print('reading institutions csv')
        with open(pathlib.PurePath(self.path, 'institutions.csv'), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                if len(row) > 1:
                    print('reading institution ' + row[0])
                    institutions_set.add(row[0])
                    Institution(affiliation_id=row[0], name=row[1], short=row[2], project_id=self.project_id).save()
        return institutions_set

    def read_network(self):
        scopus_ns = {'xocs': 'http://www.elsevier.com/xml/xocs/dtd',
                     'ce': 'http://www.elsevier.com/xml/ani/common',
                     'ait': 'http://www.elsevier.com/xml/ani/ait',
                     'cto': 'http://www.elsevier.com/xml/cto/dtd',
                     'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

        for path, subdirs, files in os.walk(self.path):
            for name in files:
                print('looking at file ' + name)
                if name.endswith('.xml'):
                    xml = ET.parse(path + "/" + name).getroot()
                    eid = xml.find('xocs:meta', scopus_ns).find('xocs:eid', scopus_ns).text
                    bibrecord = xml.find('xocs:item', scopus_ns).find('item').find('bibrecord', scopus_ns)
                    head = bibrecord.find('head', scopus_ns)
                    title = head.find('citation-title', scopus_ns) \
                        .find('titletext', scopus_ns).text
                    try:
                        year = head.find('source').find('publicationdate').find('year', scopus_ns).text
                    except AttributeError:
                        year = 0
                    try:
                        doi = bibrecord.find('item-info').find('itemidlist').find('ce:doi', scopus_ns).text
                    except AttributeError:
                        doi = ''
                    document = Document(eid=eid, year=year, citation_count=0, title=title, doi=doi,
                                        project_id=self.project_id).save()
                    for author_group in head.findall('author-group'):
                        try:
                            af_id = author_group.find('affiliation').get('afid')
                            print(af_id)
                            if af_id in self.institutions_set:
                                institution = Institution.nodes.get_or_none(affiliation_id=af_id)
                                print(institution)
                                if institution is not None:
                                    document.institution.connect(institution)
                                    print('connecting institution')
                                document.save()
                        except AttributeError:
                            print('no affiliation given')
                    print('saved document')
        return 'done'

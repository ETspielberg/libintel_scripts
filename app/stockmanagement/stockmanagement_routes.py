import json
import os
import urllib

import numpy as np
import pandas as pd
import requests
from flask import current_app as app

from . import stockmanagement_blueprint


@stockmanagement_blueprint.route("/build_from_file")
def process_list(filename):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/uploads/public/stockmanagement/' + filename
    table = pd.read_csv(path_to_file, sep=';', dtype={'ADM-Satz': object, 'ADM': object})
    sigel_score = pd.read_csv('sigel_score.txt')
    sigel_score.index = sigel_score['sigel']
    table['link'] = np.vectorize(generate_link)(table['Titel'], table['Verfasser'], table['Jahr'])
    number_libs = []
    libs = []
    scores = []
    comments = []
    for index, row in table.iterrows():
        print('processing entry ' + str(index + 1) + ' of ' + str(len(table.index)))
        score = 0
        number_lib = 0
        owners = ''
        comment = ''
        try:
            r = requests.get(row['link'])
            if r.status_code is 200:
                json_object = json.loads(r.content)
                if json_object['member'].__len__() > 0:
                    for member in json_object['member']:
                        # if no hasItem element is present, set comment and continue with next member
                        try:
                            held_item_list = member['hasItem']
                        except KeyError:
                            comments = "no hasItem element given in Lobid response"
                            continue
                        number_lib = held_item_list.__len__()
                        for owner in held_item_list:
                            if owners.__len__() > 1:
                                owners = owners + ", "
                            individual_owner = urllib.parse.unquote(owner['id'].partition('DE-')[2].replace("#!", ""))
                            sigel = individual_owner.partition(":")[0]
                            try:
                                score = score + sigel_score.loc[int(sigel)].score
                            except:
                                pass
                            owners = owners + individual_owner
                            if '465:' in owners:
                                break
                            if '464:' in owners:
                                break

                else:
                    comment = "no members given in Lobid response"
            else:
                comment = "response code of Lobid API not 200: " + str(r.status_code)
        except:
            comment = "error in connecting to Lobid API (most probably timeout)"
        comments.append(comment)
        scores.append(score)
        number_libs.append(number_lib)
        libs.append(owners)
    table['fernleih_score'] = np.array(scores)
    table['Anzahl Bibliotheken'] = np.array(number_libs)
    table['Bibliotheken'] = np.array(libs)
    table['comments'] = np.array(comments)
    table.drop('link', axis=1, inplace=True)
    table.to_csv(filename.partition('.')[0] + '_checked-nrw.csv')


def generate_link(title, author, year):
    if title.startswith('Bd.'):
        title_parts = title.split('.')
        query_string = 'title:' + title_parts[-1]
    else:
        query_string = 'title:' + title.replace('.', '')
    if author is not '':
        query_string = query_string + ' AND contribution.agent.label:' + str(author).partition(',')[0]
    if year is not '' and not None:
        query_string = query_string + ' AND publication.startDate:' + str(year)
    link = 'https://lobid.org/resources/search?q=' + urllib.parse.quote_plus(query_string) + '&format=json'
    return link


def load_blacklist():
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    blacklist = []
    files = [f for f in os.listdir('.') if f.startswith('blacklist')]
    for file in files:
        with open(file) as f:
            blacklist.append(f.readlines())
            f.close()
    return set(blacklist)


def check_blacklist(filename):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    table = pd.read_csv(filename, sep=';', dtype={'ADM-Satz': object, 'ADM': object})
    blacklist = load_blacklist()
    for index, row in table.iterrows():
        if row['ADM-Satz'] in blacklist:
            table.drop(index, axis=0)

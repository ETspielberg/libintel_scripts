import json
import urllib

from flask import request, Response, jsonify
import os
import csv
import re
import requests

import pandas as pd
import numpy as np

from app.holdings import holdings_blueprint
from flask import current_app as app

from services import list_service
from services.list_service import save_list, load_list
from services.scopus_statistics_service import collect_scopus_data_for_issn_list, collect_data


@holdings_blueprint.route('/providerAnalysis/forPublisher/<provider>')
def collect_publications_per_affiliation_and_publisher(provider):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
        af_ids = app.config.get("LIBINTEL_SCOPUS_AF_IDS")
    base_directory = location + '/providerAnalysis/' + provider + '/'
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    table = pd.read_csv(base_directory + 'issn_list.csv', sep=';', dtype={'eISSN': object, 'pISSN': object})
    table['search'] = np.vectorize(add_or)(table['pISSN'], table['eISSN'])
    eids = collect_scopus_data_for_issn_list(issn_list=table['search'].to_list(), af_ids=af_ids)
    save_list(project=provider, item_list=eids, prefix='issn')
    return jsonify(eids)


@holdings_blueprint.route('/providerAnalysis/data/<provider>')
def collect_data_per_affiliation_and_publisher(provider):
    eids = load_list(project=provider, prefix='issn')
    with app.app_context():
        keys = app.config.get("LIBINTEL_SCOPUS_KEYS")
        location = app.config.get("LIBINTEL_DATA_DIR")
    base_directory = location + '/providerAnalysis/' + provider + '/'
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    abstracts, missed_eids = collect_data(keys=keys, eids=eids)
    list_service.save_list(project=provider, item_list=missed_eids, prefix='missed_')
    rows_list = []
    for abstract in abstracts:
        dict = {}
        try:
            dict['eid'] = abstract.eid
        except AttributeError:
            dict['eid'] = ''
        try:
            dict['title'] = abstract.title
        except AttributeError:
            dict['title'] = ''
        try:
            dict['doi'] = abstract.doi
        except AttributeError:
            dict['doi'] = ''
        try:
            dict['corresponding_organization'] = abstract.correspondence.organization
        except AttributeError:
            dict['corresponding_organization'] = ''
        try:
            dict['year'] = abstract.coverDate[0:4]
        except AttributeError:
            dict['year'] = ''
        try:
            dict['date'] = abstract.coverDate
        except AttributeError:
            dict['date'] = ''
        try:
            areas = ''
            for area in abstract.subject_areas:
                areas += ' ' + area.abbreviation
            dict['subjects'] = areas
        except AttributeError:
            dict['subjects'] = ''
        rows_list.append(dict)
    df = pd.DataFrame(rows_list)
    df.to_excel(base_directory + 'result.xlsx')
    return Response({"status": "FINISHED"}, status=200)


def add_or(p_issn, e_issn):
    string = ''
    if type(p_issn) is str:
        string = string + p_issn + ' OR '
    if type(e_issn) is str:
        string = string + e_issn + ' OR '
    return string


@holdings_blueprint.route("/build_from_file")
def generate_holding_files():
    filename = request.args.get('filename', default='holdings.csv')
    number_of_entries = request.args.get('entries_count', default='25000')
    provider = request.args.get('provider', default='Buchbestand')
    medium_type = request.args.get('medium_type', default='book_electronic')
    is_ready = read_isbn_list(filename, number_of_entries, provider, medium_type)
    if is_ready:
        return Response({"status": "FINISHED"}, status=200)
    else:
        return Response({'status': 'error'}, status=500)


def clean_up_isbn(isbn):
    if '$$a' in isbn:
        pass
    elif '$$' in isbn:
        isbn = isbn.rsplit('$$')[0]
    isbn = isbn.replace('-', '')
    isbn = isbn.replace('(', '')
    isbn = isbn.replace('!', '')
    isbn = isbn.replace('$$a', '')
    print(isbn)
    return isbn


def read_isbn_list(filename, number_of_lines, provider, medium_type):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    base_directory = location + '/' + provider + '/'
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    with open(filename, 'r', encoding="utf8") as csvfile:

        # Dateiname der XML-Datei (ersetzen der Dateiendung (wahrscheinlich .csv oder .txt durch .xml
        xml_filename = filename.rsplit('.')[0] + '.xml'

        title = ''

        with open(base_directory + xml_filename, 'w', encoding="utf-8") as xml_file:

            # leere Liste an ISBNS
            isbns = []

            # Zähler für Einträge pro Datei auf 0 setzen
            entry_counter = 0

            # Zähler für Ausgabedateien auf 1 setzen
            number = 1

            # Target-Namen generieren
            target_name = provider + str(number)

            # csv-Datei einlesen mit ; als Trennzeichen

            if 'aseq' in filename:
                linereader = csv.reader(csvfile, delimiter='\t')
            else:
                linereader = csv.reader(csvfile, delimiter=';')

            # Alle Zeilen durcharbeiten:
            for line in linereader:
                field = line[0][10:14]

                # Wenn die Zeile zu wenig Einträge enthält, diesen Eintrag überspringen
                if line.__len__() < 4 and 'aseq' not in filename:
                    continue
                if 'aseq' in filename:
                    if '331' in field:
                        title = line[0][18:].replace('$$a', '')
                    if '540a' in field:
                        isbn = line[0][18:]
                    else:
                        continue
                else:
                    isbn = line[2]
                isbn = clean_up_isbn(isbn)

                # prüfen, ob nur Zahlen, X, x und Leerzeichen enthalten sind. Falls nicht, diesen Eintrag überspringen
                search = re.compile('^[0-9Xx ]*$').search
                if not bool(search(isbn)):
                    continue

                # Schreiben des entsprechenden XML-Eintrages
                entry = '<item type = "electronic">\n<isbn>' + isbn + '</isbn>\n</item>\n'
                xml_file.write(entry)

                # Eintrg der Liste an ISBNs hinzufügen (\t ist Tabstopp)
                if 'book' in medium_type:
                    isbns.append(title + '\t' + isbn + '\t' + target_name)
                else:
                    isbns.append(isbn + '\t' + target_name)

                # Zähler erhöhen
                entry_counter = entry_counter + 1

                # nur wenn der Zähler die Anzahl an Zeilen erreicht:
                if entry_counter == number_of_lines:

                    # Zähler zurücksetzen
                    entry_counter = 0

                    # komplette ISBN-List in Datei schreiben
                    with open(base_directory + target_name + '.txt', 'w', encoding='utf-8') as list_file:

                        # Header schreiben
                        if 'book' in medium_type:
                            list_file.write('#Fields:\tBook Name\t ISBN\t Provider\n')
                        else:
                            list_file.write('#Fields:\t ISBN\t Provider\n')

                        # dann alle einzelnen Einträge schreiben
                        for isbn in isbns:
                            list_file.write(isbn + '\n')

                        # Datei wieder schließen
                        list_file.close()

                    # Zähler für Dateien erhöhen
                    number = number + 1

                    # neun Target-Namen generieren
                    target_name = provider + str(number)

                    # Liste wieder leeren
                    isbns = []

            # die letzte Liste wird dann in die letzte Datei geschrieben
            with open(base_directory + target_name + '.txt', 'w', encoding='utf-8') as list_file:
                # Header schreiben
                if 'book' in medium_type:
                    list_file.write('#Fields:\tBook Name\t ISBN\t Provider\n')
                else:
                    list_file.write('#Fields:\t ISBN\t Provider\n')

                # dann alle einzelnen Einträge schreiben
                for isbn in isbns:
                    list_file.write(isbn + '\n')

                # Datei schließen
                list_file.close()

            # XML-DAtei schließen
            xml_file.close()
        # CSV-Datei schließen
        csvfile.close()
    return True


@holdings_blueprint.route("/check_hbz_holdings")
def check_hbz_holdings():
    filename = request.args.get('filename', default='list.csv')
    is_ready = process_list(filename)
    if is_ready:
        return Response({"status": "FINISHED"}, status=200)
    else:
        return Response({'status': 'error'}, status=500)


def generate_link(title, author, year):
    query_string = 'title:' + title.replace('.', '')
    if author is not '':
        query_string = query_string + ' AND contribution.agent.label:' + str(author).partition(',')[0]
    if year is not '' and not None:
        query_string = query_string + ' AND publication.startDate:' + str(year)
    link = 'https://lobid.org/resources/search?q=' + urllib.parse.quote_plus(query_string) + '&format=json'
    return link


def process_list(filename):
    table = pd.read_csv(filename, sep=';')
    sigel_score = pd.read_csv('sigel_score.txt')
    sigel_score.index = sigel_score['sigel']
    table['link'] = np.vectorize(generate_link)(table['Titel'], table['Verfasser'], table['Jahr'])
    number_libs = []
    libs = []
    scores = []
    for index, row in table.iterrows():
        print('processing entry ' + str(index+1) + ' of ' + str(len(table.index)))
        r = requests.get(row['link'])
        score = 0
        if r.status_code is 200:
            json_object = json.loads(r.content)
            if json_object['member'].__len__() > 0:
                try:
                    held_item_list = json_object['member'][0]['hasItem']
                    number_libs.append(held_item_list.__len__())
                    owners = ""
                    score = 0
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
                    libs.append(owners)
                except KeyError:
                    number_libs.append(0)
                    libs.append("")
            else:
                number_libs.append(0)
                libs.append("")
        else:
            number_libs.append(0)
            libs.append("")
        scores.append(score)
    table['fernleih_score'] = np.array(scores)
    table['Anzahl Bibliotheken'] = np.array(number_libs)
    table['Bibliotheken'] = np.array(libs)
    table.drop('link', axis=1, inplace=True)
    try:
        table.to_csv(filename.partition('.')[0] + '_checked-nrw.csv')
        return True
    except IOError:
        return False

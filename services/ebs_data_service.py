import csv
import json
import os

import requests
from flask import current_app as app

from app.ebsanalyzer.EbsTitle import EbsTitle


def load_data(filename, ebs_model):
    location = app.config.get("LIBINTEL_DATA_DIR") + "\\ebslists\\"
    with open(location + filename, 'r', encoding='utf-8-sig') as csvfile:
        linereader = csv.reader(csvfile, delimiter=';')
        if not os.path.exists(location + "\\" + ebs_model + "\\"):
            os.makedirs(location + "\\" + ebs_model + "\\")
        ebs_titles = []
        for row in linereader:
             print(row)
             try:
                isbn = row[0]
                title = row[1]
                if ";" in title:
                    title.replace(";", ".")
                subject_area = row[2]
                price_string = row[5]
                if "," in price_string:
                    price_string = price_string.replace(",", ".")
                try:
                    price = float(price_string)
                except ValueError:
                    price = 0
                try:
                    year = int(row[3][-4:])
                except ValueError:
                    year = 0
                total_usage_string = row[4]
                if "." in total_usage_string:
                    total_usage_string = total_usage_string.replace(".", "")
                try:
                    total_usage = int(total_usage_string)
                except ValueError:
                    total_usage = 0
                if total_usage != 0:
                    cost_per_usage = price / total_usage
                else:
                    cost_per_usage = price
                ebs_title = EbsTitle(isbn, title, subject_area, price, year, total_usage, cost_per_usage, True, True,
                                     False, ebs_model, 1)
                ebs_titles.append(ebs_title)
             except ValueError:
                print('no values')
    return ebs_titles


def persist_ebs_list(ebs_titles):
    payload = json.dumps([ob.__dict__ for ob in ebs_titles])
    url = 'http://localhost:11200/ebsData/saveList'
    headers = {'content-type': 'application/json'}
    post = requests.post(url, data=payload, headers=headers)
    print(post.status_code)


def save_ebs_list_file(ebs_titles, ebs_filename, ebs_model, ebs_mode):
    location = app.config.get("LIBINTEL_DATA_DIR") + "\\ebslists\\"
    filename = location + "\\" + ebs_model + "\\" + ebs_filename.replace(".csv", "_") + ebs_mode + "_out.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['ISBN', 'Title', 'Subject area', 'price', 'year', 'total usage', 'price per usage', 'selected', 'EBS model ID', 'weighting factor'])
        for item in ebs_titles:
            spamwriter.writerow([item.isbn, '"' + item.title + '"', item.subject_area, str(item.price), str(item.year), str(item.total_usage), str(item.cost_per_usage), str(item.selected), ebs_model, str(item.weighting_factor)])

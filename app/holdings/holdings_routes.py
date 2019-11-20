from flask import request, Response
import os
import csv
import re

from app.holdings import holdings_blueprint
from flask import current_app as app

with app.app_context():
    location = app.config.get("LIBINTEL_DATA_DIR")


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
            id = 0

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
                id = id + 1

                # nur wenn der Zähler die Anzahl an Zeilen erreicht:
                if id == number_of_lines:

                    # Zähler zurücksetzen
                    id = 0

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


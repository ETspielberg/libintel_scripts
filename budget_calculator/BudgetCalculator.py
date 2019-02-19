import requests

sql_insert = "INSERT INTO usage_fraction (issn, year, fraction_usage) VALUES (%s, %s, %s);"


class BudgetCalculator:

    def __init__(self, upload_dir, connection, data_url):
        self.connection = connection
        self.issn_set = set()
        self.upload_dir = upload_dir
        self.journal_collection = ''
        self.file = ''
        self.data_url = data_url
        self.year = 0

    def set_journal_collection(self, journal_collection, year):
        self.journal_collection = journal_collection
        self.year = year
        self.file = self.upload_dir + '/budgetcalculator/' + year + '_' + journal_collection + '.txt'

    def save_issn_list(self):
        with open(self.file, 'w') as list_file:
            for issn in self.issn_set:
                list_file.write(issn + '\n')
            list_file.close()
        print('saved issns to disk')

    def read_issn_list(self):
        for line in open(self.file):
            if ";" in line:
                for issn in line.split(";"):
                    self.issn_set.add(issn)
            else:
                self.issn_set.add(line)

    def analyze_usage(self):
        total_usage = 0
        usages = {}
        for issn in self.issn_set:
            url = self.data_url + '/journalcounter/getForIssn?issn=' + issn
            r = requests.get(url)
            if r.status_code == 200:
                usage = r.json()['totalRequests']
                usages[issn] = usage
                total_usage = total_usage + usage
        usage_fraction = {}
        cursor = self.connection.cursor()
        for issn in self.issn_set:
            usage_fraction[issn] = usages[issn] / total_usage
            cursor.execute(sql_insert, (issn, self.year, usage_fraction))
            self.connection.commit()
        cursor.close()
        return usage_fraction

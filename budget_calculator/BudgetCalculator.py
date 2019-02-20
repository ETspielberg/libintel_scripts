import requests

sql_insert = "INSERT INTO usage_fraction (issn, year, fraction_usage) VALUES (%s, %f, %f);"
sql_add_subject = "UPDATE usage_fraction SET subject = ezb_list.fach FROM ezb_list WHERE ezb_list.e_issn = usage_fraction.issn;"
sql_get_all = "SELECT * FROM usage_fraction;"
sql_insert_fractional_costs = "INSERT INTO fractional_costs (issn, subject, fractional_cost) VALUES (%s, %s, %f);"
sql_get_all_anchors = "SELECT distinct anchor FROM ezb_list ORDER BY anchor;"
sql_get_issns_for_anchor = "SELECT e_issn FROM ezb_list WHERE anchor = %s;"

class BudgetCalculator:

    def __init__(self, upload_dir, connection, data_url):
        self.connection = connection
        self.issn_set = set()
        self.upload_dir = upload_dir
        self.journal_collection = ''
        self.file = ''
        self.data_url = data_url
        self.year = 0
        self.usage_fraction = {}
        self.cost_per_issn = {}

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

    def analyze_usage(self, total_costs):
        total_usage = 0
        usages = {}
        for issn in self.issn_set:
            url = self.data_url + '/journalcounter/getForIssn?issn=' + issn
            r = requests.get(url)
            if r.status_code == 200:
                usage = r.json()['totalRequests']
                usages[issn] = usage
                total_usage = total_usage + usage
        cursor = self.connection.cursor()
        for issn in self.issn_set:
            usage_fraction = usages[issn] / total_usage
            cost_per_issn = usage_fraction * total_costs
            cursor.execute(sql_insert, (issn.trim(), self.year, usage_fraction, cost_per_issn))
            self.connection.commit()
        cursor.execute(sql_add_subject)
        cursor.close()
        return 'done'

    def distribute_costs(self):
        cursor = self.connection.cursor()
        cursor.execute(sql_get_all)
        for row in cursor.fetchall():
            issn = row[0]
            fractional_costs = row[2]
            subjects_field = row[3]
            if subjects_field is None:
                print('could not distirbute costs (' + str(fractional_costs) + ') for ' + issn)
                continue
            if ";" in subjects_field:
                subjects = subjects_field.split(";")
                parts = len(subjects)
                for subject in subjects:
                    cursor.execute(sql_insert_fractional_costs, (issn, subject, fractional_costs / parts))
            else:
                cursor.execute(sql_insert_fractional_costs, (issn, subjects_field, fractional_costs))
        cursor.close()

    def generate_collection_lists(self, year):
        cursor = self.connection.cursor()
        cursor.execute(sql_get_all_anchors)
        for anchor_found in cursor.fetchall():
            if anchor_found[0] is None:
                continue
            anchor = anchor_found[0].replace("?", "maybe")

            cursor.execute(sql_get_issns_for_anchor, (anchor,))
            issns_list = cursor.fetchall()
            print("found " + str(len(issns_list)) + " issns in anchcr " + anchor)
            if issns_list is None:
                print('issns is None for collection ' + anchor)
                continue
            if len(issns_list) == 0:
                print('empty issn list for collection ' + anchor)
                continue
            filename = self.upload_dir + '/budgetcalculator/' + str(year) + '_' + anchor + '.txt'
            with open(filename, 'w') as list_file:
                for issn_tuple in issns_list:
                    issn = issn_tuple[0]
                    if issn is None:
                        continue
                    if issn == '':
                        continue
                    for issn_ind in issn.split(";"):
                        list_file.write(issn_ind + '\n')
                list_file.close()

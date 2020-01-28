from pybliometrics import scopus
from pybliometrics.scopus import ScopusSearch
from pybliometrics.scopus.exception import Scopus404Error


def collect_scopus_data_for_issn_list(issn_list, af_ids):
    """
    given a list of issns a affiliation id a list of publications is retrieved
    :param issn_list: List of ISSN for which the corresponding publications shall be returned
    :param af_id: the affiliation ID of the institution
    :return: a list of EIDs
    """
    # number of ISSNs packed into one API call
    number_per_call = 100

    if issn_list is None:
        return []

    # calculate the number of API calls based on the number of ISSNs and the number of calls
    number_of_calls = int(len(issn_list) / number_per_call)
    print('performing {} calls to the scopus API'.format(number_of_calls))
    # prepare empty list of eids
    eids = []
    af_ids_string = ''
    for af_id in af_ids:
        print(af_id)
        if af_ids_string is not '':
            af_ids_string += ' OR '
        af_ids_string += 'AF-ID(' + af_id + ')'
        print(af_ids_string)

    # general search string for affiliation ID and ISSN
    search_string = '({afids}) AND ISSN({issns})'
    for n in range(0, number_of_calls):
        # perform he individual API calls
        print('making call {} of {}'.format(n, number_of_calls))

        # prepare the search string for the ISSNs
        issn_string = ''.join(issn_list[n * number_per_call:(n + 1) * number_per_call])

        print(search_string.format(afids=af_ids_string, issns=issn_string[:-4]))

        # perform the scopus search and add the individual eids to the list
        search = ScopusSearch(search_string.format(afids=af_ids_string, issns=issn_string[:-4]))
        eids += search.get_eids()
    return eids


def collect_data(keys, eids):
    """
    collects the data for one API key and a list of eids
    :param key: the API key to be used
    :param eids: a list of EIDs for which the full data shall be collected
    :return: a list of scopus abstract retrieval object
    """
    # prepare the empty lists for missed EIDs and collected abstracts
    missed_eids = []
    abstracts = []

    # if keys is a list of API keys, split the number of EIDs to be collected and collect each individual abstracts
    if type(keys) is tuple:
        pass

    # if only one key is provided collect the abstract one by one.
    else:
        # set the API key
        # scopus.config['Authentication']['APIKEY'] = keys

        for idx, eid in enumerate(eids):

            print('collecting entry {} of {}'.format(idx, len(eids)))
            # retrieve data from scopus
            try:
                scopus_abstract = scopus.AbstractRetrieval(identifier=eid, id_type='eid', view="FULL", refresh=False)
                abstracts.append(scopus_abstract)
            except IOError:
                print('could not collect data for EID ' + eid)
                missed_eids.append(eid)
                continue
            except Scopus404Error:
                print('could not find EID {} in scopus api'.format(eid))
                missed_eids.append(eid)
    return abstracts, missed_eids

import os

from flask import current_app as app


def load_list(project, list_type='eid', prefix='', module='providerAnalysis'):
    """
    loads a list of strings from a txt file
    :param project: the project id
    :param list_type: the type of list, e.g. eid, isbn, issn etc.
    :param prefix: the prefix for the list to be saved (fixed, missed, etc.)
    :param module: the module for which the list is retrieved
    :return: the list of strings
    """
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    # path to the file
    path_to_file = location + '/' + module + '/' + project + '/' + prefix + '_' + list_type + '_list.txt'
    if not os.path.exists(path_to_file):
        return []
    with open(path_to_file) as f:
        eids = f.readlines()
        f.close()
        # remove whitespace characters like `\n` at the end of each line
    return [x.strip() for x in eids]


def save_list(project, item_list, list_type='eid', prefix='', module='providerAnalysis'):
    """
    saves a list of strings to a txt file
    :param project: the project id
    :param list_type: the type of list, e.g. eid, isbn, issn etc.
    :param prefix: the prefix for the list to be saved (fixed, missed, etc.)
    :param module: the module for which the list is retrieved
    :param item_list: the list to be saved
    :return: a boolean indicating whether the saving was successful
    """
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    folder = location + '/' + module + '/' + project + '/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    try:
        with open(folder + prefix + '_' + list_type + '_list.txt', 'w') as list_file:
            for item in item_list:
                list_file.write(item + '\n')
            list_file.close()
        return True
    except IOError:
        return False

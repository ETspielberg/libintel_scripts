import os

from services import ebs_data_service
from services.list_service import load_list
from . import ebs_analyzer_blueprint
from .EbsAnalyzer import EbsAnalyzer as Analyzer
from flask import current_app as app, request


@ebs_analyzer_blueprint.route('/ebslists', methods=['POST'])
def ebslist():
    """
    takes the information from the request body, loads the corresponding file and applies the selected model
    parameters provided as request form parameters:
    filename - the name of the file that holds the usage data
    model - the model name for the analysis
    mode - the mode of analysis to be applied
    limit - the amount of money to be distributed
    :return: the final price of the selected titles
    """

    # reading parameters from HTTP-request
    ebs_filename = request.form['filename']
    ebs_model = request.form['model']
    ebs_mode = request.form['mode']
    ebs_limit = float(request.form['limit'])

    # prepare the base location for this module
    base_location = app.config.get("LIBINTEL_DATA_DIR") + "/ebslists/"
    location = base_location + ebs_model + '/'
    if not os.path.exists(location):
        os.makedirs(location)

    # load the data from the data file in the upload directory
    ebs_titles = ebs_data_service.load_data(ebs_filename, ebs_model)

    # load the list of isbns for titles which are fixed to be selected. add these to the list of fixed titles, set the
    # selected boolean to true and reduce the amount of available money by the price
    fixed_isbns = load_list(ebs_model, module='ebslists', list_type='isbn', prefix='fixed')
    fixed_titles = []
    for title in ebs_titles:
        if title.isbn.strip() in fixed_isbns:
            title.selected = True
            fixed_titles.append(title)
            ebs_limit -= title.price

    # remove the fixed titles from the list of ebs titles.
    ebs_titles = [item for item in ebs_titles if item not in fixed_titles]

    # make the selection, i.e. set the boolean "selected" and weighting factors if necessary
    analyzer = Analyzer(ebs_mode)
    selected_sum = analyzer.make_selection(ebs_limit=ebs_limit, ebs_titles=ebs_titles)

    # add the fixed ebs titles to the list of selection
    ebs_titles += fixed_titles

    # persist the results to the database in order to offer them to the fachref-assistant
    # ebs_data_service.persist_ebs_list(ebs_titles)

    # save the results to a out-file in the upload directory
    ebs_data_service.save_ebs_list_file(ebs_titles, ebs_filename, ebs_model, ebs_mode)
    return '{} of {} were spent by selection'.format(selected_sum, ebs_limit)

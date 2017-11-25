# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

from appurl import parse_app_url
from itertools import islice


def extract(resource, doc, *args, **kwargs):
    """Extract rows from an FFIEC disclosire file, from a collection of Root.References,
    for a given prefix

    This function is used as a program URL in a Root.DataFile term:

    Section: Resources
    DataFile:       python:publicdata.ffiec#extract
    Datafile.Name:  sb_loan_orig
    Datafile.Schema:cra_disclosure
    Datafile.Prefix:D1-1

    The schema for the table must be specified, because the rows are fixed width, so
    the schema must have a Column.Width for each column.

    The function also expects that all of the references in the document refer to FFEIC file, such as:

    Section: References
    Reference: https://www.ffiec.gov/cra/xls/15exp_discl.zip
    Reference.Name: discl_15
    Reference: https://www.ffiec.gov/cra/xls/14exp_discl.zip
    Reference.Name: discl_14
    Reference: https://www.ffiec.gov/cra/xls/13exp_discl.zip
    Reference.Name: discl_13
    Reference: https://www.ffiec.gov/cra/xls/12exp_discl.zip
    Reference.Name: discl_12
    Reference: https://www.ffiec.gov/cra/xls/11exp_discl.zip
    Reference.Name: discl_11
    Reference: https://www.ffiec.gov/cra/xls/10exp_discl.zip
    Reference.Name: discl_10


    """

    test = bool(resource.get_value('test', False))

    prefix = resource.prefix

    table = resource.row_processor_table()

    yield table.headers

    parser = table.make_fw_row_parser(ignore_empty=True)

    for r in doc.references():

        print("Processing ", r.name)

        t = parse_app_url(r.url).get_resource().get_target()

        with open(t.path, 'rU') as f:

            for line in (islice(f.readlines(), 10) if test else f.readlines()):
                if not line.startswith(prefix+' '):
                    continue

                yield parser(line)

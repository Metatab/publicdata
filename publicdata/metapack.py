# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""Functions for use with metapack"""

def combine(resource, doc, *args, **kwargs):
    """A Datafile generating function that combines other references that are assigned to a group.

    The functions will combine the CSV rows from references that are given the same row. It is assumed
    that all files have the same header. The header will be emitted from the first file,
    but not from any others.

    Section: References

    Reference: http://seshat.datasd.org/pd/pd_calls_for_service_2015_datasd.csv
    Reference.Name: pd_calls_2015
    Reference.Group: pd_calls

    Reference: http://seshat.datasd.org/pd/pd_calls_for_service_2016_datasd.csv
    Reference.Name: pd_calls_2016
    Reference.Group: pd_calls

    Reference: http://seshat.datasd.org/pd/pd_calls_for_service_2017_datasd.csv
    Reference.Name: pd_calls_2017_ytd
    Reference.Group: pd_calls

    Section: Resources

    Datafile: python:publicdata.metapack#combine
    Datafile.Name: pd_calls
    Datafile.Group: pd_calls


    """

    from itertools import islice



    for i, r in enumerate(doc.references()):
        if r.get_value('group') == resource.get_value('group') or r.get_value('group') == resource.get_value('name'):

            try:
                start = int(r.get_value('startline', 1))
            except ValueError as e:
                start = 1

            if i == 0:
                yield from r
            else:
                yield from islice(r, start, None)



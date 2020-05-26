# Copyright (c) 2020 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""Support code for Metapack data packages"""

from rowgenerators import parse_app_url


def fred_frame(resource, doc, env, *args, **kwargs):
    """A Resource generator for Metapack that will read all of the FredSeries
    entries in the References section and generate a single dataframe"""

    start = doc.get_value('Root.FredStart', default=None)
    end = doc.get_value('Root.FredEnd', default=None)

    series = ','.join([ t.value for t in doc['References'].find('Root.FredSeries')])

    u_s = 'fred:' + '/'.join([e for e in [series, start, end] if e])

    u = parse_app_url(u_s)

    yield from u.generator


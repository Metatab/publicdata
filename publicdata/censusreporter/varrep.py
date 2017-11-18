# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""
Functions for reading and manipulating Census Variance Replicate Tables, which allow for combining
variables and geographies with lower margins of error than with the error appoximation equations.

https://www.census.gov/programs-surveys/acs/technical-documentation/variance-tables.html

"""

import gzip

import pandas as pd
import requests
from .util import get_cache, slugify

def get_ave_weight(state):
    """Return the average weight parameter for a state"""
    import metatab as mt

    doc = mt.open_package(
        'http://s3.amazonaws.com/library.metatab.org/census.gov-varrep_tables_support-2011e2015-1.csv')

    r = doc.resource('ave_weights')

    d = {}

    for row in r.iterdict:

        try:
            if int(row['fips_state_code']) == int(state):
                return int(row['average_weight'])
        except TypeError:
            continue


def get_k_val_f():
    """Return a function that maps from population to k_values"""
    import metatab as mt

    doc = mt.open_package(
        'http://s3.amazonaws.com/library.metatab.org/census.gov-varrep_tables_support-2011e2015-1.csv')

    r = doc.resource('k_values')

    rows = list(dict(e.items()) for e in r.iterdict)

    def f(population):
        for row in rows:

            if row['range_start'] <= population and ( row['range_end'] is None or population <= row['range_end']):
                return row['k_value']

        else:
            return row['k_value']

    return f


def get_varrep_dataframe(year, table_id, summary_level, state=None, geoid=None, cache=True):
    """Load Census Variance Replicate data into a dataframe.

    :param year: release year
    :param table_id: Census table id, ex: 'B01001'
    :param state: FIPS code for the state. Required for summar levels 140 and  150
    :param summary_level: A summary level number or string, ex: 140
    :param geoid: Geoid of the containing region. ex '05000US06073' for San Diego county
    :param cache: If true, cache the response from Census Reporter ( Fast and Friendly! )
    :return:
    """

    cache_fs = get_cache()

    sl = str(summary_level).zfill(3)

    if sl in ('140', '150'):
        if not state:
            raise ValueError("A state value is required for summary levels 140 and 150")
        url_file = "{}_{}.csv.gz".format(table_id.upper(), str(state).zfill(2))
    else:
        url_file = "{}.csv.gz".format(table_id.upper())

    # https://www2.census.gov/programs-surveys/acs/replicate_estimates/2015/data/5-year/140/

    url = "https://www2.census.gov/programs-surveys/acs/replicate_estimates/{year}/data/5-year/{sl}/{file}" \
        .format(year=year, sl=sl, file=url_file)

    cache_key = slugify(url)

    # We actually always cache the file, so cache==False
    # just removes it first. ( so it means: don't read from the cache )
    if not cache and cache_fs.exists(cache_key):
        cache_fs.remove(cache_key)

    if not cache_fs.exists(cache_key):
        r = requests.get(url)

        # There is something wrong with the content encoding. Requests ought to decode it, but
        # r.raw and r.text turn out wrong.

        cache_fs.setbytes(cache_key, r.content)

    csv_file = cache_fs.getsyspath(cache_key)

    # It looks like the JSON dicts may be properly sorted, but I'm not sure I can rely on that.
    # So, sort the column id values, then make a columns title list in the same order

    return pd.read_csv(gzip.open(csv_file))

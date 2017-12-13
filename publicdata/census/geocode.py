# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import requests
from six import StringIO
from os import environ
import csv
import sys
import json
import metatab as mt
from itertools import islice
from geoid.census import Tract as CensusTract
from geoid.acs import Tract as AcsTract
from requests.exceptions import Timeout
from rowgenerators import SourceError
from metatab import MetatabError

from address_parser import Parser

geocoder_header = 'unique_id input_address match quality match_address latlon tiger_id ' \
                  'side_of_street state_fips county_fips tract_fips block_fips'.split()

response_header = 'unique_id input_address match quality match_address lat lon tiger_id ' \
             'side_of_street state_fips county_fips tract_fips block_fips tract_geoid'.split()

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

def make_request(rows):

    if  len(rows) == 0:
        return

    header = "Unique ID, Street address, City, State, ZIP".split(',')
    strio = StringIO()
    sw = csv.writer(strio)
    #sw.writerow(header)
    sw.writerows(rows)
    text = strio.getvalue()

    tries = 3

    yielded = set()

    url = 'https://geocoding.geo.census.gov/geocoder/geographies/addressbatch'

    payload = {
        'benchmark':'Public_AR_Current',
        'vintage':'ACS2013_Current',
        'returntype': 'geographies'
    }

    files = {'addressFile':  ('report.csv', text) }

    while tries:

        try:
            r = requests.post(url, files=files, data = payload, timeout= 2*60)
            r.raise_for_status()

            for i, row in enumerate(csv.reader(StringIO(r.text))):

                if not tuple(row) in yielded:
                    yield row
                yielded.add(tuple(row))

            break
        except Timeout as e:
            tries -= 1
            print("TIMEOUT!", e, file=sys.stderr)
        except Exception as e:
            tries -= 1
            print("ERROR", e, file=sys.stderr)

def mkdict(row):
    """Turn a geocoder response row into a well-formed dict"""
    d = dict(zip(geocoder_header, row))

    if len(row) > 3:

        try:

            try:
                d['lat'], d['lon'] = d['latlon'].split(',')
            except ValueError as e:
                d['lat'], d['lon'] = '',''

            d['tract_geoid'] = str(AcsTract( int(d['state_fips']), int(d['county_fips']), int(d['tract_fips']) ))

            try:
                del d['latlon']
            except Exception as e:
                pass


        except Exception as e:
            # These appear to be errors associated with quote characters in the addresses, like
            # 366426709,"8430 I AVENUE""", HESPERIA, CA," 92345""",No_Match. There aren't many of
            # them, but they are a problem
            print("ERROR for ", row, e, file=sys.stderr)

            d['input_address'] = ''
            d['match'] = 'Parse Error'

    return d

def chunked_geocode(addresses, state = None, chunk_size=250):

    # Each address entry must be a tuple of (unique_id, address)


    parser = Parser()

    row_n = 0

    request_rows = []

    for uid, address_line in addresses:

        p = parser.parse(address_line)

        rr = [uid, p.street_str(),
              p.locality.city,
              state or p.locality.state,
              p.locality.zip]


        request_rows.append(rr)

        if len(request_rows) > chunk_size:

            for row in make_request(request_rows):
                # row colums are:
                # unique_id input_address match quality match_address latlon tiger_id side_of_street state_fips county_fips tract_fips block_fips
                yield row_n, True, mkdict(row)
                row_n += 1

            request_rows = [];


    for row in make_request(request_rows):
        # row colums are:
        # unique_id input_address match quality match_address latlon tiger_id side_of_street state_fips county_fips tract_fips block_fips
        yield row_n, True, mkdict(row)
        row_n += 1

import unittest

import pandas as pd
import numpy as np
from rowgenerators.appurl import parse_app_url
from publicdata.census.api.censusapi import CensusApi
from publicdata.census.api.url import CensusApiUrl
from hashlib import sha256

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(abspath(__file__)), 'test_data', *paths))

class BasicTests(unittest.TestCase):

    def test_basic(self):

        u = CensusApiUrl('censusapi://ACSST1Y2018/state:01/county:*#NAME,S2001_C06_007E')

        self.assertEqual('censusapi',u.proto)

        self.assertIsInstance(u, CensusApiUrl)


        dataset_id, in_spec, for_spec = u.path.split('/')

        if not dataset_id: # The url has a :// in it
            dataset_id = u.netloc

        self.assertEqual('ACSST1Y2018', dataset_id)
        self.assertEqual('state:01', in_spec)
        self.assertEqual('county:*', for_spec)

        m = sha256()

        # Iterate and check the result.
        for row in u.generator:
            if row:
                m.update((' '.join(str(e) for e in row)).encode('utf8'))

        self.assertEqual('1647c540edc0b03e5e37bef0b4cef34e5e57384a32996437ac8e1dbcba2ecc4a',
                         m.hexdigest())

        m = sha256()

        for e in list(u.dataframe.NAME):
            m.update(e.encode('utf8') )

        self.assertEqual('52e616c47998a796921a8987cde8d5b466000557cea6e1fef9fa7f960a504ed7',
                         m.hexdigest())


    def test_url_entrypoint(self):
        m = sha256()

        u = parse_app_url('censusapi://ACSST1Y2018/state:01/county:*#NAME,S2001_C06_007E')



        # Iterate and check the result.
        for row in u.generator:
            if row:
                m.update((' '.join(str(e) for e in row)).encode('utf8'))

        self.assertEqual('1647c540edc0b03e5e37bef0b4cef34e5e57384a32996437ac8e1dbcba2ecc4a',
                         m.hexdigest())


if __name__ == '__main__':
    unittest.main()

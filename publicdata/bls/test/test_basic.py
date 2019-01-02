# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""Tests for BLS Series_idsk"""

import unittest
from rowgenerators import parse_app_url, Downloader

class TestBasic(unittest.TestCase):

    sample_series_ids = [
        'LASBS060000000000003',
        'LASDV063108400000003',
        'LASST060000000000003',
        'LAUBS060000000000003',
        'LAUCA062600000000003',
        'LAUCN060010000000003',
        'LAUCT060029600000003',
        'LAUDV061124400000003',
        'LAUMC061734000000003',
        'LAUMT061254000000003',
        'LAUST060000000000003']

    def setUp(self):

        import warnings # Must turn off warnings in the test function
        warnings.simplefilter("ignore")


    def test_basic(self):

        from publicdata.bls.seriesid import LauSeriesId

        for s in self.sample_series_ids:
            sid = LauSeriesId(s)
            self.assertEqual(s, str(sid))

            self.assertEqual('06',sid.state)

            print(s, sid.cbsa, sid.geoid)



if __name__ == '__main__':
    unittest.main()

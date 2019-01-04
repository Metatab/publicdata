# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest

from publicdata.test import TestCase


class TestAppUrls(TestCase):

    def test_basic(self):

        from publicdata import CensusFileUrl, CensusReporterUrl

        u = CensusFileUrl('census://CA/140/B17001')

        self.assertEqual('census://CA/140/B17001',str(u))

        self.assertEqual('B17001', u.tableid)
        self.assertEqual('140', u.summary_level)
        self.assertEqual('04000US06', u.geoid)

        url = CensusFileUrl(table='B17001', summarylevel='140', geoid='04000US06')

        self.assertEqual('B17001', u.tableid)
        self.assertEqual('140', u.summary_level)
        self.assertEqual('04000US06', u.geoid)

        url = CensusReporterUrl(table='B17001', summarylevel='140', geoid='04000US06')

        self.assertEqual('B17001', u.tableid)
        self.assertEqual('140', u.summary_level)
        self.assertEqual('04000US06', u.geoid)


    def test_geo_basic(self):
        from rowgenerators import parse_app_url
        from geoid.acs import State

        for url_s in ['census://CA/140', 'census://{}/140'.format(str(State(6))), 'census://6/140',
                      'census://CA/tract', 'census://{}/tract'.format(str(State(6))), 'census://6/tract',
                      'censusgeo://CA/140', 'censusgeo://{}/140'.format(str(State(6))), 'censusgeo://6/140',
                      'censusgeo://CA/tract', 'censusgeo://{}/tract'.format(str(State(6))), 'censusgeo://6/tract'
                      ]:
            u = parse_app_url(url_s)
            self.assertEqual(52, round(u.geoframe().head().area.sum()*100000, 0))

    def test_national_geo(self):

        from rowgenerators import geoframe

        gf = geoframe('censusgeo://US/cbsa')

        print(len(gf))



if __name__ == '__main__':
    unittest.main()

# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest


class TestAppUrls(unittest.TestCase):

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




if __name__ == '__main__':
    unittest.main()

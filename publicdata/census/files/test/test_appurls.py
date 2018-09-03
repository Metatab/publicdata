# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest


class TestAppUrls(unittest.TestCase):

    def test_basic(self):

        from publicdata.census.files.appurl import CensusUrl

        u = CensusUrl('census:B17001/140/CA')

        self.assertEqual('census://B17001/140/CA',str(u))

        self.assertEqual('B17001', u.table_id)
        self.assertEqual('140', u.summary_level)
        self.assertEqual('04000US06', u.geoid)
         

if __name__ == '__main__':
    unittest.main()

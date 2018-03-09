# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest


class TestAppUrls(unittest.TestCase):

    def test_basic(self):

        from publicdata.census.files.appurl import CensusUrl

        self.assertEqual('census://B17001/140/CA',str(CensusUrl('census:B17001/140/CA')))

if __name__ == '__main__':
    unittest.main()

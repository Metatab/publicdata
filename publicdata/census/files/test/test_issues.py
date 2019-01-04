# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest
from rowgenerators import parse_app_url

class TestIssues(unittest.TestCase):

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_no_titles(self):

        u = parse_app_url('census://CA/140/B02001')

        df = u.dataframe()

        self.assertTrue('Two or more races:' in ' '.join(df.titles.columns) )
        self.assertTrue('Two or more races:' in ' '.join(df.title_map.values()))

        x = u._mangle_dataframe(df)



        g = u.generator

        df = g.dataframe()

        columns = df.titles.columns
        print(columns)

    def test_2017(self):

        from publicdata.census.files.generators import Table, SequenceFile

        table = Table(2017, 5, 'CA', 140, 'B17001A')

        return

        u = parse_app_url('census://2017/5/CA/140/B17001A')

        print(u.generator)

    def test_header_rows(self):

        u = parse_app_url('census://2016/5/CA/40/B17001A')
        df = u.dataframe()

        print(df.table.descriptions)

if __name__ == '__main__':
    unittest.main()

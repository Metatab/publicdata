# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

import unittest


class TestIssues(unittest.TestCase):

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_no_titles(self):
        from rowgenerators import parse_app_url

        u = parse_app_url('census://CA/140/B02001')

        df = u.dataframe()

        self.assertTrue('Two or more races:' in ' '.join(df.titles.columns) )
        self.assertTrue('Two or more races:' in ' '.join(df.title_map.values()))

        x = u._mangle_dataframe(df)



        g = u.generator

        df = g.dataframe()

        columns = df.titles.columns
        print(columns)

if __name__ == '__main__':
    unittest.main()

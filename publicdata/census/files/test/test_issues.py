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

    def test_split_tables(self):

        # Table b24121 Detailed Occupation by Median Earnings for the Full-time, Year-round Civilian Population is split
        # across multiple segments.
        from publicdata.census.files.generators import Table, TableMeta, SequenceFile
        from publicdata.census.files.metafiles import TableLookup
        from itertools import islice

        sequence_file = SequenceFile(2017, 5, 'RI', 50, 85)
        print(sequence_file.header_url)
        print(len(list(sequence_file.columns)))

        for c in list(sequence_file.columns)[:10]:
            print(c.row)

        sequence_file = SequenceFile(2017, 5, 'RI', 50, 86)
        print(len(list(sequence_file.columns)))

        sequence_file = SequenceFile(2017, 5, 'RI', 50, 87)
        print(len(list(sequence_file.columns)))
        print(sequence_file.est_url)

        print('\n'.join(str(e) for e in list(islice(sequence_file, 10))))

        meta = TableMeta(2017, 5)

        print(len(meta.tables['b24121'].columns))

        tl = TableLookup(2017, 5)
        print (tl.url)

        table = Table(2017, 5, 'RI', 40, 'B24121')

        self.assertEqual(1056, (len(list(table.file_headers))))
        self.assertEqual(1056, len(list(table.columns)))

        from rowgenerators import dataframe
        df = dataframe('census://2016/5/RI/40/B24121')

    def test_titles(self):
        import rowgenerators as rg
        #df = rg.dataframe(f'census:/2017/1/CA/50/B22003')
        #print(df.titles.head().T)

        u = parse_app_url('census:/2017/1/CA/50/B22003')
        for e in u.generator.table.columns:
            print(e.row)

    def test_B02001(self):
        import rowgenerators as rg

        raceeth = rg.dataframe('census://2017/5/tract/B02001')


if __name__ == '__main__':
    unittest.main()

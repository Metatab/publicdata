
import unittest
import requests
from publicdata.census.files.url_templates import *
from publicdata.census.files.metafiles import Table, Column, TableShell, TableLookup, TableMeta
from publicdata.census.files.generators import SequenceFile, GeoFile, Table as TableGenerator
from rowgenerators import parse_app_url
from itertools import islice
import csv
import logging


class TestGenerators(unittest.TestCase):

    def test_tableshell(self):

        ts = TableShell(2016, 1)

        ts._process()

        self.assertEqual(1319, len(ts.tables))

        self.assertEqual(['b15002h', 'c15002h', 'b15002i', 'c15002i', 'b15003',
                          'c15003', 'b15010', 'c15010', 'c15010a', 'c15010b'],
                         list(ts.tables.keys())[500:510])

        self.assertEqual(ts.tables['c16004'].title,
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        with open('/tmp/tables_shell.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Table.csv_header)
            w.writerows(t.row for t in ts.tables.values())

    def test_tablelookup(self):

        ts = TableLookup(2016, 1)

        ts._process()

        self.assertEqual(1310, len(ts.tables))

        self.assertEqual(['c15002d', 'c15002e', 'c15002f', 'c15002g', 'c15002h',
                          'c15002i', 'c15003', 'c15010', 'c15010a', 'b15011'],
                         list(ts.tables.keys())[500:510])

        self.assertEqual(ts.tables['c16004'].title,
                         'Age By Language Spoken At Home By Ability To Speak English For The Population 5 Years And Over')

        with open('/tmp/tables_lookup.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Table.csv_header)
            w.writerows(t.row for t in ts.tables.values())

    def test_tablemeta(self):
        tm = TableMeta(2016, 1)

        tm._process()

        self.assertEqual(1319, len(tm.tables))

        self.assertEqual(['b15002h', 'c15002h', 'b15002i', 'c15002i',
                          'b15003', 'c15003', 'b15010', 'c15010', 'c15010a', 'c15010b'],
                         list(tm.tables.keys())[500:510])

        self.assertEqual(tm.tables['c16004'].title,
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        with open('/tmp/tables_meta.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Table.csv_header)
            w.writerows(t.row for t in tm.tables.values())


        with open('/tmp/columns_meta.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Column.csv_header)

            for t in tm.tables.values():
                for cn in sorted(t.columns):
                    c = t.columns[cn]
                    w.writerow(c.row )



    def test_geo(self):

        tm = GeoFile(2016, 5, 'RI', 140, 1)

        for row in islice(tm,10):
            print(row)

    def test_table(self):
        import geoid.core

        tm = TableGenerator(2016, 5, 'CA', geoid.core.names['tract'], 'B01001')

        tracts = list(tm)
        self.assertEqual(8058, len(tracts))

        lens = [len(row) for row in tracts]

        self.assertTrue(all(x == lens[0] for x in lens))

        rows = list(islice(tm,5))

        self.assertEqual(('GEOID', 'B01001_001_m90', 'B01001_004', 'B01001_006_m90', 'B01001_009',
                          'B01001_011_m90', 'B01001_014', 'B01001_016_m90', 'B01001_019', 'B01001_021_m90',
                          'B01001_024', 'B01001_026_m90', 'B01001_029', 'B01001_031_m90', 'B01001_034',
                          'B01001_036_m90', 'B01001_039', 'B01001_041_m90', 'B01001_044', 'B01001_046_m90',
                          'B01001_049'),
                          rows[0][::5])


        self.assertEqual(('14000US06001400100', 'CA', '001', 'Census Tract 4001, Alameda County, California',
                          3018, 195),
                          rows[1][:6])

        # Checksum a few rows
        self.assertEqual(6561, sum(rows[1][7:]))
        self.assertEqual(9061, sum(rows[4][7:]))

    def test_appurl(self):

        from rowgenerators import parse_app_url

        u = parse_app_url('census://2016/5/RI/140/B17001')

        rows = list(u.generator)

        self.assertEqual(245,len(rows))

    def test_appurl_US(self):
        from rowgenerators import parse_app_url
        from rowgenerators.appurl.web.download import logger as download_logger
        from publicdata.census.files import logger

        logging.basicConfig()

        logger.setLevel(logging.DEBUG)

        u = parse_app_url('census://2016/5/US/50/B17001')

        rows = list(u.generator)

        self.assertEqual(3272,len(rows))

    def test_sequence(self):

        sf = SequenceFile(2016,5,'RI',140, 3 )

        h, f, m = list(zip(sf.file_headers, sf.descriptions, sf.meta))[60]

        self.assertEqual('B01001G_028', h)
        self.assertEqual('SEX BY AGE (TWO OR MORE RACES) for People Who Are Two Or More Races% Female:% 55 to 64 years',
                         f)

        for h,f,m in list(zip(sf.file_headers, sf.descriptions, sf.meta)):
            self.assertEqual(h, m.unique_id)

    def test_dataframe(self):
        from publicdata.census.files.appurl import CensusFile
        from rowgenerators import parse_app_url

        u = parse_app_url('census://2016/5/RI/140/B01002')

        print(type(u))

        g = u.generator

        rows = list(g)

        self.assertEqual(245,len(rows))

        df = u.generator.dataframe()

        self.assertEqual(9708, int(df['B01002_001'].sum()))
        self.assertEqual(809, int(df['B01002_001_m90'].sum()))
        self.assertEqual(9375, int(df['B01002_002'].sum()))
        self.assertEqual(1171, int(df['B01002_002_m90'].sum()))

    def test_geo_dataframe(self):

        u = parse_app_url('census://2016/5/RI/140/B01002')

        gdf = u.generator.geoframe

        print(gdf.head())
        print(gdf.geometry.head())

if __name__ == '__main__':
    unittest.main()

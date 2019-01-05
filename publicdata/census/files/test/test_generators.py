
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

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')


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

        self.assertEqual(1310, len(tm.tables))

        self.assertEqual(sorted(['b00001', 'b00002', 'b01001', 'b01001a', 'b01001b', 'b01001c',
                                 'b01001d', 'b01001e', 'b01001f', 'b01001g']),
                         sorted(list(tm.tables.keys())[:10]))

        self.assertEqual(sorted(['b15011', 'c15002d', 'c15002e', 'c15002f', 'c15002g',
                                 'c15002h', 'c15002i', 'c15003', 'c15010', 'c15010a']),
                         sorted(list(tm.tables.keys())[500:510]))

        self.assertEqual(tm.tables['c16004'].title,
                         'Age By Language Spoken At Home By Ability To Speak English For The Population 5 Years And Over')

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
        from publicdata.census.util import sub_geoids, sub_summarylevel

        from rowgenerators import parse_app_url
        from publicdata.census.exceptions import CensusParsingException

        #self.assertEqual(245,list(parse_app_url('census://2016/5/RI/140/B17001').generator))

        #self.assertEqual(245, list(parse_app_url('census://RI/140/B17001').generator))

        with self.assertRaises(ValueError):
            sub_geoids('foobar')

        u = parse_app_url('census://RI/140/B17001')
        self.assertEqual('B17001', u.tableid)
        self.assertEqual('04000US44', u.geoid)

        u = parse_app_url('census://B17001/140/RI')
        self.assertEqual('B17001', u.tableid)
        self.assertEqual('04000US44', u.geoid)

        u = parse_app_url('census://140/RI/B17001')
        self.assertEqual('B17001', u.tableid)
        self.assertEqual('04000US44', u.geoid)

        with self.assertRaises(CensusParsingException):
            parse_app_url('census://B17001/Frop/140')

        with self.assertRaises(CensusParsingException):
            parse_app_url('census://BINGO/RI/140')


    def test_appurl_US(self):
        from rowgenerators import parse_app_url
        from rowgenerators.appurl.web.download import logger as download_logger
        from publicdata.census.files import logger

        logging.basicConfig()

        logger.setLevel(logging.DEBUG)

        # Iterate over all counties in the US
        u = parse_app_url('census://2016/5/US/county/B01003')

        rows = list(u.generator)

        states = set()
        counties = set()
        for row in rows[1:]:
            states.add(row[1])
            counties.add(row[3])

        from collections import Counter

        c = Counter(row[3] for row in rows[1:])

        for k, v in c.items():
            if v > 1:
                print(k,v)

        self.assertEqual(52, len(states))
        self.assertEqual(3220, len(counties))
        self.assertEqual(3220,len(rows[1:]))

    def test_sequence(self):

        sf = SequenceFile(2016,5,'RI',140, 3 )

        h, f, m = list(zip(sf.file_headers, sf.descriptions, sf.columns))[60]

        self.assertEqual('B01001G_028', h)
        self.assertEqual('SEX BY AGE (TWO OR MORE RACES) for People Who Are Two Or More Races - Female: - 55 to 64 '
                         'years',
                         f)

        for h,f,m in list(zip(sf.file_headers, sf.descriptions, sf.columns)):
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

        self.assertEqual(244, len(u.geoframe().geometry))

        u = parse_app_url('censusgeo://2016/5/RI/140')

        self.assertEqual(244, len(u.geoframe().geometry))


    def test_age_dimensions(self):

        '''Check that there are not tables with 'year' in the title that don't get a parsed age range'''

        tm = TableMeta(2016, 5)

        age_tables = []
        for t_id, table in tm.tables.items():
            if 'by age' in table.title.lower():
                age_tables.append(t_id)

        for at in age_tables:
            u = parse_app_url('census://2016/5/RI/40/{}'.format(at.lower()))
            g = u.generator
            t = g.table

            parse_errors = []

            for c in t.columns:
                if '_m90' not in c.unique_id and 'year' in c.description and not c.age_range and '1 year ago' not in \
                        c.description and 'year-round' not in c.description:
                    parse_errors.append(c)

            for parse_error in parse_errors:
                print(parse_error.row)

            self.assertEqual(0, len(parse_errors))

    def test_race_dimensions(self):

        table_ids = ['B03002','C02003', 'B02017']

        table_ids = ['b02008', 'b02010', 'b02015']

        table_ids = ['B05010','B17001', 'B17001a', 'B17001b', 'B17001i']

        for t_id in table_ids:
            u = parse_app_url('census://2016/5/RI/40/{}'.format(t_id.lower()))
            g = u.generator
            t = g.table
            print('---- ', t.table.title)
            for i, c in enumerate(t.columns):
                if '_m90' not in c.unique_id and i > 3:
                    row = [c.unique_id, c.sex, c.race, c.age, c.description]
                    print(row)

                if i > 30:
                    break

    def test_pov_dimensions(self):
        tm = TableMeta(2016, 5)

        for t_id, table in tm.tables.items():
            u = parse_app_url('census://2016/5/RI/40/{}'.format(t_id.lower()))
            g = u.generator
            t = g.table

            for i, c in enumerate(t.columns):
                if '_m90' not in c.unique_id and 'poverty' in c.long_description:
                    print(c.unique_id, c.poverty_status, c.long_description)

    def test_dimensions(self):
        tm = TableMeta(2016, 5)

        with open('/tmp/dimensions.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow("id sex race age pov description".split())

            for t_id, table in tm.tables.items():
                u = parse_app_url('census://2016/5/RI/40/{}'.format(t_id.lower()))
                g = u.generator
                t = g.table

                w.writerow([t_id, table.title])
                for i, c in enumerate(t.columns):
                    if '_m90' not in c.unique_id and i > 3:
                        row = [c.unique_id, c.sex, c.race, c.age, c.poverty_status, c.description]
                        print(row)
                        w.writerow(row)




if __name__ == '__main__':
    unittest.main()

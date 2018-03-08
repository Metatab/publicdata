
import unittest
import requests
from publicdata.census.files.url_templates import *
from publicdata.census.files.metafiles import Table, Column, TableShell, TableLookup, TableMeta
from publicdata.census.files.generators import SequenceFile, GeoFile, Table
from rowgenerators import parse_app_url
from itertools import islice
import csv


class TestGenerators(unittest.TestCase):

    def test_tableshell(self):

        ts = TableShell(2016, 1)

        ts._process()

        print (len(ts.tables))

        print(list(ts.tables.keys())[500:550])

        self.assertEqual(ts.tables['C16004'].title,
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        with open('/tmp/tables_shell.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Table.csv_header)
            w.writerows(t.row for t in ts.tables.values())

    def test_tablelookup(self):

        ts = TableLookup(2016, 1)

        ts._process()

        print (len(ts.tables))

        print(list(ts.tables.keys())[500:550])

        self.assertEqual(ts.tables['C16004'].title,
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        with open('/tmp/tables_lookup.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(Table.csv_header)
            w.writerows(t.row for t in ts.tables.values())

    def test_tablemeta(self):
        tm = TableMeta(2016, 1)

        tm._process()

        print(len(tm.tables))

        print(list(tm.tables.keys())[500:550])

        self.assertEqual(tm.tables['C16004'].title,
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

    def test_sequence(self):

        tm = SequenceFile(2016, 5, 'RI', 140, 2)

        for row in islice(list(tm),3):
            print(row)

    def test_geo(self):

        tm = GeoFile(2016, 5, 'RI', 140, 1)

        for row in islice(tm,10):
            print(row)

    def test_table(self):
        import geoid.core

        tm = Table(2016, 5, 'CA', geoid.core.names['tract'], 'B01001')

        tracts = list(tm)
        self.assertEqual(8058, len(tracts))

        lens = [len(row) for row in tracts]

        self.assertTrue(all(x == lens[0] for x in lens))

        for row in islice(tm,5):
            print(row)

if __name__ == '__main__':
    unittest.main()

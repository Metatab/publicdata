
from itertools import islice

import csv
import unittest
from publicdata.census.files.generators import SequenceFile, GeoFile, Table
from publicdata.census.files.metafiles import Table as MetaTable, Column, TableShell, TableLookup, TableMeta


class TestMeta(unittest.TestCase):

    def test_tableshell(self):

        ts = TableShell(2016, 1)

        print(ts.url)

        ts._process()

        # For 2016, at least, there are 131`9 tables in the TableShell, but 1310 in The TableLookup
        # and TableMeta. The TableShell includes racial iterations for:
        # C2410 SEX BY OCCUPATION FOR THE CIVILIAN EMPLOYED POPULATION 16 YEARS AND OVER
        self.assertEqual(1319,len(ts.tables))

        keys = ['b18135', 'b18140', 'b19001', 'b19001a', 'b19001b', 'b19001c', 'b19001d', 'b19001e', 'b19001f',
                'b19001g', 'b19001h', 'b19001i', 'b19013', 'b19013a', 'b19013b', 'b19013c', 'b19013d', 'b19013e',
                'b19013f', 'b19013g', 'b19013h', 'b19013i', 'b19019', 'b19025', 'b19025a', 'b19025b', 'b19025c',
                'b19025d', 'b19025e', 'b19025f', 'b19025g', 'b19025h', 'b19025i', 'b19037', 'b19037a', 'b19037b',
                'b19037c', 'b19037d', 'b19037e', 'b19037f', 'b19037g', 'b19037h', 'b19037i', 'b19049', 'b19050',
                'b19051', 'b19052', 'b19053', 'b19054', 'b19055']

        self.assertEqual(keys, sorted(ts.tables.keys())[500:550])

        self.assertEqual(ts.tables['c16004'].title.upper(),
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')



    def test_tablelookup(self):

        ts = TableLookup(2016, 1)

        ts._process()

        self.assertEqual(1310, len(ts.tables))

        keys = ['b18135', 'b18140', 'b19001', 'b19001a', 'b19001b', 'b19001c', 'b19001d', 'b19001e', 'b19001f',
                'b19001g', 'b19001h', 'b19001i', 'b19013', 'b19013a', 'b19013b', 'b19013c', 'b19013d', 'b19013e',
                'b19013f', 'b19013g', 'b19013h', 'b19013i', 'b19019', 'b19025', 'b19025a', 'b19025b', 'b19025c',
                'b19025d', 'b19025e', 'b19025f', 'b19025g', 'b19025h', 'b19025i', 'b19037', 'b19037a', 'b19037b',
                'b19037c', 'b19037d', 'b19037e', 'b19037f', 'b19037g', 'b19037h', 'b19037i', 'b19049', 'b19050',
                'b19051', 'b19052', 'b19053', 'b19054', 'b19055']

        self.assertEqual(keys, sorted(ts.tables.keys())[500:550])

        self.assertEqual(ts.tables['c16004'].title.upper(),
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        for t_id, table in ts.tables.items():
            if table.number_of_segments > 1:
                print(t_id, table.title)


    def test_tablemeta(self):
        tm = TableMeta(2016, 1)

        tm._process()

        self.assertEqual(1310, len(tm.tables))

        keys = ['b18135', 'b18140', 'b19001', 'b19001a', 'b19001b', 'b19001c', 'b19001d', 'b19001e', 'b19001f',
                'b19001g', 'b19001h', 'b19001i', 'b19013', 'b19013a', 'b19013b', 'b19013c', 'b19013d', 'b19013e',
                'b19013f', 'b19013g', 'b19013h', 'b19013i', 'b19019', 'b19025', 'b19025a', 'b19025b', 'b19025c',
                'b19025d', 'b19025e', 'b19025f', 'b19025g', 'b19025h', 'b19025i', 'b19037', 'b19037a', 'b19037b',
                'b19037c', 'b19037d', 'b19037e', 'b19037f', 'b19037g', 'b19037h', 'b19037i', 'b19049', 'b19050',
                'b19051', 'b19052', 'b19053', 'b19054', 'b19055']

        self.assertEqual(keys, sorted(tm.tables.keys())[500:550])

        self.assertEqual(tm.tables['c16004'].title.upper(),
                         'AGE BY LANGUAGE SPOKEN AT HOME BY ABILITY TO SPEAK ENGLISH FOR THE POPULATION 5 YEARS AND OVER')

        with open('/tmp/tables_meta.csv', 'w') as f:
            w = csv.writer(f)

            w.writerow(MetaTable.csv_header)
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

        tract_sl = geoid.core.names['tract']

        tm = Table(2016, 5, 'CA', tract_sl, 'B01001')

        tracts = list(tm)
        self.assertEqual(8058, len(tracts))

        lens = [len(row) for row in tracts]

        self.assertTrue(all(x == lens[0] for x in lens))




if __name__ == '__main__':
    unittest.main()

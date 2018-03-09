import unittest

import pandas as pd
import numpy as np

from appurl import parse_app_url


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(abspath(__file__)), 'test_data', *paths))


class BasicTests(unittest.TestCase):

    def test_basic(self):
        from publicdata.censusreporter.url import CensusReporterURL
        from publicdata.censusreporter.generator import CensusReporterSource

        u = parse_app_url('censusreporter://B01001/140/05000US06073')

        self.assertEqual(629, len(list(u.generator)))
        self.assertIsInstance(u, CensusReporterURL)
        self.assertIsInstance(u.generator, CensusReporterSource)

        B01001 = u.generator.dataframe()

        self.assertEqual(3223096.0, B01001.B01001001.sum())

        #print(B01001.titles.iloc[:2].T)

        cols = [
            'geoid',
            'B01001001',  # Total Population
            'B01001002',  # Total Male
            'B01001026',  # Total Female
            'B01001013', 'B01001014',  # Males, 35-39 and 40-44
            'B01001037', 'B01001038'  # Female, 35-39 and 40-44
        ]

        df = B01001[cols].copy()


        df['male_35_44'], df['male_35_44_m90'] = df.sum_m('B01001013', 'B01001014')
        df['female_35_44'], df['female_35_44_m90'] = df.sum_m('B01001037', 'B01001038')

        df['m_ratio'],df['m_ratio_m90'] = df.ratio('male_35_44','B01001002')

        print(len(df.proportion('male_35_44', 'female_35_44')))

        df['mf_proprtion'] , df['mf_proprtion_m90'] = df.proportion('male_35_44', 'female_35_44')

        self.assertEqual(211707.0, df.female_35_44.dropna().sum())
        self.assertEqual(82, int(df.m_ratio.dropna().sum()))

    def test_census_shapes(self):
        from publicdata.censusreporter.url import CensusReporterShapeURL
        from rowgenerators.appurl.shapefile import ShapefileUrl, ShapefileShpUrl
        from rowgenerators.generator.shapefile import ShapefileSource

        u = parse_app_url('censusreportergeo://B01003/140/05000US06073')

        self.assertTrue(str(u.resource_url).endswith('&format=shp'))

        self.assertIsInstance(u, CensusReporterShapeURL)

        r = u.get_resource()

        self.assertIsInstance(r, ShapefileUrl)

        self.assertTrue(str(r).endswith('/latest.zip#.%2A%5C.shp%24'), str(r))

        g = r.generator

        self.assertIsInstance(g, ShapefileSource)

        self.assertEquals(629, (len(list(g))))

        return

    def test_geo(self):

        u = parse_app_url('censusreporter://B01001/140/05000US06073')

        B01001 = u.generator.dataframe()

        geo = B01001.geo

        print(len(geo))

if __name__ == '__main__':
    unittest.main()

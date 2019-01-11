from publicdata.test import TestCase
from rowgenerators import parse_app_url, Downloader


class TestBasic(TestCase):


    def test_basic(self):


        from publicdata import CensusFileUrl, CensusReporterUrl

        args= dict(year=2016,release=5,table='B17001',summarylevel='tract',geoid='RI')



        for cls in (CensusReporterUrl, CensusFileUrl, ):

            print("Class: ", cls)

            url = cls(**args, downloader = Downloader.get_instance())

            self.assertEqual(245, len(list(url.generator)))

            df = url.dataframe()

            print("Type", type(df))

            self.assertEqual(244, len(df)) # No header, so one less

            print('Geo', url.geo_url)

            print('Geo Generator', url.geo_generator)

            gdf = url.geoframe()

            #print(gdf.head())

            print(gdf.iloc[0].geometry.envelope)

            gdf = df.geoframe()
            print(gdf.iloc[0].geometry.envelope)

    def test_RowGenerator(self):
        import warnings
        warnings.simplefilter("ignore")

        from rowgenerators import RowGenerator

        rg = RowGenerator('census://CA/140/B17001')

        self.assertEqual(8058, len(list(rg)))

        df = rg.dataframe()

        self.assertEqual(8057, len(df))

    def test_urls(self):

        import rowgenerators as rg

        gdf = rg.geoframe('censusgeo://CA/140')
        print(gdf.set_index('geoid').head())



        return

        u = rg.parse_app_url('census://CA/140/B17001')
        t = u.get_resource().get_target()
        print(t, t.year, t.release)
        self.assertEqual('census://CA/140/B17001',str(t))
        self.assertEqual(2016, t.year)
        self.assertEqual(5, t.release)

        u = rg.parse_app_url('census://2015/3/CA/140/B17001')
        t = u.get_resource().get_target()
        print(t, t.year, t.release)
        self.assertEqual('census://2015/3/CA/140/B17001', str(t))
        self.assertEqual(2015, t.year)
        self.assertEqual(3, t.release)

        gdf = t.geoframe()
        self.assertEqual(43.083, gdf.area.sum().round(3))

        gdf = rg.geoframe('census://CA/140/B17001')
        self.assertEqual(43.083, gdf.area.sum().round(3))

        gdf = rg.geoframe('censusgeo://CA/140')
        self.assertEqual(43.083, gdf.area.sum().round(3))

    def test_dimensions(self):

        import rowgenerators as rg

        df = rg.dataframe('census://CA/140/B17001')

        print(type(df))

        #for c in df.table.columns:
        #    print(c.unique_id, c.sex, c.race, c.age, c.poverty_status)

        print(df.head())



if __name__ == '__main__':
    unittest.main()

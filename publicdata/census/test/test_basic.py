import unittest
from rowgenerators import parse_app_url, Downloader

class TestBasic(unittest.TestCase):


    def test_basic(self):

        import warnings # Must turn off warnings in the test function
        warnings.simplefilter("ignore")

        from publicdata import CensusFileUrl, CensusReporterUrl

        args= dict(year=2016,release=5,table='B17001',summarylevel='tract',geoid='RI')



        for cls in (CensusReporterUrl, CensusFileUrl, ):

            print("Class: ", cls)

            url = cls(**args, downloader = Downloader())

            self.assertEqual(245, len(list(url.generator)))

            df = url.dataframe

            print("Type", type(df))

            self.assertEqual(244, len(df)) # No header, so one less

            print('Geo', url.geo_url)

            print('Geo Generator', url.geo_generator)

            gdf = url.geoframe

            #print(gdf.head())

            print(gdf.iloc[0].geometry.envelope)

            gdf = df.geoframe
            print(gdf.iloc[0].geometry.envelope)

if __name__ == '__main__':
    unittest.main()

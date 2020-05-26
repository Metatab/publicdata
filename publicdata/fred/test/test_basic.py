# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


import unittest
from rowgenerators import parse_app_url, Downloader
from publicdata.fred import *

downloader = Downloader()

class TestBasic(unittest.TestCase):


    def setUp(self):

        import warnings # Must turn off warnings in the test function
        warnings.simplefilter("ignore")


    def test_basic(self):

        u = parse_app_url('fred:SP500/2014-09-02/2019-01-01', downloader=downloader)
        print(u, type(u))


        print(u.dataframe().head())



if __name__ == '__main__':
    unittest.main()

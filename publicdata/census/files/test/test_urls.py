import unittest
import requests
from publicdata.census.files.url_templates import *
from rowgenerators import parse_app_url

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(abspath(__file__)), 'test_data', *paths))


class BasicTests(unittest.TestCase):

    def test_inconsistent_dc_name(self):

        self.assertEqual('DistrictOfColumbia', state_name('dc', 2016, 5))
        self.assertEqual('DistrictofColumbia', state_name('dc', 2016, 1))

    def yield_args_w_state(self):
        for year in [2014, 2015, 2016]:
            for release in [1, 5]:
                for stusab in ['CA','NH','DC']:
                    for summary_level in [50,140,150]:
                        for seq in [99]:
                            yield dict(year=year, release=release, stusab=stusab,
                                              summary_level=summary_level, seq=seq)


    def yield_args_wo_state(self):
        for year in [2011,2012,2013,2014, 2015, 2016]:
            for release in [1, 5]:
                for summary_level in [50,140,150]:
                    for seq in [99]:
                        yield dict(year=year, release=release, stusab=None,
                                          summary_level=summary_level, seq=seq)

    def yield_args_releases(self):
        for year in [2013,2014, 2015, 2016]:
            for release in [1, 5]:
                for summary_level in [None]:
                    for seq in [None]:
                        yield dict(year=year, release=release, stusab=None,
                                          summary_level=summary_level, seq=seq)

    def test_header_archive_url(self):


        for d in self.yield_args_wo_state():
            url = header_archive_url(**d)

            print(url)

            r = requests.head(url)
            self.assertEqual(200,r.status_code,  url)

    def test_seq_archive_url(self):

        for d in self.yield_args_w_state():
            url = seq_archive_url(**d)

            print(url)

            r = requests.head(url)
            self.assertEqual(200,r.status_code,  url)

    def test_seq_header_url(self):

        for d in self.yield_args_wo_state():
            url = seq_header_url(**d)

            print(url)

            r = requests.head(url)
            self.assertEqual(200,r.status_code,  url)

    def test_geo_url(self):


        for d in self.yield_args_w_state():
            url = geo_url(**d)

            print(url)

            r = requests.head(url)
            self.assertEqual(200, r.status_code, url)


    def test_shell_url(self):

        for d in self.yield_args_releases():
            for f in [table_shell_url, table_lookup_url]:

                url = f(**d)

                r = requests.head(url)
                self.assertEqual(200, r.status_code, url)

    def test_seq_header(self):


        url_s = seq_header_url(year=2016, release=1, stusab=None, summary_level=None, seq=100)

        u = parse_app_url(url_s)

        rows = list(u.generator)

        for e in zip(*rows):
            print(e)


    def test_dump_states(self):

        import yaml, requests
        from geoid.censusnames import stusab

        r = requests.get('https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.yml')

        rows = []

        states = {v:k for k, v in stusab.items()}

        for k, v in yaml.load(r.content).items():
            try:
                rows.append((states[v['abbreviation']], v['abbreviation'], v['name'] ))
            except KeyError:
                print(k, v)

        print(rows)


    def test_geo_urls(self):
        from itertools import islice

        for year in [2016, 2017]:
            for sl in [50,140, 160]:
                for stusab in ['RI','AZ','NY']:
                    us = tiger_url(year, sl, stusab)

                    u = parse_app_url(us)
                    print(type(u), u)
                    r = u.get_resource().get_target()

                    #for row in islice(r.generator, 2):
                    #    print(row)

                    break

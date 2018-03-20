"""
Direct access to Census ACS files, automatically downloaded from the Census website.
"""

from rowgenerators import parse_app_url
import logging

logger = logging.getLogger('publicdata.census.files')

def acs_dataframe(year, release, stateab, summary_level, table):
    """
    Return a dataframe with ACS data

    :param year: ACS year
    :param release: Release, either 5 or 1
    :param stateab:  State abbreviation, or US
    :param summary_level: Summary level, either a number or string
    :param table: Table ID
    :return:
    """


    u = parse_app_url('census://2016/5/RI/140/B01002')

    print(type(u))

    g = u.generator

    rows = list(g)

    self.assertEqual(245, len(rows))

    df = u.generator.dataframe()

    self.assertEqual(9708, int(df['B01002_001'].sum()))
    self.assertEqual(809, int(df['B01002_001_m90'].sum()))
    self.assertEqual(9375, int(df['B01002_002'].sum()))
    self.assertEqual(1171, int(df['B01002_002_m90'].sum()))

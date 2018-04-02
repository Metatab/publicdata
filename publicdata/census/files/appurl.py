# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

from publicdata.census.appurl import CensusUrl
from publicdata.census.files.url_templates import tiger_url
from publicdata.census.util import sub_geoids, sub_summarylevel
from rowgenerators import parse_app_url
from rowgenerators.exceptions import AppUrlError

class CensusFile(CensusUrl):

    """
    A URL that references row data from American Community Survey files

    census://2016/5/US/tract/B17001

    The general form is:

        census://year/release/geo_containment/summary_level/table

    """

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

        self._parts # Will raise on format errors

    def _match(cls, url, **kwargs):
        return url.scheme.startswith('census')

    @property
    def _parts(self):
        if not self.netloc:
            # If the URL didn't have ://, there is no netloc
            parts = self.path.strip('/').split('/')
        else:
            parts = tuple([self.netloc] + self.path.strip('/').split('/'))

        if len(parts) != 5:
            raise AppUrlError("Census reporters must have three path components. Got: '{}' ".format(parts)+
                              "Format is census://year/release/geo_containment/summary_level/table ")

        return parts

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('census')

    @property
    def year(self):
        return self._parts[0]

    @property
    def release(self):
        return self._parts[1]

    @property
    def geoid(self):
        return sub_geoids(self._parts[2])

    @property
    def summary_level(self):
        return sub_summarylevel(self._parts[3])

    @property
    def tableid(self):
        return sub_geoids(self._parts[4])

    @property
    def geo_url(self):
        """Return a url for the geofile for this Census file"""
        from geoid.acs import AcsGeoid

        us = tiger_url(self.year, self.summary_level, AcsGeoid.parse(self.geoid).stusab)

        return parse_app_url(us)

    @property
    def table(self):
        """Return the census table object"""
        return self.generator.table

    @property
    def meta(self):
        """Return a dict of column metadata"""
        return list(self.generator.meta)

    @property
    def dataframe(self):
        """Return a Pandas dataframe with the data for this table"""
        return self.generator.dataframe


    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()


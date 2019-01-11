# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" App Urls and generators for  accessing  static files from census.gov"""

from publicdata.census.appurl import CensusUrl
from publicdata.census.files.url_templates import tiger_url
from publicdata.census.util import sub_geoids, sub_summarylevel
from rowgenerators import parse_app_url
from rowgenerators.exceptions import AppUrlError
from warnings import warn

class CensusFileUrl(CensusUrl):

    """
    A URL that references row data from American Community Survey files

    census://2016/5/US/tract/B17001

    The general form is:

        census://year/release/geo_containment/summary_level/table

    """

    default_year = 2017

    def __init__(self, url=None, downloader=None, **kwargs):


        super().__init__(url, downloader, **kwargs)

        if self._year == 0:
            warn("Census URL '{}' is missing a year. Assuming {} ".format(url, self.default_year))
            self._year = self.default_year

        self.scheme = 'census'


    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme == 'census'

    @property
    def geo_url(self):
        """Return a url for the geofile for this Census file"""
        from geoid.acs import AcsGeoid

        return CensusGeoUrl(str(self), downloader=self.downloader)


    def _mangle_dataframe(self, df):
        """Manipulate datafames, mostly by creating a geoid index"""

        import geoid.acs
        from geoid.acs import AcsGeoid
        from geoid.core import get_class

        cls = get_class(geoid.acs, int(self.summary_level))

        # Transform the geoid to the normal ACS format
        try:
            # HACK! The '00US' part will be wrong if the geo file has a component,
            # but that should only be in the regional files, I think ...
            df['GEOID'] = df.GEOID.apply(lambda v: str(cls.parse(str(int(self.summary_level)).zfill(3) + '00US' +
                                                                     v)))
            #df.set_index('geoid_index', inplace = True)
        except:
            # Or dont ...
            pass

        df.columns = [c.lower() for c in df.columns]

        return df

    def geoframe(self):
        """Return a geoframe, with some modifications from the shapefile version. """
        return self.geo_url.geoframe()

    def dataframe(self):
        return super().dataframe()
        return self._mangle_dataframe(super().dataframe())

    @property
    def table(self):
        """Return the census table object"""
        return self.generator.table

    @property
    def meta(self):
        """Return a dict of column metadata"""
        return list(self.generator.meta)


    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()

CensusFile = CensusFileUrl

class CensusGeoUrl(CensusFileUrl):
    """ Defines a URL for a geographic shape file, of the form:

           censusgeo://<year>/<release/<geoid>/<summarylevel>

    """
    def __init__(self, url=None, downloader=None, **kwargs):

        super().__init__(url, downloader, **kwargs)

        self.scheme = 'censusgeo'

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme == 'censusgeo'

    @property
    def shape_url(self):
        """Return the shapefile URL"""
        from geoid.acs import AcsGeoid

        us = tiger_url(self.year, self.summary_level, AcsGeoid.parse(self.geoid).stusab)

        return parse_app_url(us)

    def get_resource(self):
        return self.shape_url.get_resource()

    def geoframe(self):
        """Return a geoframe, with some modifications from the shapefile version. """
        gf = self.get_resource().get_target().generator.geoframe()
        return self._mangle_dataframe(gf)

    def dataframe(self):
        raise NotImplementedError()
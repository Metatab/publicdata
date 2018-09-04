# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""


import json
from os.path import dirname, join

import requests
from publicdata.census.appurl import CensusUrl

from rowgenerators import parse_app_url
from rowgenerators.appurl.web import WebUrl
from rowgenerators.exceptions import AppUrlError
from publicdata.census.censusreporter.jsonurl import CensusReporterJsonUrl


class CensusReporterUrl(CensusUrl):
    """A URL for censusreporter tables.

    General form:

        censusreporter:<table_id>/<summary_level>/<geoid>

    for instance:

        censusreporter:B17001/140/05000US06073

    """

    api_host = 'api.censusreporter.org/1.0'

    def __init__(self, url=None, downloader=None, **kwargs):

        self._proto = 'censusreporter'

        super().__init__(url, downloader, **kwargs)

    @property
    def geo_url(self):
        """Return the geo version of this URL"""

        return CensusReporterShapeURL(str(self), downloader=self._downloader)

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('censusreporter')

    @property
    def resource_url(self):
        return WebUrl("http://{host}/data/show/latest?table_ids={table_id}&geo_ids={sl}|{geoid}" \
            .format(host=self.api_host,table_id=self.tableid, sl=self.summary_level, geoid=self.geoid),
                      downloader=self.downloader)

    def get_resource(self):
        cache = self.downloader.cache

        if cache and cache.exists(self.cache_key):
            pass

        else:
            r = requests.get(self.resource_url)
            r.raise_for_status()
            data = r.json()

            if cache:
                cache.makedirs(dirname(self.cache_key), recreate=True)
                cache.settext(self.cache_key, json.dumps(data, indent=4))

        return parse_app_url(cache.getsyspath(self.cache_key),
                             fragment=[join(*self.path_parts),None],
                             ).as_type(CensusReporterJsonUrl)

    def get_target(self):
        # get_resource returns a CensusReporterJsonUrl so this should never be called
        raise NotImplementedError()


CensusReporterURL = CensusReporterUrl # Legacy Name

class CensusReporterShapeURL(CensusReporterURL):
    """A URL for censusreporter tables.

    General form:

        censusreportergeo:<table_id>/<summary_level>/<geoid>

    for instance:

        censusreportergeo:B17001/140/05000US06073

    """

    api_host = 'api.censusreporter.org'

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

        self.scheme = 'censusreportergeo'


    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('censusreporter')



    @property
    def resource_url(self):

        return parse_app_url("http://{host}/1.0/data/download/latest?table_ids={table_id}&geo_ids={sl}|{geoid}&format=shp" \
            .format(host=self.api_host,table_id=self.tableid, sl=self.summary_level, geoid=self.geoid),
                      downloader=self.downloader)

    def get_resource(self):
        from os import symlink, remove
        from os.path import exists

        from rowgenerators.appurl.file.shapefile import ShapefileUrl

        r = ShapefileUrl(self.resource_url.get_resource())

        # The downloaded file doesn't have a .zip extension, so Fiona won't recognize
        # it as a Shapeilfe ZIP archive. So, just make a link.

        p = r.inner.fspath
        pz = p.with_suffix('.zip')

        if exists(pz):
            remove(pz)

        symlink(p, pz)

        return ShapefileUrl(pz)

    def get_target(self):

        raise NotImplementedError()

    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()
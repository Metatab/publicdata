# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""


import json
from os.path import dirname, join

import requests

from appurl import WebUrl, AppUrlError, parse_app_url
from publicdata.censusreporter.jsonurl import CensusReporterJsonUrl


class CensusReporterURL(WebUrl):
    """A URL for censusreporter tables.

    General form:

        censusreporter:<table_id>/<summary_level>/<geoid>

    for instance:

        censusreporter:B17001/140/05000US06073

    """

    api_host = 'api.censusreporter.org/1.0'

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

        self._parts # Will raise on format errors

    @property
    def _parts(self):
        if not self.netloc:
            # If the URL didn't have ://, there is no netloc
            parts =  self.path.strip('/').split('/')
        else:
            parts = tuple( [self.netloc] + self.path.strip('/').split('/'))

        if len(parts) != 3:
            raise AppUrlError("Census reporters must have three path components. Got: '{}' ".format(parts))

        return parts

    @property
    def table_id(self):
        return self._parts[0]

    @property
    def summary_level(self):
       return self._parts[1]

    @property
    def geoid(self):
        return self._parts[2]

    @property
    def geo(self):
        """Return the geo version of this URL"""

        return CensusReporterShapeURL(str(self), downloader=self._downloader)

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('censusreporter')

    @property
    def cache_key(self):
        """Return the path for this url's data in the cache"""
        return "{}/{}/{}/{}.json".format(self.api_host, *self._parts)

    @property
    def resource_url(self):
        return WebUrl("http://{host}/data/show/latest?table_ids={table_id}&geo_ids={sl}|{geoid}" \
            .format(host=self.api_host,table_id=self.table_id, sl=self.summary_level, geoid=self.geoid),
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
                             fragment=[join(*self._parts),None],
                             ).as_type(CensusReporterJsonUrl)

    def get_target(self):
        # get_resource returns a CensusReporterJsonUrl so this should never be called
        raise NotImplementedError()

    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()

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

        self._parts # Will raise on format errors

        self.scheme = 'censusreportergeo'

    @property
    def _parts(self):
        if not self.netloc:
            # If the URL didn't have ://, there is no netloc
            parts =  self.path.strip('/').split('/')
        else:
            parts = tuple( [self.netloc] + self.path.strip('/').split('/'))

        if len(parts) != 3:
            raise AppUrlError("Census reporters must have three path components. Got: '{}' ".format(parts))

        return parts

    @property
    def table_id(self):
        return self._parts[0]

    @property
    def summary_level(self):
       return self._parts[1]

    @property
    def geoid(self):
        return self._parts[2]

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('censusreporter')

    @property
    def cache_key(self):
        """Return the path for this url's data in the cache"""
        return "{}/{}/{}/{}.zip".format(self.api_host, *self._parts)

    @property
    def resource_url(self):

        return parse_app_url("http://{host}/1.0/data/download/latest?table_ids={table_id}&geo_ids={sl}|{geoid}&format=shp" \
            .format(host=self.api_host,table_id=self.table_id, sl=self.summary_level, geoid=self.geoid),
                      downloader=self.downloader)

    def get_resource(self):
        from os import symlink, remove
        from os.path import exists

        from rowgenerators.appurl.shapefile import ShapefileUrl

        r = ShapefileUrl(self.resource_url.get_resource())

        # The downloaded file doesn't have a .zip extension, so Fiona won't recognize
        # it as a Shapeilfe ZIP archive. So, just make a link.

        p = r.inner.path
        pz = p+'.zip'

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
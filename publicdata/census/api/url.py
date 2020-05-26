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
from publicdata.census.api.censusapi import  CensusApi
from rowgenerators import Url

class CensusApiUrl(Url):
    """A URL for censusreporter tables.

    General form:

        censusapi:<dataset>/<in_specification>/<for_specification>#<column_list>

    for instance:


    """

    def __init__(self, url=None, downloader='default', **kwargs):

        self._proto = 'censusapi'

        super().__init__(url, downloader, **kwargs)

        self.dataset_id, self.geo_in, self.geo_for = self.path.split('/')

        if not self.dataset_id: # The url has a :// in it
            self.dataset_id = self.netloc

        self._dataset = None

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme.startswith('censusapi')

    @property
    def dataset(self):
        if not self._dataset:
            self._dataset = CensusApi().get_dataset(self.dataset_id)

        return self._dataset

    @property
    def resource_url(self):
        predicates = {}

        url = self.dataset.fetch_url(*self.target_file.split(','),
                             geo_for=self.geo_for, geo_in=self.geo_in, **predicates)

        return parse_app_url(url, downloader=self.downloader)

    def get_resource(self):

        ru = self.resource_url.get_resource()

        return CensusApiResourceUrl(ru, downloader=self.downloader)

    def get_target(self):
        return self.get_resource().get_target()

    @property
    def generator(self):
        """
        Return the generator for this URL, if the rowgenerator package is installed.

        :return: A row generator object.
        """

        from rowgenerators.core import get_generator

        return self.get_resource().get_target().generator

    @property
    def dataframe(self):
        return self.generator.dataframe()

    @property
    def cache_key(self):
        """Return the path for this url's data in the cache"""
        raise NotImplementedError()


    @property
    def path_parts(self):
        raise NotImplementedError

    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()

from rowgenerators.generator.json import JsonRowSource
from rowgenerators.appurl.file.file import FileUrl


class CensusApiResourceUrl(FileUrl):
    """A URL for censusreporter tables.

    General form:

        censusapi:<dataset>/<in_specification>/<for_specification>#<column_list>

    for instance:


    """

    @classmethod
    def _match(cls, url, **kwargs):
        raise NotImplementedError

    @property
    def dataset(self):
        if not self._dataset:
            self._dataset = CensusApi().get_dataset(self.dataset_id)

        return self._dataset

    def get_resource(self):
        return self

    def get_target(self):
        return self

    @property
    def generator(self):
        return JsonRowSource(self)



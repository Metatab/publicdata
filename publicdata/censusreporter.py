# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""
Return dataframes from the Census Reporter API
"""

import requests
from operator import itemgetter
from rowgenerators import Source
from appurl import WebUrl, FileUrl, parse_app_url, AppUrlError
from appurl.util import slugify
import json
from os.path import dirname, join
from urllib.parse import unquote
from itertools import repeat

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

class CensusReporterJsonUrl(FileUrl):
    """Url for the JSON file downloaded by CensusReporterUrl"""

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

        # HACK This hsould be handled properly in parse_app_url
        self._fragment = kwargs.get('_fragment')
        self.scheme_extension = 'CRJSON'

    def get_resource(self):
        return self

    def get_target(self):
        return self


class CensusReporterSource(Source):
    """A RowGenerator source that can be registered for Census REporter URLs.

    To install it:

    > from rowgenerators import register_proto
    > register_proto('censusreporter', CensusReporterSource)

    Then, this class will be used for urls of the form:

        censusreporter:B17001/140/05000US06073

    or, Generically:

        censusreporter:<table_id>/<summary_level>/<geoid>

    """

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

        assert isinstance(ref, CensusReporterJsonUrl)

    # noinspection PyUnusedLocal
    def dataframe(self, limit=None):
        """
        Return a CensusReporterDataframe
        :param limit: Limit is ignored
        :return:
        """
        from .dataframe import CensusDataFrame

        rows, columns, release = self.get_cr_rows()

        df = CensusDataFrame(rows, schema=columns)

        df.release = release

        return df

    def __iter__(self):

        rows, self.columns, release = self.get_cr_rows()

        yield [e['code'] for e in self.columns]

        for row in rows:
            yield row


    def get_cr_rows(self):
        """
        :param cache: If true, cache the response from Census Reporter ( Fast and Friendly! )
        :param kwargs: Catchall so dict can be expanded into the signature.
        :return:
        """

        table_id, summary_level, geoid = unquote(self.ref.target_file).split('/')

        with open(self.ref.path) as f:
            data = json.load(f)

        # It looks like the JSON dicts may be properly sorted, but I'm not sure I can rely on that.
        # So, sort the column id values, then make a columns title list in the same order

        columns = [
            {
                'name': 'geoid',
                'code': 'geoid',
                'title': 'geoid',
                'code_title': 'geoid',
                'indent': 0,
                'index': '   ',  # Index in census table
                'position': 0  # Index in dataframe
            }, {
                'name': 'name',
                'code': 'name',
                'title': 'name',
                'code_title': 'name',
                'indent': 0,
                'index': '   ',
                'position': 1
            }
        ]

        title_stack = []

        if 'tables' not in data:
            print(json.dumps(data, indent=4))

        # SOme of the column codes have '.' in them; those are supposed to be headers, not real columns
        column_codes = sorted(c for c in data['tables'][table_id]['columns'].keys() if '.' not in c)

        for column in column_codes:

            name = data['tables'][table_id]['columns'][column]['name']
            indent = data['tables'][table_id]['columns'][column]['indent']

            index = column[-3:]

            if len(title_stack) <= indent:
                title_stack.extend(repeat('', indent - len(title_stack) + 1))
            elif len(title_stack) > indent:
                title_stack = title_stack[:indent + 1]

            title_stack[indent] = name.replace(':', '')

            columns.append({
                'name': name,
                'title': ' '.join(title_stack),
                'code': column,
                'code_title': column + " " + ' '.join(title_stack),
                'indent': indent,
                'index': index,
                'position': len(columns)})

            columns.append({
                'name': "Margins for " + name,
                'title': "Margins for " + ' '.join(title_stack),
                'code': column + "_m90",
                'code_title': "Margins for " + column + " " + ' '.join(title_stack),
                'indent': indent,
                'index': index,
                'position': len(columns)

            })

        rows = []

        row_ig = itemgetter(*column_codes)

        d = data['data']

        for geo in data['data'].keys():

            row = [geo, data['geography'][geo]['name']]

            ests = row_ig(d[geo][table_id]['estimate'])
            errs = row_ig(d[geo][table_id]['error'])

            # Some tables have only one column
            if not isinstance(ests, (list, tuple)):
                ests = [ests]

            if not isinstance(errs, (list, tuple)):
                errs = [errs]

            for e, m in zip(ests, errs):
                row.append(e)
                row.append(m)
            rows.append(row)

        assert len(rows) == 0 or len(columns) == len(rows[0])

        return rows, columns, data['release']



def make_citation_dict(t):
    """
    Return a dict with BibText key/values
    :param t:
    :return:
    """

    from nameparser import HumanName
    from datetime import datetime
    from appurl import Url

    try:
        if Url(t.url).proto == 'censusreporter':

            try:
                url = str(t.resolved_url.url)
            except AttributeError:
                url = t.url

            return {
                'type': 'dataset',
                'name': t.name,
                'origin': 'United States Census Bureau',
                'publisher': 'CensusReporter.org',
                'title': "2010 - 2015 American Community Survey, Table {}: {}".format(t.name.split('_', 1).pop(0), t.description),
                'year': 2015,
                'accessDate': '{}'.format(datetime.now().strftime('%Y-%m-%d')),
                'url': str(url)
            }
    except (AttributeError, KeyError) as e:

        pass


    return False

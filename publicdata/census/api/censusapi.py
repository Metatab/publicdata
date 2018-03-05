# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""
Access the Census API and create Pandas dataframes, with support for IPython and Jupyter display
"""

import json
from collections import UserList, UserDict
from textwrap import fill

import requests
from terminaltables import AsciiTable as TermTable
from .util import nl2br

from publicdata.censusreporter.exceptions import  AccessException


def _cached_get(url, cache=True):
    """Return the results of a GET request, possibly cached.
    Assumes the response is JSON"""

    from publicdata.censusreporter.util import get_cache, slugify

    cache_fs = get_cache()

    cache_key = slugify(url)

    if cache and cache_fs.exists(cache_key):
        data = json.loads(cache_fs.gettext(cache_key))
    else:
        try:
            r = requests.get(url)
            data = r.json()
            r.raise_for_status()
        except:
            raise AccessException("ERROR "+r.text)


        if cache:
            cache_fs.settext(cache_key, json.dumps(data, indent=4))

    return data


class VariableMeta(UserDict):
    def __init__(self, dict=None, **kwargs):
        super().__init__(dict, **kwargs)


class VariableList(UserList):
    """List container for dataset results"""

    def __init__(self, initlist=None):
        super().__init__(initlist)

    def _table_data(self):

        return ['Name Label Concept Type Required'.split()] + \
               [[e.get('name'), e.get('label'), e.get('concept'), e.get('predicateType', ''),
                 e.get('required', '')]
                for e in sorted(self.data, key=lambda e: e.get('name'))]

    def __str__(self):

        table = TermTable(self._table_data())

        table.inner_row_border = True

        return table.table

    def _repr_html_(self):

        data = self._table_data()

        def make_row(cells, tag='td'):
            return "<tr>{}</tr>".format(''.join("<{1}>{0}</{1}>".format(nl2br(str(c)), tag) for c in cells))

        return "<table>\n" + make_row(data[0],tag='th') +\
               ''.join(make_row(cells) for cells in data[1:]) + "</table>"

    def _repr_pretty_(self, p, cycle):
        """Default pretty printer """
        if cycle:
            p.text(self.__class__.__name__ + "(...)")
        else:
            p.text(str(self))


class DatasetMeta(UserDict):
    """Container for Dataset Metadata and an access API"""

    def __init__(self, dict=None, **kwargs):
        super().__init__(dict, **kwargs)

    @property
    def access_url(self):
        for d in self.get('distribution'):
            if d.get('format') == 'API':
                return d.get('accessURL')

    @property
    def id(self):
        return self.get('identifier', '').replace('http://api.census.gov/data/id/', '')

    @property
    def variables_meta(self):
        return _cached_get(self.c_variablesLink)

    @property
    def variables(self):
        return VariableList(sorted(
            [VariableMeta(dict([('name', k)] + list(v.items())))
             for k, v in self.variables_meta.get('variables', []).items()],
            key=lambda x: x.get('name', '').lower()
        ))

    def _search_variables(self, *args, **kwargs):
        import re

        for variable in sorted(self.variables, key=lambda d: d.get('label')):

            text = variable.get('name', '') + ' ' + variable.get('label', '') + ' ' + variable.get('concept', ' ')

            if any(a.search(text.lower()) if isinstance(a, re._pattern_type) else  a.lower() in str(text.lower())
                   for a in args):
                yield variable
                continue

            for k, v in kwargs.items():
                if isinstance(v, re._pattern_type) and v.search(variable.get(k, '')):
                    yield variable
                    break
                elif v in variable.get(k, ''):
                    yield variable
                    break

    def search_variables(self, *args, **kwargs):
        return VariableList(self._search_variables(*args, **kwargs))

    def __getattr__(self, item):
        return self[item]

    def fetch_url(self, *get, geo_for=None, geo_in=None, **predicates):
        from six.moves.urllib.parse import urlencode, quote_plus

        d = dict(
            get=','.join(quote_plus(e) for e in get)
        )

        if geo_for:
            d['for'] = geo_for

        if geo_in:
            d['in'] = geo_in

        for k, v in predicates.items():
            d[k] = v

        return self.access_url+"?"+urlencode(d)

    def fetch(self, *get, geo_for=None, geo_in=None, cache=True, **predicates ):

        url = self.fetch_url(*get, geo_for=geo_for, geo_in=geo_in, **predicates)

        return _cached_get(url, cache=cache)

    def fetch_dataframe(self, *get, geo_for=None, geo_in=None, cache=True, **predicates):
        import pandas

        d = self.fetch(*get, geo_for=geo_for, geo_in=geo_in, cache=cache, **predicates)

        return pandas.DataFrame(d[1:], columns=d[0])


    def _table_data(self):
        from textwrap import fill
        return [
            ['title', self.title],
            ['identitfier', self.identifier],
            ['description', fill(self.description, 75)],
            ['vintage', self.get('c_vintage')],
            ['Access Url', self.access_url],
            ['Geographies', self.get('c_geographyLink','').replace('.json','.html')],
            ['Variables', self.get('c_variablesLink', '').replace('.json', '.html')],
            ['Examples', self.get('c_examplesLink', '').replace('.json', '.html')],
        ]

    def __str__(self):

        table = TermTable(self._table_data())

        table.inner_row_border = False
        table.title = "Dataset " + self.id
        return table.table

    def _repr_html_(self):
        """Display routine for IPython"""

        data = self._table_data()

        def make_row(cells, tag='td'):
            return "<tr>{}</tr>".format(''.join("<{1}>{0}</{1}>".format(c, tag) for c in cells))

        return "<table>\n" + '\n'.join(make_row(cells) for cells in data) + "</table>"

    def _repr_pretty_(self, p, cycle):
        """Default pretty printer """
        if cycle:
            p.text(self.__class__.__name__ + "(...)")
        else:
            p.text(str(self))


class DatasetList(UserList):
    """List container for dataset results"""

    def __init__(self, initlist=None):
        super().__init__(initlist)

    @property
    def titles(self):
        """Return only the titles from the results"""
        return [e.get('title') for e in self.data]

    def _table_data(self):
        return ['Title Description '.split()] + \
               [[e.id + '\n' + fill(e.get('title', ''), 18),
                 fill(e.get('description', ''), 60)]
                for e in self.data]

    def __str__(self):

        data = self._table_data()

        table = TermTable(data)

        table.inner_row_border = True

        return table.table

    def _repr_html_(self):

        data = self._table_data()

        def make_row(cells, tag='td'):
            return "<tr>{}</tr>".format(''.join("<{1}>{0}</{1}>".format(nl2br(str(c)), tag) for c in cells))

        return "<table>\n" + make_row(data[0], tag='th') + \
               ''.join(make_row(cells) for cells in data[1:]) + "</table>"

    def _repr_pretty_(self, p, cycle):
        """Default pretty printer """
        if cycle:
            p.text(self.__class__.__name__ + "(...)")
        else:
            p.text(str(self))


class CensusApi(object):
    def __init__(self):
        pass

    @property
    def metadata(self):
        return self._metadata(cache=True)

    def _metadata(self, cache=True):
        """Return the API metadata"""

        url = "https://api.census.gov/data.json"

        return _cached_get(url, cache=cache)

    def _datasets(self):
        for _dataset in sorted(self.metadata.get('dataset', []), key=lambda d: d.get('title')):
            yield DatasetMeta(_dataset)

    @property
    def datasets(self):
        return DatasetList(self._datasets())

    def _search_datasets(self, *args, **kwds):

        import re

        for _dataset in sorted(self.metadata.get('dataset', []), key=lambda d: d.get('title')):

            dataset = DatasetMeta(_dataset)

            text = dataset.id + ' ' + \
                   dataset.get('title', '') + ' ' + \
                   dataset.get('description', ' ') + \
                   (' '.join(dataset.get('keyword', [])) + ' ' + str(dataset.get('vintage', ' ')))


            if any(a.search(text.lower()) if isinstance(a, re._pattern_type) else  a.lower() in str(text.lower())
                   for a in args):
                yield dataset
                continue

            for k, v in kwds.items():
                if isinstance(v, re._pattern_type) and v.search(dataset.get(k, '')):
                    yield dataset
                    break
                elif v in dataset.get(k, ''):
                    yield dataset
                    break

    def search_datasets(self, *args, **kwds):
        return DatasetList(self._search_datasets(*args, **kwds))


    def get_dataset(self, id):
        """Return a dataset given its id or identifier"""

        parts = id.split('/')

        ident = parts[-1]

        for d in self.metadata.get('dataset', []):

            if d.get('identifier', '').endswith('/' + ident):
                return DatasetMeta(d)

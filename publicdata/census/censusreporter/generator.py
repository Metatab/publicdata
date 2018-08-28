# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""


import json
from itertools import repeat
from operator import itemgetter
from urllib.parse import unquote

from publicdata.census.censusreporter.jsonurl import CensusReporterJsonUrl
from rowgenerators import Source


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

        self._source_url = kwargs.get('source_url')

        assert isinstance(ref, CensusReporterJsonUrl)

    @property
    def columns(self):
        """ Returns columns for the file accessed by accessor.

        """

        return self._columns

    # noinspection PyUnusedLocal
    def dataframe(self, limit=None):
        """
        Return a CensusReporterDataframe
        :param limit: Limit is ignored
        :return:
        """
        from publicdata.census.dataframe import CensusDataFrame

        rows, self._columns, release = self.get_cr_rows()

        df = CensusDataFrame(rows, schema=self._columns, url=self._source_url)

        df.release = release

        return df

    def __iter__(self):

        rows, self._columns, release = self.get_cr_rows()

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

        with open(self.ref.fspath) as f:
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
# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from publicdata.census.files.url_templates import seq_estimate_url, seq_margin_url, \
    seq_header_url, geo_header_url, geo_url
from publicdata.census.files.metafiles import TableLookup
from rowgenerators import parse_app_url
from functools import lru_cache
from operator import itemgetter
from rowgenerators import Source
from publicdata.census.files.appurl import CensusUrl

class _CensusFile(object):

    def __init__(self, year, release, stusab, summary_level, seq=None):
        self.year = year
        self.release = release
        self.stusab = stusab
        self.summary_level = summary_level
        self.seq = seq


class GeoFile(_CensusFile):

    def __init__(self, year, release, stusab, summary_level, seq=None):
        super().__init__(year, release, stusab, summary_level, seq)

        self.geo_header_url = geo_header_url(year, release, stusab, summary_level, seq)
        self.geo_url = geo_url(year, release, stusab, summary_level, seq)

    def __iter__(self):
        headers = list(parse_app_url(self.geo_header_url).generator)

        yield headers[0]

        t =  parse_app_url(self.geo_url).get_resource().get_target()
        t.encoding = 'latin1'

        yield from t.generator


# https://gist.github.com/smdabdoub/5213405
from itertools import chain

def ileave(*iters):
    return list(chain(*zip(*iters)))

class SequenceFile(_CensusFile):

    def __init__(self, year, release, stusab, summary_level, seq):
        super().__init__(year, release, stusab, summary_level, seq)

        self.est_url = seq_estimate_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        self.margin_url = seq_margin_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        self.headerurl = seq_header_url(self.year, self.release, self.stusab, self.summary_level, self.seq)

        self._file_headers, self._descriptions = list(parse_app_url(self.headerurl).generator)

    @property
    def file_headers(self):

        est_headers = self._file_headers[6:]
        margin_headers = [e + '_m90' for e in est_headers]

        return self._file_headers[:6] + ileave(est_headers, margin_headers)

    @property
    def descriptions(self):

        est_headers = self._descriptions[6:]
        margin_headers = [ '' for e in est_headers]

        return self._descriptions[:6] + ileave(est_headers, margin_headers)

    def __iter__(self):

        yield self.file_headers

        for e, m in zip(parse_app_url(self.est_url).generator, parse_app_url(self.margin_url).generator):
            yield e[:6] + list(ileave(e[6:], m[6:]))

@lru_cache(maxsize=100, typed=False)
def tablemeta(year, release):
    return TableLookup(year, release)


def try_number(v):
    try:
        return int(v)
    except:
        pass

    try:
        return float(v)
    except:
        pass

    return v

class Table(_CensusFile):
    """Iterator for a single table in a single segment file"""
    geo_headers = tuple('LOGRECNO GEOID SUMLEVEL STUSAB COUNTY NAME COMPONENT'.split())

    sl_col_pos = geo_headers.index('SUMLEVEL')


    def __init__(self, year, release, stusab, summary_level, tableid):
        super().__init__(year, release, stusab, summary_level, seq=None)

        self.meta = tablemeta(year, release)

        self.table = self.meta.tables[tableid.strip().lower()]

        seq = int(self.table.seq)
        self.geo_file = GeoFile(year, release, stusab, summary_level, seq)
        self.sequence_file = SequenceFile(year, release, stusab, summary_level, seq)

        # Get the column names that we will be extracting from the segment
        cols = [ self.table.columns[k].unique_id for k in sorted(self.table.columns.keys()) ]

        cols_m90 = [e+'_m90' for e in cols]

        self.table_columns = sorted(cols+cols_m90)

        self.chariter_pos = self.sequence_file.file_headers.index('CHARITER')
        self.lr_pos = self.sequence_file.file_headers.index('LOGRECNO')

        self.col_positions = [i+self.lr_pos+1 for i, c in enumerate(self.table_columns)]
        self.ig = itemgetter(*self.col_positions)

        print(self.sequence_file.file_headers)

    @property
    def file_headers(self):
        return self.geo['LOGRECNO']+('CHARITER',)+self.ig(self.sequence_file.file_headers)

    @property
    def descriptions(self):
        return self.geo['LOGRECNO']+('CHARITER',)+self.ig(self.sequence_file.descriptions)

    @property
    def geo(self):

        geo = {}

        lr_pos = None

        for i, row in enumerate(self.geo_file):
            if i == 0:
                col_positions = [row.index(c) for c in self.geo_headers]
                ig = itemgetter(*col_positions)
                lr_pos = row.index('LOGRECNO')

            else:
                geo[row[lr_pos]] = ig(row)

        # This one gets returned for the header row
        geo['LOGRECNO'] = self.geo_headers

        return geo

    def __iter__(self):

        geo = self.geo

        for i, row in enumerate(self.sequence_file):

            geo_cols = geo[row[self.lr_pos]]

            summary_level = geo_cols[self.sl_col_pos]

            if i == 0:
                yield geo_cols + (row[self.lr_pos],) + self.ig(row) # Headers, these are supposed to be strings
            else:
                if int(summary_level) == int(self.summary_level):
                    yield geo_cols +  (row[self.lr_pos],)  + tuple(try_number(e) for e in self.ig(row))


class CensusSource(Source):
    """ """

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        from geoid.acs import AcsGeoid
        from publicdata.census.files.metafiles import TableMeta

        super().__init__(ref, cache, working_dir, **kwargs)

        gid = AcsGeoid.parse(self.ref.geoid)

        self.table = Table(self.ref.year, self.ref.release, gid.stusab,
                   str(self.ref.summary_level), self.ref.tableid)

        self.meta = TableMeta(self.ref.year, self.ref.release)

        assert isinstance(ref, CensusUrl)

    @property
    def file_headers(self):
        return self.table.file_headers

    @property
    def descriptions(self):
        return self.table.descriptions

    def meta(self):
        {
            'name': name,
            'title': ' '.join(title_stack),
            'code': column,
            'code_title': column + " " + ' '.join(title_stack),
            'indent': indent,
            'index': index,
            'position': len(columns)
        }

    def __iter__(self):

        for row in self.table:
            yield (row[1],) + row[8:]
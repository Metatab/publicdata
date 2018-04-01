# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from publicdata.census.files.url_templates import seq_estimate_url, seq_margin_url, \
    seq_header_url, geo_header_url, geo_url
from publicdata.census.files.metafiles import TableMeta
from rowgenerators import parse_app_url
from functools import lru_cache
from operator import itemgetter
from rowgenerators import Source
from publicdata.census.files.appurl import CensusUrl
from copy import copy
from rowgenerators import SourceError
from itertools import chain
from functools import lru_cache

from . import logger


# https://gist.github.com/smdabdoub/5213405
@lru_cache(maxsize=100, typed=False)
def tablemeta(year, release):
    return TableMeta(year, release)


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


def ileave(*iters):
    return list(chain(*zip(*iters)))


class _CensusFile(object):

    def __init__(self, year, release, stusab, summary_level, seq=None):
        self.year = year
        self.release = release
        self.stusab = stusab
        self.summary_level = summary_level
        self.seq = seq


class GeoFile(_CensusFile):
    """This GeoFile holds information about the geographic summary level,
    not the shape of the boundary of the region. """

    def __init__(self, year, release, stusab, summary_level, seq=None):
        super().__init__(year, release, stusab, summary_level, seq)

        self.geo_header_url = geo_header_url(year, release, stusab, summary_level, seq)
        self.geo_url = geo_url(year, release, stusab, summary_level, seq)

    def __iter__(self):
        headers = list(parse_app_url(self.geo_header_url).generator)

        yield headers[0]

        t = parse_app_url(self.geo_url).get_resource().get_target()
        t.encoding = 'latin1'

        yield from t.generator


class SequenceFile(_CensusFile):

    def __init__(self, year, release, stusab, summary_level, seq):

        assert seq is not None

        super().__init__(year, release, stusab, summary_level, seq)

        self.est_url = seq_estimate_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        self.margin_url = seq_margin_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        self.headerurl = seq_header_url(self.year, self.release, self.stusab, self.summary_level, self.seq)

        self.table_meta = tablemeta(self.year, self.release)

        self._file_headers, self._descriptions = list(parse_app_url(self.headerurl).generator)

    @property
    def file_headers(self):

        est_headers = self._file_headers[6:]
        margin_headers = [e + '_m90' for e in est_headers]

        return self._file_headers[:6] + ileave(est_headers, margin_headers)

    @property
    def descriptions(self):

        est_headers = self._descriptions[6:]
        margin_headers = ['' for e in est_headers]

        return self._descriptions[:6] + ileave(est_headers, margin_headers)

    @property
    def meta(self):
        from .metafiles import Column

        columns = []

        for i, c in enumerate(self._file_headers[:6]):
            c = Column(None, c, i, description=c, short_desc=c, seq_file_col_no=i)
            columns.append(c)

        for k, v in self.table_meta.tables.items():
            if int(v.seq) == self.seq:
                for k in sorted(v.columns):
                    c = copy(v.columns[k])
                    c.seq_file_col_no = columns[-1].seq_file_col_no + 1
                    columns.append(c)

                    c = copy(v.columns[k])
                    c.unique_id = c.unique_id + '_m90'
                    c.seq_file_col_no = columns[-1].seq_file_col_no + 1
                    columns.append(c)

        return columns

    def __iter__(self):

        yield self.file_headers

        for e, m in zip(parse_app_url(self.est_url).generator, parse_app_url(self.margin_url).generator):
            yield e[:6] + list(ileave(e[6:], m[6:]))


class Table(_CensusFile):
    """Iterator for a single table in a single segment file"""
    geo_headers = tuple('LOGRECNO GEOID SUMLEVEL STUSAB COUNTY NAME COMPONENT'.split())

    sl_col_pos = geo_headers.index('SUMLEVEL')

    def __init__(self, year, release, stusab, summary_level, tableid):
        from geoid.censusnames import stusab as state_name_map

        super().__init__(year, release, stusab, summary_level, seq=None)

        self.meta = tablemeta(year, release)

        self.tableid = tableid.strip().lower()

        try:
            self.table = self.meta.tables[self.tableid]
        except KeyError as e:

            alt_c = 'c' + self.tableid[1:]
            alt_b = 'b' + self.tableid[1:]

            if (self.tableid.startswith('b') and alt_c in self.meta.tables):
                other_msg = f" However, table '{alt_c}' exists"
            elif (self.tableid.startswith('c') and alt_b in self.meta.tables):
                other_msg = f" However, table '{alt_b}' exists"
            else:
                other_msg = ''

            raise SourceError(f"Table metadata does not include table '{self.tableid}' " + other_msg)

        self.seq = int(self.table.seq)

        self.state_abs = list(state_name_map.values()) if self.stusab.upper() == 'US' else [self.stusab]

        # First sequence file
        sequence_file = SequenceFile(self.year, self.release, self.state_abs[0],
                                     self.summary_level, self.seq)

        # Get the column names that we will be extracting from the segment

        self._columns = []

        for c in sequence_file.meta:
            if c.table_id and c.table_id.lower() == tableid.lower():
                self._columns.append(c)

        self.lr_pos = sequence_file.file_headers.index('LOGRECNO')

        self.col_positions = [c.seq_file_col_no for c in self._columns]
        self.ig = itemgetter(*self.col_positions)

        geo = self.geo()

        self.file_headers = geo['LOGRECNO'][0] + self.ig(sequence_file.file_headers)
        self.descriptions = geo['LOGRECNO'][0] + self.ig(sequence_file.descriptions)

    @lru_cache()
    def geo(self, stusab=None):
        """Return a map of logrecno line numbers to geo headers values from the"""
        geo = {}

        sl_pos = lr_pos = None

        self.geo_file = GeoFile(self.year, self.release, stusab or self.state_abs[0],
                                self.summary_level, self.seq)

        for i, row in enumerate(self.geo_file):
            if i == 0:
                # Build an itemgeter for a few of the columns.
                ig = itemgetter(row.index('GEOID'),
                                row.index('STUSAB'),
                                row.index('COUNTY'),
                                row.index('NAME'))

                lr_pos = row.index('LOGRECNO')
                sl_pos = row.index('SUMLEVEL')

            geo[row[lr_pos]] =  ig(row), row[sl_pos], i

        # NOTE! Because the line above also runs on the header, getting
        # "geo['LOGRECNO']" will return the headers for the rows values.

        # This one gets returned for the header row; the rows are indexed by the LOGRECNO value,

        return geo

    @property
    def columns(self):
        """Yield Column objects for this table"""
        from .metafiles import Column

        cols = [None] * len(self.geo()['LOGRECNO'][0]) + self._columns

        # Geez, what a mess ...
        short_descriptions_map = { c.unique_id:c.description for c in self.table.columns.values() }

        for i, (f, d, c) in enumerate(zip(self.file_headers, self.descriptions, cols)):

            if c is None:
                c = Column(None, f, i, d, f, )

            c.col_no = i
            c.description = d
            c.short_description = short_descriptions_map.get(c.unique_id)

            yield c

    def _iter_components(self):

        i = 0
        for stusab in self.state_abs:

            logger.debug(f"Iterate {self.tableid} for state {stusab}")

            sequence_file = SequenceFile(self.year, self.release, stusab,
                                         self.summary_level, self.seq)

            geo = self.geo(stusab)

            for j, row in enumerate(sequence_file):

                lrno = row[self.lr_pos]

                geo_cols, summary_level, geo_row_n = geo[lrno]

                if i == 0 and j == 0:
                    yield i, 'stusab', 'row_n', geo_cols, self.ig(row)  # Headers, these are supposed to be strings
                elif j ==0:
                    pass # its a header on the second or later state
                else:
                    if int(summary_level) == int(self.summary_level):
                        yield i, stusab, stusab+str(int(lrno)), geo_cols, tuple(try_number(e) for e in self.ig(row))
                        
                i += 1

    def __iter__(self):
        
        for i, stusab, geo_row_n, geo_cols, data_cols in self._iter_components():
            yield geo_cols + data_cols

    @property
    def iterdata(self):
        """Iterate only the data columns excluding the geographic columns"""

        for i, stusab, lrno, geo_cols, data_cols in self._iter_components():
            yield (stusab+'_'+str(lrno),) + data_cols

    @property
    def itergeo(self):
        """Iterate only the geographic columns"""

        for i, stusab, lrno, geo_cols, data_cols in self._iter_components():
            yield (lrno,) + geo_cols


    def _repr_html_(self, **kwargs):

        from geoid.core import names as sl_names

        tm = self.table

        column_rows = ''
        for c in self.columns:
            column_rows += f"<tr><td>{c.col_no}</td><td>{c.unique_id}</td><td>{c.short_description}</td><td>{c.description}</td></tr>\n"

        try:
            sl_name = {v: k for k, v in sl_names.items()}.get(int(self.summary_level),
                                                              f'Summary Level {self.summary_level}')
        except ValueError as e:
            sl_name = self.summary_level

        return f"""
        <h1>Census Table {tm.unique_id} ({self.year}/{self.release})</h1>
        <p><i>{tm.title}, {tm.universe}. </i>{sl_name.title()} in {self.stusab} 
           {', Subject: '+tm.subject if tm.subject else ''}<p>
        <table>
        <tr><th>#</th><th>Name</th><th>Short Description</th><th>Description</th></tr>
        {column_rows}
        </table>
        """


class CensusSource(Source):
    """ """

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        from geoid.acs import AcsGeoid
        from publicdata.census.files.metafiles import TableMeta

        super().__init__(ref, cache, working_dir, **kwargs)

        gid = AcsGeoid.parse(self.ref.geoid)

        self.table = Table(self.ref.year, self.ref.release, gid.stusab,
                           str(self.ref.summary_level), self.ref.tableid)

        self._meta = TableMeta(self.ref.year, self.ref.release)

        assert isinstance(ref, CensusUrl)

    @property
    def file_headers(self):
        return self.table.file_headers

    @property
    def descriptions(self):
        return self.table.descriptions

    @property
    def columns(self):
        """Yield column objects for all columns"""
        yield from self.table.columns

    @property
    def meta(self):

        for c in self.columns:

            try:
                parts = c.unique_id.replace('_m90', '').split('_')
                index = int(parts[1])
            except IndexError:
                index = None

            yield {
                'name': c.unique_id,
                'title': c.description,
                'code': c.unique_id,
                'code_title': c.unique_id + ' ' + c.description if c.unique_id != c.description else c.unique_id,
                'indent': None,
                'index': index,
                'position': c.col_no
            }

    def dataframe(self, limit=None):
        """
        Return a CensusReporterDataframe
        :param limit: Limit is ignored
        :return:
        """

        from publicdata.census.dataframe import CensusDataFrame
        from itertools import islice
        import numpy as np

        rows = list(islice(self, 1, None))

        df = CensusDataFrame(rows, schema=self.meta, table=self.table, url=None)

        df.release = self.ref.release

        return df.replace('.', np.nan).set_index('GEOID')

    @property
    def geo_url(self):
        return self.ref.geo_url

    @property
    def geo(self):
        """Return a generator for the geographic file"""
        return self.geo_url.get_resource().get_target().generator

    @property
    def geoframe(self):

        import geopandas as gpd
        from shapely.geometry.polygon import BaseGeometry
        from shapely.wkt import loads

        rows = list(self.geo)

        gdf = gpd.GeoDataFrame(rows[1:], columns=[e.lower() for e in rows[0]])

        first = next(gdf.iterrows())[1].geometry

        if isinstance(first, str):
            shapes = [loads(row['geometry']) for i, row in gdf.iterrows()]

        elif not isinstance(first, BaseGeometry):
            # If we are reading a metatab package, the geometry column's type should be
            # 'geometry' which will give the geometry values class type of
            # rowpipe.valuetype.geo.ShapeValue. However, there are other
            # types of objects that have a 'shape' property.

            shapes = [row['geometry'].shape for i, row in gdf.iterrows()]

        else:
            shapes = gdf['geometry']

        gdf['geometry'] = gpd.GeoSeries(shapes)

        return gdf.set_geometry('geometry').set_index('geoid')

    def __iter__(self):
        yield from self.table

    @property
    def itergeo(self):
        yield from self.table.itergeo

    @property
    def iterdata(self):
        yield from self.table.iterdata

class CensusGeoSource(Source):

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

    def dataframe(self):
        pass

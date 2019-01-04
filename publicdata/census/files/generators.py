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



@lru_cache(maxsize=100, typed=False)
def tablemeta(year, release):
    """Function to cache creation of TableMeta objects"""
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
    return list(chain(*zip(*iters))) # From https://gist.github.com/smdabdoub/5213405


class _CensusFile(object):

    def __init__(self, year, release, stusab, summary_level, seq=None):
        try:
            self.year = int(year)
        except ValueError:
            self.year = year

        try:
            self.release = int(release)
        except ValueError:
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
    """Represents a single Sequence file, which holds data for a single state and may contain
    multiple tables"""
    
    def __init__(self, year, release, stusab, summary_level, seq):

        assert seq is not None

        super().__init__(year, release, stusab, summary_level, seq)

        # Url to the estimates
        self.est_url = seq_estimate_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        # Url to the margins
        self.margin_url = seq_margin_url(self.year, self.release, self.stusab, self.summary_level, self.seq)
        # Url to the file header, which includes fancy descriptions
        self.header_url = seq_header_url(self.year, self.release, self.stusab, self.summary_level, self.seq)

        self.table_meta = tablemeta(self.year, self.release)

        self._file_headers, _descriptions = list(parse_app_url(self.header_url).generator)

        # At least some of the fields have '%' as a seperator
        self._descriptions =  [ c.replace('%',' -') for c in _descriptions]

    @property
    def file_headers(self):

        est_headers = self._file_headers[6:]
        margin_headers = [e + '_m90' for e in est_headers]

        return self._file_headers[:6] + ileave(est_headers, margin_headers)

    @property
    def descriptions(self):

        # The descriptions is a 2-row Excel file, intended to be used as the headers
        # for the data files. The first row is the colum ids, and the second is
        # the titles. The first 6 columns are for STUSAB, SEQUENCE, LOGRECNO, etc,
        # so they are cut off.

        est_headers = self._descriptions[6:]
        margin_headers = ['' for e in est_headers]

        return self._descriptions[:6] + ileave(est_headers, margin_headers)

    @property
    def meta(self):
        from .metafiles import Column

        columns = []

        # Get column entries for the first 6 columns in the file, which are
        # support data, not estimates or margins. These are fake columns,
        # so they don't have a table id.
        for i, c in enumerate(self._file_headers[:6]):
            c = Column(None, None, c, i, description=c, short_desc=c, seq_file_col_no=i)
            columns.append(c)

        # The remainder of the columns come from the metadata, and do have an associated table.
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
    """Iterator for a single table in a single segment file

    This table is distinguished from meta.table in that this table is attached to a sequence,
    and the Sequence files have Sequence headers, which have the long descriptions. These descriptions for
    columns are fully-qualified paths in the hierarchy, so they can be parsed for race, sex and age information
    """
    geo_headers = tuple('LOGRECNO GEOID SUMLEVEL STUSAB COUNTY NAME COMPONENT'.split())

    sl_col_pos = geo_headers.index('SUMLEVEL')

    def __init__(self, year, release, stusab, summary_level, tableid):

        ## HACK! This initializer will download files. It should not

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
        self.sequence_file = SequenceFile(self.year, self.release, self.state_abs[0],
                                     self.summary_level, self.seq)

        # Get the column names that we will be extracting from the segment

        self._columns = []

        for c in self.sequence_file.meta:
            if c.table_id and c.table_id.lower() == tableid.lower():
                self._columns.append(c)

        self.lr_pos = self.sequence_file.file_headers.index('LOGRECNO')

        self.col_positions = [c.seq_file_col_no for c in self._columns]
        self.ig = itemgetter(*self.col_positions)

        geo = self.geo()

        self.file_headers = geo['LOGRECNO'][0] + self.ig(self.sequence_file.file_headers)
        self.descriptions = geo['LOGRECNO'][0] + self.ig(self.sequence_file.descriptions)



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

        for i, (f, ld, c) in enumerate(zip(self.file_headers, self.descriptions, cols)):

            if c is None:
                # Column(table, table_id, col_id, col_no, description=None, short_desc=None, seq_file_col_no=None):
                c = Column(self.table, self.tableid, f, i, ld, f )

            c.col_no = i # Why are we assigning this again? It was set in the initializer
            c.long_description = ld

            # Long description includes the table title
            c.description = ' - '.join(c.long_description.split(' - ')[1:])

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

        try:
            stusab = gid.stusab
        except AttributeError:
            gid.us# "US" level geoids don't have a state parameter.
            stusab = "US"

        self.table = Table(self.ref.year, self.ref.release, stusab,
                           str(self.ref.summary_level), self.ref.tableid)

        self._meta = TableMeta(self.ref.year, self.ref.release)

        self._source_url = kwargs.get('source_url')

        assert(self._source_url)

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

    def dataframe(self, *args, limit=None, **kwargs):
        """
        Return a CensusReporterDataframe
        :param limit: Limit is ignored
        :return:
        """

        from publicdata.census.dataframe import CensusDataFrame
        from itertools import islice
        import numpy as np

        rows = list(islice(self, 1, None))

        df = CensusDataFrame(rows, schema=self.meta, table=self.table, url=self._source_url)

        df.release = self.ref.release

        return df.replace('.', np.nan).set_index('GEOID')

    def geoframe(self, *args, limit=None, **kwargs):
        """Return a geoframe for the associated geographic information"""
        from rowgenerators import geoframe

        return self.ref.geo_url.generator.geoframe(*args, **kwargs)



    def __iter__(self):
        yield from self.table

    @property
    def itergeo(self):
        yield from self.table.itergeo

    @property
    def iterdata(self):
        yield from self.table.iterdata

from rowgenerators.generator.shapefile import ShapefileSource

class CensusGeoSource(ShapefileSource):

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

    def geoframe(self):
        gdf =  super().geoframe()
        return self.ref._mangle_dataframe(gdf)




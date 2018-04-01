# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


"""Classes to acess metadata files"""
from publicdata.census.files.url_templates import table_shell_url, table_lookup_url
from rowgenerators import parse_app_url


class Table(object):
    """Represents a  Census Table"""
    csv_header = 'id seq start title universe subject'.split()

    def __init__(self, table_id, title, universe=None, seq=None, fileid=None, startpos=None, subject=None):
        self.unique_id = table_id
        self.title = title
        self.universe = universe
        self.releases = set()

        self.seq = seq
        self.fileid = fileid
        self.startpos = startpos
        self.subject = subject

        self.columns = {}

    @property
    def row(self):
        return [
            self.unique_id,
            self.seq,
            self.startpos,
            self.title,
            self.universe,
            self.subject
        ]

    def _repr_html_(self, **kwargs):

        column_rows = ''
        for col_pos in sorted(self.columns):
            c = self.columns[col_pos]
            column_rows += f"<tr><td>{c.col_no}</td><td>{c.unique_id}</td><td>{c.short_description}</td><td>{c.description}</td></tr>\n"

        return f"""
        <h1>Census Table {self.unique_id}</h1>
        <i>{self.title}</i>
        <p>Universe: {self.universe}, Subject {self.subject}</p>
        <p>Seq {self.seq}, Start {self.startpos}<p>
        <table>
        <tr><th>#</th><th>Name</th><th>Short Description</th><th>Description</th></tr>
        {column_rows}
        </table>
        """



class Column(object):
    """Represents a column in a Census Table"""
    csv_header = 'tableid id colno desc short_desc'.split()

    def __init__(self, table_id, col_id, col_no, description=None, short_desc=None, seq_file_col_no=None):
        self.table_id = table_id
        self.unique_id = col_id
        self.description = description
        self.short_description = short_desc
        self.col_no = col_no
        self.seq_file_col_no = seq_file_col_no

    @property
    def row(self):
        return [
            self.table_id,
            self.unique_id,
            self.col_no,
            self.seq_file_col_no,
            self.description,
            self.short_description
        ]


class TableShell(object):
    """Collection of tables and columns"""

    def __init__(self, year, release):
        url_s = table_shell_url(year=year, release=release, stusab=None, summary_level=None, seq=None)

        self.url = parse_app_url(url_s)

        self._tables = None

    def _process(self, tables=None):

        if self._tables:
            return self._tables

        tables = tables or {}

        for row in self.url.generator.iter_rp:

            if not row[0].strip():
                continue

            table_id_key = row[0].strip().lower()

            if not row['UniqueID']:  # Table row

                if table_id_key not in tables:
                    tables[table_id_key] = Table(row[0], row['Stub'].strip())
                elif 'Universe' in row['Stub']:
                    tables[table_id_key].universe = row['Stub'].strip().replace('Universe: ', '')

            else:  # column row

                line_no = int(row['Line'])

                if not line_no in tables[table_id_key].columns:
                    startpos = tables[table_id_key].startpos or 0

                    tables[table_id_key].columns[line_no] = Column(row[0], row['UniqueID'], line_no,
                                                                   short_desc=row['Stub'],
                                                                   seq_file_col_no=line_no+startpos)
                else:
                    tables[table_id_key].columns[line_no].short_desc = row['Stub']

        self._tables = tables

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process(self)

        return self._tables

class TableLookup(object):

    def __init__(self, year, release):

        from rowgenerators.appurl.file import CsvFileUrl

        url_s = table_lookup_url(year=year, release=release, stusab=None, summary_level=None, seq=None)

        url = str(parse_app_url(url_s).get_resource().get_target())

        self.url = CsvFileUrl(url, encoding='latin1')

        self._tables = None

    def _process(self, tables=None):
        """Build the local data structure from the source data structure"""

        if self._tables:
            return self._tables

        tables = tables or {}

        for row in self.url.generator.iter_rp:

            table_id_key = row['Table ID'].strip().lower()

            if not row['Line Number'].strip():
                if 'Universe' not in row['Table Title']:
                    if table_id_key not in tables:
                        tables[table_id_key] = Table(row['Table ID'], row['Table Title'].strip().title(),
                                                        seq=row['Sequence Number'],
                                                        startpos=int(row['Start Position']))
                    else:
                        tables[table_id_key].seq = row['Sequence Number']
                        tables[table_id_key].startpos = row['Start Position']
                        tables[table_id_key].subject = row['Subject Area']

                else:
                    tables[table_id_key].universe = row['Table Title'].replace('Universe: ', '').strip()

            else:  # column row
                try:

                    line_no = int(row['Line Number'])

                    if not line_no in tables[table_id_key].columns:
                        tables[table_id_key].columns[line_no] = Column(row['Table ID'],
                                                                          f"{row['Table ID']}_{line_no:03}",
                                                                          line_no,
                                                                          description=row['Table Title'])
                    else:
                        tables[table_id_key].columns[line_no].description = row['Table Title']


                except ValueError as e:
                    # Headings, which have fractional line numebrs
                    # print(row)
                    pass

        self._tables = tables

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process()

        return self._tables


class TableMeta(object):
    """Combines the lookup and  shell objects"""

    def __init__(self, year, release):

        from rowgenerators.appurl.file import CsvFileUrl

        self.year = year
        self.release = release

        self.ts = None
        self.tl = None

        self._tables = None

    def _process(self):

        if self._tables:
            return self._tables

        #self.ts = TableShell(self.year, self.release)
        #self._tables = self.ts._process()

        self._tables = {}

        self.tl = TableLookup(self.year, self.release)
        self._tables = self.tl._process(tables=self._tables)

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process()

        return self._tables

    @property
    def summary_levels(self):
        """Return a dict of summary level names, numebrs and descriptions"""
        from geoid.core import names, descriptions

        sl = {}

        for sl_name, sl_no in names.items():
            sl[sl_no] = {
                'number': sl_no,
                'name': sl_name,
                'desc': descriptions.get(sl_no)
            }

        return sl

    @property
    def states(self):
        """Return a dict of state names, numbers and abbreviations"""
        from geoid.core import names
        from geoid.censusnames import geo_names, stusab

        states = {}

        for state_no, stusab in stusab.items():
            states[stusab] = {
                'name': geo_names[(state_no,0)],
                'stusab': stusab,
                'number' : state_no
            }

        states['US'] = {
                'name': 'United States',
                'stusab': 'US',
                'number' : 0
            }

        return states



    def _repr_html_(self, **kwargs):

        return f"""
        <h1>Census Metadata {self.year}, release {self.release}
        <table>
        <tr><td>Meta Tables</td><td>{len(self.tables)}</td></tr>
        <tr><td>Shell Tables</td><td>{len(self.ts.tables) if self.ts else 0}</td></tr>
        <tr><td>Lookup Tables</td><td>{len(self.tl.tables) if self.tl else 0}</td></tr>
        </table>"""


class SequenceMeta(object):
    pass
# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


"""Classes to acess metadata files"""
from publicdata.census.files.url_templates import table_shell_url, table_lookup_url
from rowgenerators import parse_app_url


class Table(object):

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


class Column(object):
    csv_header = 'tableid id colno desc short_desc'.split()

    def __init__(self, table_id, col_id, col_no, description=None, short_desc=None, seq_file_col_no=None):
        self.table_id = table_id
        self.unique_id = col_id
        self.description = description
        self.sort_description = short_desc
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
            self.sort_description
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
                    tables[table_id_key].columns[line_no] = Column(row[0], row['UniqueID'], line_no,
                                                                   short_desc=row['Stub'],
                                                                   seq_file_col_no=line_no+tables[table_id_key].startpos)
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

        self._tables = None

    def _process(self):

        if self._tables:
            return self._tables

        ts = TableShell(self.year, self.release)
        self._tables = ts._process()

        tl = TableLookup(self.year, self.release)
        tl._process(tables=self.tables)

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process(self)

        return self._tables


class SequenceMeta(object):
    pass
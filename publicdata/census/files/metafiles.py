# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


"""Classes to acess metadata files"""
from publicdata.census.files.url_templates import table_shell_url, table_lookup_url, seq_estimate_url, seq_margin_url, \
    seq_header_url, geo_header_url, geo_url

from rowgenerators import parse_app_url


race_iterations = [
        ('A', 'white',   'White'),
        ('B', 'black',   'Black or African American'),
        ('C', 'aian',    'American Indian and Alaska Native'),
        ('D', 'asian',   'Asian'),
        ('E', 'nhopi',   'Native Hawaiian and Other Pacific Islander'),
        ('F', 'other',   'Some Other Race'),
        ('G', 'many',    'Two or More Races'),
        ('H', 'nhwhite', 'White Alone, Not Hispanic or Latino'),
        ('N', 'nhisp',   'Not Hispanic or Latino'),
        ('I', 'hisp',    'Hispanic or Latino'),
        ('C', 'aian',    'American Indian'),
        (None, 'all',    'All races')]

ri_code_map = { code.lower():race for code, race, term in race_iterations if code}


class Table(object):
    """Represents a  Census Table"""

    csv_header = 'id seq start title universe subject'.split()

    def __init__(self, table_id, title, universe=None, seq=None, fileid=None, startpos=None, subject=None):
        self.unique_id = table_id
        self.title = title
        self.universe = universe
        self.releases = set()

        self.number_of_segments = 1 # > 1 for multi-segment tables, like b24010 or b24121

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


    @property
    def race(self):
        """Return a race code from the table id"""

        return ri_code_map.get(self.unique_id[-1].lower)


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

    def __init__(self, table, table_id, col_id, col_no, description=None, short_desc=None, seq_file_col_no=None):
        self.table = table
        self.table_id = table_id
        self.unique_id = col_id
        self.description = description
        self.short_description = short_desc
        self.long_description = short_desc
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
            self.short_description,
            self.long_description,
        ]


    @property
    def sex(self):
        v = self.description.lower()

        if 'male' in v:
            return 'male'
        elif 'female' in v:
            return 'female'
        else:
            return 'both'

    @property
    def race(self):

        race_from_table = ri_code_map.get(self.table_id[-1].lower())

        if race_from_table and race_from_table != 'all':
            return race_from_table

        # Special case for a specific table, C02003
        if 'two or more races' in self.long_description:
            return 'many'

        v = self.description.lower()

        for code, race, term in race_iterations:
            if term.lower() in v.lower():
                return race

        # Maybe there is more race information in the table title, but
        # it isn't an iteration, like:
        # b02015: Asian Alone By Selected Groups

        v = self.long_description.lower()

        for code, race, term in race_iterations:
            if term.lower() in v.lower():
                return race

        return 'all'

    @property
    def age_range(self):
        """Parse the description fo an age range"""
        import re

        v = self.description.lower()

        pats = {
            'to':re.compile("(?P<lower>\d+) to (?P<upper>\d+) years"),
            'and':re.compile("(?P<lower>\d+) and (?P<upper>\d+) years"),
            'under':re.compile("under (?P<upper>\d+) years"),
            'over': re.compile("(?P<lower>\d+) years and over"),
            'single':re.compile("(?P<upperlower>\d+) years"),

        }

        if v and 'year' in v:

            v = v.replace('1 year ago', '').replace('year-round','')

            m = pats['to'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = pats['and'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = pats['under'].search(v)
            if m:
                return (0, int(m.group('upper')))

            m = pats['over'].search(v)
            if m:
                return (int(m.group('lower')), 120)

            m = pats['single'].search(v)
            if m:
                return (int(m.group('upperlower')), int(m.group('upperlower')))

        return None

    @property
    def age(self):
        ar = self.age_range
        if ar:
            return "{:03d}-{:03d}".format(*ar)
        else:
            return 'all'


    @property
    def poverty_status(self):

        v = self.long_description.lower()

        pov_map = {
            'under 1.00':              'lt100',
            'below 100 percent of the poverty level': 'lt100',
            'below poverty level':     'lt100',
            'below the poverty level': 'lt100',
            'above poverty level':     'gt100',
            'above the poverty level': 'gt100',
            '100 to 149 percent of the poverty level': '100-150',
            'at or above 150 percent of the poverty level': 'gt150',
            '1.00 to 1.99':           '100-200',
            '2.0  and over':          'gt200'
        }

        for term, code in pov_map.items():
            if term in v:
                return code

        return None




class TableShell(object):
    """Access object for table shell files.

    The Shell Files, such as:

        https://www2.census.gov/programs-surveys/acs/summary_file/2016/documentation/user_tools/ACS2016_Table_Shells.xlsx

    The Shell files have information about each table and columns, including:
        * Table Id
        * Data column line number in the table
        * Column title ( called "Stub" )
        * Which release the column is available in

    """

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

                try:
                    line_no = int(row['Line'])

                except ValueError:
                    # Probably, the line number  is a float, which indicates a header line. Header lines don't have
                    # estimates associated with them, so we exclude them.
                    pass
                else:

                    if not line_no in tables[table_id_key].columns:
                        startpos = tables[table_id_key].startpos or 0

                        tables[table_id_key].columns[line_no] = Column(None, row[0], row['UniqueID'], line_no,
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
    """Access object for the TableLookup files.

    The Lookup files, such as:

        https://www2.census.gov/programs-surveys/acs/summary_file/2017/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt

    have information about each table and column, including:
        * Table Number
        * Column Line
        * Table start position in sequence file
        * Total cells in table and sequence
        * Short column title

    """

    def __init__(self, year, release):


        self.url = table_lookup_url(year=year, release=release, stusab=None, summary_level=None, seq=None)

        self._tables = None

    def _process(self, tables=None):
        """Build the local data structure from the source data structure"""

        from rowgenerators.appurl.file import CsvFileUrl

        if self._tables:
            return self._tables

        tables = tables or {}

        url = str(parse_app_url(self.url).get_resource().get_target())

        csv_url = CsvFileUrl(url, encoding='latin1')

        for row in csv_url.generator.iter_rp:

            table_id_key = row['Table ID'].strip().lower()

            if not row['Line Number'].strip(): # Either the table title, or the Universe row
                
                if 'Universe' not in row['Table Title']:
                    if table_id_key not in tables:
                        tables[table_id_key] = Table(row['Table ID'], row['Table Title'].strip().title(),
                                                        seq=[int(row['Sequence Number'])],
                                                        startpos=int(row['Start Position']),
                                                        subject=row['Subject Area'])
                    else:
                        # This case is for muli-segment tables
                        assert(int(row['Start Position']) == 7) # Should always start at the beginning of the segment

                        tables[table_id_key].seq.append(int(row['Sequence Number']))

                        tables[table_id_key].number_of_segments += 1


                else:
                    tables[table_id_key].universe = row['Table Title'].replace('Universe: ', '').strip()

            else:  # column row
                try:

                    line_no = int(row['Line Number'])

                    if not line_no in tables[table_id_key].columns:
                        tables[table_id_key].columns[line_no] = Column(tables[table_id_key], row['Table ID'],
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
    """Combines the lookup and  shell objects, but mostly just uses the TableLookup"""

    def __init__(self, year, release):

        self.year = year
        self.release = release

        self.ts = None
        self.tl = None

        self._tables = None

    def _process(self):

        if self._tables:
            return self._tables

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
        """Return a dict of summary level names, numbers and descriptions"""
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
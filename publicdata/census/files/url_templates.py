# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""URl Template for file locations"""

acs_base_url = 'https://www2.census.gov/programs-surveys/acs/summary_file/{year}'
acs_data_base_url = acs_base_url+'/data'

def geo_name(year, release, summary_level):
    """Resolve a year, release and summar level number into a URL geography group name"""
    if int(summary_level) in (140, 150):
        return 'Tracts_Block_Groups_Only'
    else:
        return 'All_Geographies_Not_Tracts_Block_Groups'

def state_name(stusab, year, release):

    states_by_stusab = {e[1]: e[2] for e in states}

    # The code fo DC is inconsistent
    yr_code = str(year)+str(release)

    if stusab.upper() == 'DC' and release == 1:
        return 'DistrictofColumbia'
    else:
        return states_by_stusab[stusab.upper()]

# Only US states and PR; excludes most US territories.
states = [(2, 'AK', 'Alaska'), (1, 'AL', 'Alabama'), (4, 'AZ', 'Arizona'), (5, 'AR', 'Arkansas'),
          (6, 'CA', 'California'), (8, 'CO', 'Colorado'), (9, 'CT', 'Connecticut'), (10, 'DE', 'Delaware'),
          (11, 'DC', 'DistrictOfColumbia'), (12, 'FL', 'Florida'), (13, 'GA', 'Georgia'), (15, 'HI', 'Hawaii'),
          (16, 'ID', 'Idaho'), (17, 'IL', 'Illinois'), (18, 'IN', 'Indiana'), (19, 'IA', 'Iowa'), (20, 'KS', 'Kansas'),
          (21, 'KY', 'Kentucky'), (22, 'LA', 'Louisiana'), (23, 'ME', 'Maine'), (24, 'MD', 'Maryland'),
          (25, 'MA', 'Massachusetts'), (26, 'MI', 'Michigan'), (27, 'MN', 'Minnesota'), (28, 'MS', 'Mississippi'),
          (29, 'MO', 'Missouri'), (30, 'MT', 'Montana'), (31, 'NE', 'Nebraska'), (32, 'NV', 'Nevada'),
          (33, 'NH', 'NewHampshire'), (34, 'NJ', 'NewJersey'), (35, 'NM', 'NewMexico'), (36, 'NY', 'NewYork'),
          (37, 'NC', 'NorthCarolina'), (38, 'ND', 'NorthDakota'), (39, 'OH', 'Ohio'), (40, 'OK', 'Oklahoma'),
          (41, 'OR', 'Oregon'), (42, 'PA', 'Pennsylvania'), (72, 'PR', 'PuertoRico'), (44, 'RI', 'RhodeIsland'),
          (45, 'SC', 'SouthCarolina'), (46, 'SD', 'SouthDakota'), (47, 'TN', 'Tennessee'), (48, 'TX', 'Texas'),
          (49, 'UT', 'Utah'), (50, 'VT', 'Vermont'), (51, 'VA', 'Virginia'), (53, 'WA', 'Washington'),
          (54, 'WV', 'WestVirginia'), (55, 'WI', 'Wisconsin'), (56, 'WY', 'Wyoming')]

##
## Header files
##

header_template = acs_data_base_url + '/{year}_{release}yr_Summary_FileTemplates.zip'


seq_header_resource_template = 'Seq{seq}.xls'

geo_header_resource_template = '{year}_SFGeoFileTemplate.xls'

def header_archive_url(year, release, stusab, summary_level, seq=None):
    """Return the URL to the summary file header archive file"""
    return header_template.format(
        year=int(year),
        release=int(release),
        geo_name=geo_name(year=year, release=release, summary_level=summary_level)
    )

def seq_header_url(year, release, stusab, summary_level, seq=None):
    """Return the URL to the summary file header, possibly within an  archive file"""
    hau =  header_archive_url(year, release, summary_level, seq)

    return hau+'#'+seq_header_resource_template.format(seq=seq)

def geo_header_url(year, release, stusab, summary_level, seq=None):
    """Return the URL to the summary file header, possibly within an  archive file"""
    hau =  header_archive_url(year, release, stusab, summary_level, seq)

    return hau+'#'+geo_header_resource_template.format(year=year)

##
## Sequence files
##

seq_file_templates = acs_data_base_url + \
                     '/{release}_year_seq_by_state/{stname_title}/{geo_name_slash}' + \
                     '{year}{release}{stusab}{seq4}000.zip'


def seq_archive_url(year, release, stusab, summary_level, seq):
    """Return the URL to a squence archive file"""


    if release == 1:
        geo_name_slash = ''
    else:
        geo_name_slash = geo_name(year=year, release=release, summary_level=summary_level)+'/'

    return seq_file_templates.format(
        year=int(year),
        release=int(release),
        geo_name_slash=geo_name_slash,
        stname_title = state_name(stusab.upper(), year, release),
        stusab=stusab.lower(),
        seq4=str(int(seq)).zfill(4)
    )

def seq_estimate_url(year, release, stusab, summary_level, seq):
    """Return the URL to an estimate file, possibly within an archive file"""

    assert seq is not None

    sau = seq_archive_url(year, release, stusab, summary_level, seq)

    return sau + '#' + 'e{year}{release}{stusab}{seq4}000.txt&target_format=csv'.format(
        year=int(year),
        release=int(release),
        stusab=stusab.lower(),
        seq4=str(int(seq)).zfill(4)
    )


def seq_margin_url(year, release, stusab, summary_level, seq):
    """Return the URL to an estimate file, possibly within an archive file"""

    sau = seq_archive_url(year, release, stusab, summary_level, seq)

    return sau + '#' + 'm{year}{release}{stusab}{seq4}000.txt&target_format=csv'.format(
        year=int(year),
        release=int(release),
        stusab=stusab.lower(),
        seq4=str(int(seq)).zfill(4)
    )

##
## Geo files
##

# Full state geofile, with seperate values for each component
geo_file_template = acs_data_base_url + \
                    '/{release}_year_seq_by_state/{stname_title}/{geo_name_slash}' + \
                    'g{year}{release}{stusab_l}.csv'

# https://www2.census.gov/programs-surveys/acs/summary_file/2016/documentation/geography/1_year_Mini_Geo.xlsx
# https://www2.census.gov/programs-surveys/acs/summary_file/2016/documentation/geography/5yr_year_geo/
# Geo file with just the geoids and the file line numbers

geoid_file_template_1 = acs_base_url + '/documentation/geography/1_year_Mini_Geo.xlsx'

geoid_file_template_5 = acs_base_url + \
                    '/documentation/geography/5yr_year_geo/{stusab_l}.xslx'

def geo_url(year, release, stusab, summary_level, seq):

    if release == 1:
        geo_name_slash = ''
    else:
        geo_name_slash = geo_name(year=year, release=release, summary_level=summary_level)+'/'

    return geo_file_template.format(
        year=int(year),
        release=int(release),
        stname_title=state_name(stusab.upper(), year, release),
        stusab=stusab.upper(),
        stusab_l=stusab.lower(),
        geo_name_slash=geo_name_slash
    )

def geoid_url(year, release, stusab, summary_level, seq):

    if release == 1:
        t = geoid_file_template_1
    else:
        t = geoid_file_template_5

    return t.format(
        year=int(year),
        release=int(release),
        stname_title=state_name(stusab.upper(), year, release),
        stusab=stusab.upper(),
        stusab_l=stusab.lower()
    )
##
## Table Shells and Lookups
##


table_shell_templates = {
    2013: acs_base_url + '/documentation/user_tools/ACS{year}_TableShells.xls',
    2014: acs_base_url + '/documentation/user_tools/ACS{year}_Table_Shells.xlsx'
}

lookup_template = acs_base_url + '/documentation/user_tools/ACS_{release}yr_Seq_Table_Number_Lookup.txt'


def table_shell_url(year, release, stusab, summary_level, seq=None):

    if int(year) >= 2014:
        table_shell_template = table_shell_templates[2014]
        frag = ''
    else:
        table_shell_template = table_shell_templates[2013]
        frag = '#1'

    return table_shell_template.format(year=int(year))+frag


def table_lookup_url(year, release, stusab, summary_level, seq=None):
    return lookup_template.format(year=year, release=int(release))


def tiger_url(year, summary_level, stusab=None):
    """

    :param year: Vintage year
    :param summary_level: Summary level, in number format
    :param stusab: US State abbreviation
    :return:
    """


    from geoid.censusnames import  stusab as _stusab_map
    from geoid.core import names as _sl_names

    sl_name_map = { v:k for k,v in _sl_names.items() }

    stusab_map = { v:k for k,v in _stusab_map.items()}

    state = stusab_map.get(stusab.upper())

    try:
        sl = sl_name_map[int(summary_level)].upper()
    except ValueError:
        sl_u = summary_level.upper()


    # ftp://ftp2.census.gov/geo/tiger/TIGER2016/TRACT/tl_2016_15_tract.zip

    base =  f'shape+ftp://ftp2.census.gov/geo/tiger/TIGER{year}/{sl.upper()}'

    if sl=='COUNTY':
        return base+f'/tl_{year}_us_{sl.lower()}.zip'
    else:
        return base+f'/tl_{year}_{state:02}_{sl.lower()}.zip'


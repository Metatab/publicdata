# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Functions for discovering and using dimensions

"""

import re

# Age Ranges.

age_patterns = re.compile(r'(?P<range>(\d+) to (\d+) years)|'
               r'(?P<over>(\d+) years and over)|'
               r'(?P<and>(\d+) and (\d+) years)|'
               r'(?P<under>Under (\d+) years)|'
               r'(?P<single>(\d+) years)'
               )

age_formats = { 'and': '{:02d},{:02d}',
            'range': '{:02d}-{:02d}',
            'over': '{:02d}+',
            'single': '{:02d}',
            'under': '00-{:02d}'}

def age_range(c):
    """return the age range for a column"""

    # Questions about grandparents
    if 'grand' in c.description.lower():
        return 'na'

    m = age_patterns.search(c.description.strip())
    if m:
        format = None
        d = m.groupdict()
        for k in age_formats.keys():
            if k in d.keys() and d[k] is not None:
                format = k
                break

        ages = []
        for v in m.groups():
            try:
                ages.append(int(v))
            except:
                pass

        if format == 'and':  # convert to a range
            return age_formats['range'].format(ages[0], ages[1])
        elif format == 'single':  # convert to a range
            return age_formats['range'].format(ages[0], ages[0])
        else:
            return age_formats[format].format(*ages)

    else:

        return 'na'


race_eths = {
    'American Indian and Alaska Native Alone': 'aian',
    'Asian Alone': 'asian',
    'Black or African American Alone': 'black',
    'Hispanic or Latino': 'hisp',
    'Native Hawaiian and Other Pacific Islander Alone': 'nhopi',
    'White alone': 'white',
    'White Alone, Not Hispanic or Latino': 'whitenh',
    'Multiple': 'multi',
    'Some Other Race Alone': 'other',
    'Two or More Races': 'two',
    'Total Population': 'total'
}

def race(desc):

    for k, v in race_eths.items():
        if k.lower() in desc.lower() and 'not' not in desc.lower():
            return v


def classify(c):
    """Classify columns according to sex and age

    NOTE: This doesn't work right for race when the race is in the column name, such as
    b25006. Race is only meaningful with it is in the table title.
    """

    current_sex = 'na'
    current_age = 'na'

    race_eth = race(c.table.description) or 'na'

    for c1 in c.table.columns:

        if 'Female' in c1.description:
            sex = 'female'
        elif 'Male' in c1.description:
            sex = 'male'
        else:
            sex = None

        if sex:
            if sex != current_sex:
                current_sex = sex
                has_sex_class = True
                current_age = 'na'

        age = age_range(c1)

        if age != 'na':
            current_age = age

        if '+' in age:
            age_min = int(current_age[:-1])
            age_max = 200
        elif '-' in age:
            age_min, age_max = current_age.split('-')
        else:
            age_min, age_max = 0, 200

        if c1.name == c.name:
            return {
                'race_eth': race_eth,
                'age': current_age,
                'age_min': int(age_min),
                'age_max': int(age_max),
                'sex': current_sex
            }







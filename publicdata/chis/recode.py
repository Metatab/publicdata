# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Recode some variables

"""

import pandas as pd

def age_group_parts(v):
    try:
        y1, y2, _ = v.replace('-', ' ').split()
        return y1, y2
    except ValueError:
        # Probably '85+ YEARS'
        return 85, 120


def age_group_to_age(v):
    y1, y2 = age_group_parts(v)
    if y1 == 85:
        return 85
    else:
        return (int(y1) + int(y2)) / 2

# Convert to census age ranges
census_age_ranges = [
    pd.Interval(18, 24, closed='both'),
    pd.Interval(25, 34, closed='both'),
    pd.Interval(35, 44, closed='both'),
    pd.Interval(45, 54, closed='both'),
    pd.Interval(55, 64, closed='both'),
    pd.Interval(65, 74, closed='both'),
    pd.Interval(75, 85, closed='both')  # Actualy range is 75:120, but want a lower mean for prediction
]

def recode(df):
    """ Recode to a simpler group of races in variable race_recode  For a lot of health outcomes, the major divisions are
    * non-hispanic white
    * asian
    * black
    * hispanic/latino
    * other

    Also produces new variables for:

    * urminority: True of respondent is an under-represented minority; not nhwhite nor asian
    * old: Respondent is older than 45 years
    * poor: Respondent has an income of 199% of the Federal Poverty Level or below.

    """

    from pandas.api.types import CategoricalDtype

    df['race_recode'] = df.racedf_p1
    df.replace({'race_recode': {
        'NON-LATINO WHITE': 'nhwhite',
        'NON-LATINO ASIAN': 'asian',
        'NON-LATINO AMERICAN INDIAN/ALASKAN NATIVE': 'other',
        'NON-LATINO AMERICAN INDIAN/ALASKA NATIVE': 'other',
        'NON-LATINO AFR. AMER.': 'black',
        'LATINO': 'hisp',
        'NON-LATINO, TWO+ RACES': 'other',
        'NON-LATINO OTHER, ONE RACE': 'other'
    }}, inplace=True)
    df.race_recode = df.race_recode.astype('category')

    df['urminority'] = (~df['race_recode'].isin(['nhwhite','asian'])).astype(int)

    df['old'] = (df.srage_p1 < '45-49 YEARS').astype(CategoricalDtype(categories=[False, True], ordered=True))
    df.old.cat.rename_categories(['OLD', 'YOUNG'], inplace=True)

    df['poor'] = (df.povll.isin(('200-299% FPL', '300% FPL AND ABOVE'))) \
        .astype(CategoricalDtype(categories=[True, False], ordered=True))
    df.poor.cat.rename_categories(['NPOV', 'POV'], inplace=True)

    df['age_group_mean'] = df.srage_p1.apply(lambda v: age_group_to_age(v)).astype(float)
    df['age_group_min'] = df.srage_p1.apply(lambda v: age_group_parts(v)[0]).astype(int)
    df['age_group_max'] = df.srage_p1.apply(lambda v: age_group_parts(v)[1]).astype(int)

    df['census_age_group'] = pd.cut(df.age_group_mean, pd.IntervalIndex(census_age_ranges))

    return df



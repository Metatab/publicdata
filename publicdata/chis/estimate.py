# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Functions for preparing a chis dataset

"""

import pandas as pd

def select_columns(df, columns):
    """Return a subset of a dataframe, with the specified columns and all of the weights. """

    return  df[columns + [c for c in df.columns if 'raked' in c]]

def chis_estimate(df, column, ci=True, pct=True, rse=False):
    """ Calculate estimates for CHIS variables, with variances, as 95% CI,  from the replicate weights. Percentages
    are calculated with  a denominator of the sum of the estimates.

    :param df: a CHIS dataset dataframe
    :param column: Variable on which to compute estimate
    :param ci: If True, add 95% confidence intervals. If False, add standard error.
    :param pct: If true, add percentages.
    :param rse:  If true, add Relative Standard Error.
    :return:
    """

    import numpy as np

    weight_cols = [c for c in df.columns if 'raked' in c]

    t = df[[column] + weight_cols]  # Get the column of interest, and all of the raked weights
    t = t.set_index(column, append=True)  # Move the column of interest into the index
    t = t.unstack()  # Unstack the column of interest, so both values are now in multi-level columns
    t = t.sum()  # Sum all of the weights for each of the raked weight set and "YES"/"NO"
    t = t.unstack()  # Now we have sums for each of the replicats, for each of the variable values.

    est = t.iloc[0].to_frame()  # Replicate weight 0 is the estimate

    est.columns = [column]

    total = est.sum()[column]

    t = t.sub(t.loc['rakedw0']).iloc[1:]  # Subtract off the median estimate from each of the replicates
    t = (t ** 2).sum()  # sum of squares

    se = np.sqrt(t)  # sqrt to get stddev,
    ci_95 = se * 1.96  # and 1.96 to get 95% CI

    if ci:
        est[column + '_95_l'] = est[column] - ci_95
        est[column + '_95_h'] = est[column] + ci_95
    else:
        est[column + '_se'] = se

    if pct:
        est[column + '_pct'] = (est[column] / total * 100).round(1)
        if ci:
            est[column + '_pct_l'] = (est[column + '_95_l'] / total * 100).round(1)
            est[column + '_pct_h'] = (est[column + '_95_h'] / total * 100).round(1)
        est['total_pop'] = total
    if rse:
        est[column + '_rse'] = (se / est[column] * 100).round(1)

    est.rename(columns={column: column + '_count'}, inplace=True)

    return est


def chis_segment_estimate(df, column, segment_columns=None):
    """ Return aggregated CHIS data, segmented on one or more other variables.

    :param df: a CHIS dataset dataframe
    :param column:  Variable on which to compute estimate
    :param segment_columns: A string ot list of strings of column names on which to segment the results.
    :return:
    """

    import pandas as pd

    if segment_columns is None:
        # Convert the chis_estimate() result to the same format.
        t = chis_estimate(df, 'diabetes', rse=True).unstack().to_frame()
        t.columns = ['value']
        t.index.names = ['measure'] + t.index.names[1:]
        return t


    if not isinstance(segment_columns, (list, tuple)):
        segment_columns = [segment_columns]

    odf = None

    for index, row in df[segment_columns].drop_duplicates().iterrows():
        query = ' and '.join(["{} == '{}'".format(c, v) for c, v in zip(segment_columns, list(row))])

        x = chis_estimate(df.query(query), column, ci=True, pct=True, rse=True)
        x.columns.names = ['measure']
        x = x.unstack()

        for col, val in zip(segment_columns, list(row)):
            x = pd.concat([x], keys=[val], names=[col])

        if odf is None:
            odf = x
        else:
            odf = pd.concat([odf, x])

    odf = odf.to_frame()
    odf.columns = ['value']

    return odf


def concat(datasets, columns):
    """Concatenate multiple CHIS datasets, add in the weight columns, and divide the weight columns by
    the number of years of data. """

    concat_sets = [select_columns(df, columns) for df in datasets]

    df = pd.concat(concat_sets).reset_index()

    n_years = len(concat_sets)

    # Need to divide all of the weights by 2
    weight_cols = [c for c in df.columns if 'raked' in c]

    df.loc[:, weight_cols] /= n_years

    return n_years, df


def process_segments(df, target_column, target_value, segment_columns):
    """

    :param df:
    :param target_column: Column to get values for
    :param target_value: Categorical values of the target column to get values for
    :param segment_columns: Segmentation columns.
    :return:
    """
    idx = pd.IndexSlice  # Convenience redefinition.

    t = chis_segment_estimate(df, target_column, segment_columns)
    # Create a slice, with a varaible number of slices for the segment_columns
    sc_slice = (slice(None),) * len(segment_columns)

    t = t.loc[
        sc_slice + ((target_column + '_pct', target_column + '_count', target_column + '_rse'), target_value),  # rows
        idx[:]  # columns
    ]

    t = t.unstack('measure')

    # The columns are multi-level, but there is only one value for the first level,
    # so it is useless.
    t.columns = t.columns.droplevel()

    # We already selected for the single value of 'YES', so this level is useless too
    t.index = t.index.droplevel(target_column)

    return t
# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from itertools import islice
from math import ceil

import csv
import h5py
import numpy as np
import pandas as pd
from copy import copy
from pathlib import Path
from rowgenerators import Source
from rowgenerators.appurl.web import WebUrl
from functools import lru_cache

class NlsyUrl(WebUrl):
    pass


class NlsySource(Source):
    pass

class NLSY(object):

    respondent_cols = None # Columns for variables that are about the respondent, across years.
    f = None

    def __init__(self, hdf):

        self.hdf_file = hdf

        self.f = h5py.File(self.hdf_file)

        self.base_name = Path(self.hdf_file).stem

        self._metadata = None
        self._value_labels = None
        self._column_map = None
        self._question_map = None
        self._respondent_meta = None

    def __del__(self):
        self.close()

    def close(self):
        if self.f:
            self.f.close()

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self._get_dataframe(self.base_name+'_variable_labels')

        return self._metadata

    @property
    def valuelabels(self):
        if self._value_labels is None:
            self._value_labels = self._get_dataframe(self.base_name + '_value_labels')

        return self._value_labels

    def get_label_maps(self, df, var_name='question_name'):
        """Return a dict of label maps for the columns of a dataframe"""
        vl = self.valuelabels
        t = vl[vl[var_name].isin(df.columns)]

        label_maps = {}

        def maybeint(v):
            try:
                return int(v)
            except ValueError:
                return v

        g = t.groupby(var_name)
        for question_name in g.groups:
            group = g.get_group(question_name)
            label_maps[question_name] = dict(zip( [maybeint(e) for e in group.value], group.label))

        return label_maps

    @property
    def column_map(self):
        if self._column_map is None:
            # This method is much faster than building a dataframe and iterating over it

            headers = list(self.f[self.base_name + '_variable_labels_headers'])

            ds = self.f[self.base_name + '_variable_labels']

            cn = headers.index('col_no')

            d = {k: v for v, k in ds[:, [cn, headers.index('variable_name')]]}
            d.update({k: v for v, k in ds[:, [cn, headers.index('variable_name_nd')]]})
            d.update({k: v for v, k in ds[:, [cn, headers.index('question_name')]]})

            self._column_map = d

        return self._column_map

    @property
    def question_map(self):
        if self._question_map is None:
            # This method is much faster than building a dataframe and iterating over it

            headers = list(self.f[self.base_name + '_variable_labels_headers'])

            ds = self.f[self.base_name + '_variable_labels']

            cn = headers.index('col_no')

            self._question_map = dict(ds[:, [headers.index('variable_name_nd'),
                                             headers.index('question_name')]])

        return self._question_map

    def columns_meta(self, columns):
        """Get a dataframe with the dimention numbers and survey year for the
        given columns"""
        q_meta = self.metadata[self.metadata.variable_name_nd.isin(columns)]

        df =  q_meta[['variable_name_nd', 'survey_year', 'dim1', 'dim2', 'dim3',
                         'component', 'response_choice']] \
            .replace('nan', np.nan) \
            .dropna(axis=1, how='all')

        try:
            df['survey_year'] = df.survey_year.astype(int)
        except:
            # Not for "XRND", etc
            pass

        return df

    @property
    def respondent_meta(self):
        """Get a dataframe of data about all respondents. """
        if self._respondent_meta is None:
            self._respondent_meta = self.get_dataframe(self.respondent_cols)
            self._respondent_meta.columns = [self.question_map[c] for c in self._respondent_meta.columns]

        return self._respondent_meta.copy()

    @lru_cache()
    def _get_dataframe(self, name, col_nos=None):
        ds = self.f[name]
        headers = self.f[name + '_headers']

        if col_nos:
            # col_nos must be a list! a tuple will index differently
            return pd.DataFrame(ds[:, list(col_nos)], columns=list(headers[list(col_nos)]))
        else:
            return pd.DataFrame(ds[:], columns=list(headers[:]))

    def get_dataframe(self, col_nos=None ):
        """Return a dataframe, with headers from the NLSY HDF5 file"""
        import h5py
        import pandas

        if col_nos is None:
            return self._get_dataframe(self.base_name, col_nos=None)
        else:
            def mapcolno(n):
                try:
                    return int(n)
                except ValueError:
                    return self.column_map.get(n, n)

            col_nos = sorted([int(mapcolno(n)) for n in col_nos])

            return self._get_dataframe(self.base_name, col_nos=tuple(col_nos))

    def base_question_columns(self,base_qn):

        m = self.metadata
        return list(m[m.base_qn == base_qn].variable_name_nd)

    def question_dataframe(self, base_qn, rmeta=True, cmeta=True):
        """
        Return a dataframe with all columns for a base question, linked to the column metadata
        and some respondent data. The dataframe will be pivoted so there is a single

        :param base_qn:
        :param rmeta:
        :param cmeta:
        :return:
        """

        if rmeta is True:
            rmeta = self.respondent_cols
        elif rmeta is False:
            rmeta = self.min_respondent_cols

        cols = self.base_question_columns(base_qn)

        if not cols:
            return None

        df = self[cols]

        respondent_meta = self.respondent_meta
        assert len(respondent_meta) == len(df)

        t = respondent_meta[rmeta].join(df).melt(id_vars=rmeta, var_name='variable_name_nd', value_name=base_qn)

        if cmeta:
            columns_meta = self.columns_meta(df.columns)
            t = t.merge(columns_meta, on="variable_name_nd")

            col_order = list(t.columns)
            col_order.remove(base_qn)
            col_order += [base_qn]

            t = t[col_order]

        return t.drop(columns=["variable_name_nd"])

    def categoricalize(self,df):
        """Convert all of the categorical columns.
        The columns must have question names, not variable names. """
        lm = self.get_label_maps(df)

        for c in df:
            if c in lm:
                df[c] = df[c].astype('category').cat.rename_categories({int(k): v for k, v in lm[c].items()})
            pass

        return df


    def __getitem__(self, item):

        if not isinstance(item,(list,tuple)):
            return self.get_dataframe([item])
        else:
            return self.get_dataframe(list(item))



class NLSY97(NLSY):
    # Variables that only appear in one year.

    # For weighting, see
    # https://www.nlsinfo.org/content/cohorts/nlsy97/using-and-understanding-the-data/sample-weights-design-effects

    sampling_weight = 'SAMPLING_WEIGHT_CC'
    panel_weight = 'SAMPLING_PANEL_WEIGHT'

    respondent_cols =['PUBID','KEY!SEX','KEY!BDATE_Y', 'KEY!RACE','KEY!ETHNICITY','KEY!RACE_ETHNICITY']
    min_respondent_cols = ['PUBID']

class NLSY79(NLSY):
    # Variables that only appear in one year, maybe?
    respondent_cols = ['SAMPLE_ID','SAMPLE_RACE','SAMPLE_SEX','SHIFTSP_86A','VERSION_R26']

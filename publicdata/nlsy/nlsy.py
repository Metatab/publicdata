# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from functools import lru_cache
from functools import reduce
from pathlib import Path
from warnings import warn

import h5py
import numpy as np
import pandas as pd
from rowgenerators import Source
from rowgenerators.appurl.web import WebUrl


class NlsyUrl(WebUrl):
    pass


class NlsySource(Source):
    pass


class NLSY(object):
    respondent_cols = None  # Columns for variables that are about the respondent, across years.
    f = None

    na_labels = {
        '-1': 'NA',
        '-2': 'NA',
        '-3': 'NA',
        '-4': 'NA',
        '-5': 'NA'

    }

    def __init__(self, hdf):

        self.hdf_file = Path(hdf)

        if self.hdf_file.is_dir():
            # Assume it is an archive directory, properly named
            self.hdf_file = self.hdf_file.joinpath(self.hdf_file.name + '.h5')

        self.f = h5py.File(self.hdf_file, 'r')

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
            self._metadata = self._get_dataframe(self.base_name + '_variable_labels')

            # Fix brokenness
            #  https://github.com/Metatab/publicdata/issues/7
            for col in ['var_no', 'col_no', 'labels_id', 'is_categorical']:
                self._metadata[col].replace('nan', np.nan, inplace=True)
                self._metadata[col] = pd.to_numeric(self._metadata[col])

            self._metadata.replace(['nan'], [None], inplace=True)

            self._metadata.at[1, 'is_categorical'] = 1

        return self._metadata

    @property
    def valuelabels(self):
        if self._value_labels is None:
            self._value_labels = self._get_dataframe(self.base_name + '_value_labels')

            self._value_labels['value'] = pd.to_numeric(self._value_labels['value'])

            self._value_labels.dropna(inplace=True)

            self._value_labels['value'] = self._value_labels['value'].astype('int')

        return self._value_labels

    def _get_label_maps(self, df, var_name):
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

            lm = dict(zip([maybeint(e) for e in group.value], group.label))

            # lm.update(self.na_labels)

            label_maps[question_name] = lm

        return label_maps

    def get_label_maps(self, df):

        vl1 = self._get_label_maps(df, 'question_name')
        vl2 = self._get_label_maps(df, 'base_name')

        vl1.update(vl2)

        return vl1

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
        """Get a dataframe with the dimension numbers and survey year for the
        given columns"""
        q_meta = self.metadata[self.metadata.variable_name_nd.isin(columns)]

        df = q_meta[['variable_name_nd', 'survey_year', 'dim1', 'dim2', 'dim3',
                     'component', 'response_choice']] \
            .replace('nan', np.nan)  # \
        # .dropna(axis=1, how='all') # drops columns with no values

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

        df = self._respondent_meta.copy()

        return df

    @lru_cache()
    def _get_dataframe(self, name, col_nos=None):
        ds = self.f[name]
        headers = self.f[name + '_headers']

        if col_nos:
            # col_nos must be a list! a tuple will index differently
            return pd.DataFrame(ds[:, list(col_nos)], columns=list(headers[list(col_nos)]))
        else:
            return pd.DataFrame(ds[:], columns=list(headers[:]))

    def get_dataframe(self, col_nos=None):
        """Return a dataframe, with headers from the NLSY HDF5 file"""

        if col_nos is None:
            return self._get_dataframe(self.base_name, col_nos=None)
        else:
            def mapcolno(n):
                try:
                    return int(n)
                except ValueError:
                    return self.column_map.get(n)

            col_nos = sorted([int(mapcolno(n)) for n in col_nos if mapcolno(n)])

            return self._get_dataframe(self.base_name, col_nos=tuple(col_nos))

    def base_question_columns(self, base_qn):

        m = self.metadata

        return list(m[m.base_qn == base_qn].variable_name_nd)

    def _question_dataframe(self, base_qn, rmeta=True, cmeta=True, replacena=False, agg=None):
        """
        Return a dataframe with all columns for a base question, linked to the column metadata
        and some respondent data. The dataframe will be pivoted so there is a single

        :param replacena:
        :return:
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

        # Maybe didn't get all of the respondent meta columns, so reset to the ones we have
        rmeta =[ c for c in self.respondent_meta.columns if c in rmeta]

        assert len(respondent_meta) == len(df)

        t = respondent_meta[rmeta].join(df).melt(id_vars=rmeta, var_name='variable_name_nd', value_name=base_qn)

        if cmeta:
            columns_meta = self.columns_meta(df.columns)
            t = t.merge(columns_meta, on="variable_name_nd")

            col_order = list(t.columns)
            # Move the observation column to the end
            col_order.remove(base_qn)
            col_order += [base_qn]

            t = t[col_order]

        t = t.drop(columns=["variable_name_nd"])

        # The N/A Values are all less than or equal to 0, so we can replace all of them
        # with NaN
        if replacena:
            t[base_qn] = t[base_qn].where(t[base_qn] >= 0, np.nan)

        if agg:
            t = t.groupby(['PUBID', 'survey_year']).agg(agg)[base_qn].to_frame().reset_index()

        t.drop(columns=['component', 'response_choice'], errors='ignore', inplace=True)

        # Fix some odd issues with the dimensions getting the wrong type
        for dc in ['dim1', 'dim2', 'dim3']:
            if dc in t.columns:
                t[dc] = pd.to_numeric(t[dc], errors='coerce')

        # Survey year can be a string, so make it always a string
        if 'survey_year' in t.columns:
            t['survey_year'] = t['survey_year'].astype(str)

        return t

    def question_dataframe(self, base_qn=None, rmeta=True, cmeta=True, replacena=True, dropna=True, agg=None):
        """
        :param base_qn:  Base question, either a single string, or a list of string question names. If None, use all questions
        :param rmeta: If True, link in respondent metadata. Defaults to True
        :param cmeta: If True, link in column metadata. Defaults to True
        :param replacena: If true, replace negative values with Nan. Defaults to True
        :param dropna: If true, drop columns that are all null. Defaults to True
        :param agg: If set, group the dataframe on PUBID and survey year, and apply this aggregation function
        :return:


        The `agg` parameter is important for questions that  have multiples dimensions, such as YSCH-20500.01.02,
        which has two extra dimensions, for college # ( '01' ) and term #, ('02'). Question dataframes with
        dimensions cannot be merged with question dataframes with a different set of dimensions.

        There are 5  dimensions that the aggregation function may have to consider.

        * dim1
        * dim2
        * dim3
        * component
        * response_choice

        For example, for the question name: 'YSCH-23900.01.02.03~000004' The dimensions are

        * dim: 1
        * dim2: 2
        * dim3: 3
        * component 4
        * response_choice "1. Your biological parents together"

        The first four are parts of the name, the response choice is defined in the codebook for the heading "RESPONSE
        CHOICE" and should be linked to the component. The is, when both the comonent and response choice are
        defined, the component is a number that identifies the response choice.

        """

        if base_qn is None:
            base_qn = list(e for e in self.metadata.base_qn.unique() if e != 'PUBID')

        if isinstance(base_qn, (list, tuple)):

            # Uniquify
            _base_qn, base_qn = base_qn, []
            for e in _base_qn:
                if e not in base_qn:
                    base_qn.append(e)

            def get_agg(base_qn):

                try:
                    return agg.get(base_qn)
                except AttributeError:
                    return agg

            frames = [self._question_dataframe(e.strip(), False, True,
                                               replacena=replacena, agg=get_agg(e.strip()))
                      for e in base_qn]

            index_cols = list(reduce(lambda x, y: x | set(y.columns[:-1]), frames, set()))

            # reorder to the standard order
            index_cols = [e for e in self.all_dims if e in index_cols]

            df = frames[0].set_index(index_cols)

            for i, e in enumerate(frames[1:], 1):

                try:
                    e.set_index(index_cols, inplace=True)

                    df = df.join(e, how='outer')
                except ValueError as exc:

                    warn(('Failed to join question data frames, '
                          "probably because some have extra dimensions and others don't: {}\n"
                          "For question {}\n{}")
                         .format(exc, base_qn[i], e.head(3)))
                except TypeError as exc:
                    # This case is for debugging instances of a column having mixed types.
                    raise

                    for c in df.reset_index().columns:
                        print(c, set(type(e) for e in df.reset_index()[c]))
                    print('----')
                    for c in e.reset_index().columns:
                        print(c, set(type(e) for e in e.reset_index()[c]))


            if rmeta:
                # Avoid overlapping columns if some of the rmeta columns are included
                # among the requested questions
                rm_cols = self.respondent_meta.columns
                df_cols = [c for c in df.columns if c not in rm_cols]

                df = df[df_cols].join(self.respondent_meta.set_index('PUBID'))

        else:
            df = self._question_dataframe(base_qn.strip(), rmeta, cmeta, replacena, agg)

        if dropna:
            return df.reset_index().dropna(axis=1, how='all')  # drops columns with no values
        else:
            return df.reset_index()

    def categoricalize(self, df, columns=None):
        """Convert all of the categorical columns.
        The columns must have question names, not variable names. """
        lm = self.get_label_maps(df)

        if isinstance(columns, str):
            columns = [columns]

        for c in df:

            if columns and c not in columns:
                continue

            if c in lm:
                df[c] = df[c].astype('category').cat.rename_categories({int(k): v for k, v in lm[c].items()})

            pass

        return df

    def dummify(self, df):
        pass

    def __getitem__(self, item):

        if not isinstance(item, (list, tuple)):
            return self.get_dataframe([item])
        else:
            return self.get_dataframe(list(item))

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


class NLSY97(NLSY):
    # Variables that only appear in one year.

    # For weighting, see
    # https://www.nlsinfo.org/content/cohorts/nlsy97/using-and-understanding-the-data/sample-weights-design-effects

    sampling_weight = 'SAMPLING_WEIGHT_CC'
    panel_weight = 'SAMPLING_PANEL_WEIGHT'

    all_dims = ['PUBID', 'survey_year', 'dim1', 'dim2', 'dim3', 'component', 'response_choice']

    respondent_cols = ['PUBID', 'KEY!SEX', 'KEY!BDATE_Y', 'KEY!RACE', 'KEY!ETHNICITY', 'KEY!RACE_ETHNICITY']
    min_respondent_cols = ['PUBID']


class NLSY79(NLSY):
    # Variables that only appear in one year, maybe?
    respondent_cols = ['SAMPLE_ID', 'SAMPLE_RACE', 'SAMPLE_SEX', 'SHIFTSP_86A', 'VERSION_R26']

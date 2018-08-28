# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""

"""

import six
import pandas as pd
import numpy as np
from publicdata.exc import PublicDataException

class CensusDataFrame(pd.DataFrame):
    _metadata = ['title_map', 'release', '_dataframe', '_url', 'table']  # Release is the Census Reporter release metadata

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False, schema=None,
                 table=None, url=None):

        if columns is None and schema is not None:
            self.title_map = {s['code']: s['code_title'] for s in schema}
            columns = self.title_map.keys()
        else:
            self.title_map = {}

        self._url = url

        self.table = table

        super(CensusDataFrame, self).__init__(data, index, columns, dtype, copy)

        for c in self.columns:
            self[c].title = self.title_map.get(c, c)

    @property
    def _constructor(self):
        return CensusDataFrame

    @property
    def _constructor_sliced(self):
        from .series import CensusSeries
        return CensusSeries

    @property
    def titles(self):
        """Return a copy that uses titles for column headings"""

        return self.rename(index=str,
                           columns=self.title_map,
                           inplace=False)

    def search_columns(self, *args):
        """Return full titles for columns that contain one of the strings in the arguments

        :param *args: String arguments, or compiled regular expressions


        """

        import re

        def _f():
            for a in args:
                for k, v in self.title_map.items():
                    if a.search(v) if isinstance(a, re._pattern_type) else  a in str(v):
                        yield (k, v)

        return pd.DataFrame(data=list(_f()), columns='code title'.split())

    def _col_name_match(self, c, key):

        return (key == str(c['name']) or str(key).lower() == str(c['name']).lower() or
                key == c['code'] or key == str(c['code']).lower() or
                key == c['title'].lower() or
                key == str(c['index']).lower() or key == str(c['position']))

    def _default_schema_entry(self, pos, c):
        """ Return a schema entry for columns that aren't ACS table columns

        :param pos: Position of the column
        :param c: Column name
        :return:
        """

        return {
            'name': c,
            'title': c,
            'code': c,
            'code_title': c,
            'indent': 0,
            'index': None,
            'position': pos
        }

    @property
    def rows(self):
        """Yield rows like a partition does, with a header first, then rows. """

        yield [self.index.name] + list(self.columns)

        for t in self.itertuples():
            yield list(t)

    @property
    def geo(self):
        """Return a geopandas dataframe with boundaries for the area"""
        from publicdata.census.censusreporter.url import CensusReporterURL
        from rowgenerators import get_generator
        from itertools import islice
        from metapack.jupyter.pandas import  MetatabDataFrame

        if isinstance(self._url, CensusReporterURL):
            geo_url = self._url.geo

            r = geo_url.get_resource()
            t = r.get_target()

            g = get_generator(t)

            headers = next(islice(g, 0, 1))
            data = islice(g, 1, None)

            df = MetatabDataFrame(list(data), columns=headers, metatab_resource=self)

            return df.geo

        else:
            raise PublicDataException("Dataframe doesn't have a CensusReporterURL, so can't find geo source")


    def sum_m(self, *cols):
        """Sum a set of Dataframe series and return the summed series and margin. The series must have names"""

        # See the ACS General Handbook, Appendix A, "Calculating Margins of Error for Derived Estimates".
        # (https://www.census.gov/content/dam/Census/library/publications/2008/acs/ACSGeneralHandbook.pdf)
        # for a guide to these calculations.

        if len(cols) == 1 and isinstance(cols[0], (list, tuple)):
            cols = cols[0]

        cols = [self[c] for c in cols]

        estimates = sum(cols)

        margins = np.sqrt(sum(c.m90 ** 2 for c in cols))

        return estimates, margins

    def add_sum_m(self, col_name, *cols):
        """
        Add new columns for the sum, plus error margins, for 2 or more other columns

        The routine will add two new columns, one named for col_name, and one for <col_name>_m90

        :param col_name: The base name of the new column
        :param cols:
        :return:
        """

        self[col_name], self[col_name + '_m90'] = self.sum_m(*cols)

        return self

    def add_rse(self, *col_name):
        """
        Create a new column, <col_name>_rse for Relative Standard Error, using <col_name> and <col_name>_m90

        :param col_name:
        :return:

        """

        for cn in col_name:
            self[cn + '_rse'] = self[cn].rse

        return self

    def sum_col_range(self, first, last):
        """Sum a contiguous group of columns, and return the sum and the new margins.  """

        c1 = self[first]
        c2 = self[last]

        cols = self.ix[:, c1.col_position:c2.col_position + 1]

        estimates = sum(cols)

        margins = np.sqrt(np.sum(c.m90 ** 2 for c in cols))

        return estimates, margins

    def ratio(self, n, d):
        """
        Calculate a ratio. The numerator should not be a subset of the denominator,
        such as the ratio of males to females. If it is  a subset, use proportion().

        :param n: The Numerator, a string, CensusSeries or tuple
        :param d: The Denominator, a string, CensusSeries or tuple
        :return: a tuple of series, the estimates and the margins
        """

        return self._ratio(n, d, subset=False)

    def proportion(self, n, d):
        """
        Calculate a proportion. The numerator should be a subset of the denominator,  such
        as the proportion of females to the total population. If it is not a subset, use ratio().

        ( I think "subset" mostly means that the numerator < denominator )

        :param n: The Numerator, a string, CensusSeries or tuple
        :param d: The Denominator, a string, CensusSeries or tuple
        :return: a tuple of series, the estimates and the margins
        """

        return self._ratio(n, d, subset=True)

    def normalize(self, x):
        """Convert any of the numerator and denominator forms into a consistent
        tuple form"""

        from .series import CensusSeries

        if isinstance(x, tuple):
            return self[x[0]], self[x[1]]

        elif isinstance(x, six.string_types):
            return self[x], self[x].m90

        elif isinstance(x, CensusSeries):
            return x.value, x.m90

        else:
            raise ValueError("Don't know what to do with a {}".format(type(x)))

    def _ratio(self, n, d, subset=True):
        """
        Compute a ratio of a numerator and denominator, propagating errors

        Both arguments may be one of:
        * A CensusSeries for the estimate
        * a string that can be resolved to a colum with .lookup()
        * A tuple of names that resolve with .lookup()

        In the tuple form, the first entry is the estimate and the second is the 90% margin

        :param n: The Numerator, a string, CensusSeries or tuple
        :param d: The Denominator, a string, CensusSeries or tuple
        :return: a tuple of series, the estimates and the margins
        """

        n, n_m90 = self.normalize(n)
        d, d_m90 = self.normalize(d)

        rate = n.astype(float) / d.astype(float)

        if subset:
            try:
                # From external_documentation.acs_handbook, Appendix A, "Calculating MOEs for
                # Derived Proportions". This is for the case when the numerator is a subset of the
                # denominator

                # In the case of a neg arg to a square root, the acs_handbook recommends using the
                # method for "Calculating MOEs for Derived Ratios", where the numerator
                # is not a subset of the denominator. Since our numerator is a subset, the
                # handbook says " use the formula for derived ratios in the next section which
                # will provide a conservative estimate of the MOE."
                # The handbook says this case should be rare, but for this calculation, it
                # happens about 50% of the time.

                # Normal calc, from the handbook
                sqr = n_m90 ** 2 - ((rate ** 2) * (d_m90 ** 2))

                # When the sqr value is <= 0, the sqrt will fail, so use the other calc in those cases
                sqrn = sqr.where(sqr > 0, n_m90 ** 2 + ((rate ** 2) * (d_m90 ** 2)))

                # Aw, hell, just punt.
                sqrnz = sqrn.where(sqrn > 0, float('nan'))

                rate_m = np.sqrt(sqrnz) / d

            except ValueError:

                return self._ratio(n, d, False)


        else:
            rate_m = np.sqrt(n_m90 ** 2 + ((rate ** 2) * (d_m90 ** 2))) / d

        return rate, rate_m

    def product(self, a, b):

        a, a_m90 = self.normalize(a)
        b, b_m90 = self.normalize(b)

        p = a * b

        margin = np.sqrt(a ** 2 * b_m90 ** 2 + b ** 2 * a_m90 ** 2)

        return p, margin

    def dim_columns(self, pred):
        """
        Return a list of columns that have a particular value for age,
        sex and race_eth. The `pred` parameter is a string of python
        code which is evaled, with the classification dict as the local
        variable context, so the code string can access these variables:

        - sex
        - age
        - race-eth
        - col_num

        Col_num is the number in the last three digits of the column name

        Some examples of predicate strings:

        - "sex == 'male' and age != 'na' "

        :param pred: A string of python code that is executed to find column matches.

        """

        from .dimensions import classify

        out_cols = []

        for i, c in enumerate(self.partition.table.columns):
            if c.name.endswith('_m90'):
                continue

            if i < 9:
                continue

            cf = classify(c)
            cf['col_num'] = int(c.name[-3:])

            if eval(pred, {}, cf):
                out_cols.append(c.name)

        return out_cols

    def __getitem__(self, key):
        """

        """
        from pandas import DataFrame, Series
        from .series import CensusSeries

        result = super(CensusDataFrame, self).__getitem__(key)

        if isinstance(result, DataFrame):
            result.__class__ = CensusDataFrame
            result._dataframe = self

        elif isinstance(result, Series):
            result.__class__ = CensusSeries
            result._dataframe = self

        return result

    def copy(self, deep=True):

        r = super(CensusDataFrame, self).copy(deep)
        r.__class__ = CensusDataFrame
        r.title_map = self.title_map

        return r

    def set_index(self, keys, drop=True, append=False, inplace=False, verify_integrity=False):

        r = super().set_index(keys, drop, append, inplace, verify_integrity)
        r = self if inplace else r

        return r

    def groupby(self, by=None, axis=0, level=None, as_index=True, sort=True,
                group_keys=True, squeeze=False, **kwargs):
        """
        Overrides groupby() to return CensusDataFrameGroupBy

        """
        from .groupby import groupby

        if level is None and by is None:
            raise TypeError("You have to supply one of 'by' and 'level'")

        axis = self._get_axis_number(axis)

        return groupby(self, by=by, axis=axis, level=level, as_index=as_index,
                       sort=sort, group_keys=group_keys, squeeze=squeeze,
                       **kwargs)

    ##
    ## Extension Points
    ##

    @property
    def _constructor(self):
        return CensusDataFrame

    @property
    def _constructor_sliced(self):
        from .series import CensusSeries
        return CensusSeries

    def _getitem_column(self, key):
        """ Return a column from a name

        :param key:
        :return:
        """

        c = super(CensusDataFrame, self)._getitem_column(key)
        c.parent_frame = self
        c.title = self.title_map.get(key, key)

        return c

    def _getitem_array(self, key):
        """Return a set of columns. The keys can be any of the names for the column, the
        method automatically adds _m90 columns"""

        if isinstance(key, list):

            # augmented_key is the original list of columns with the _m90 columns added
            augmented_key = []

            for col_name in key:
                augmented_key.append(col_name)

                try:
                    self[col_name + '_m90']
                    augmented_key.append(col_name + '_m90')
                except KeyError:
                    pass

            df = super()._getitem_array(augmented_key)
        else:
            df = super()._getitem_array(key)

        assert id(df) != id(self)

        return df

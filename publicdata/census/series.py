# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""

"""

from pandas import Series
import numpy as np


class CensusSeries(Series):

    _metadata = ['schema', 'parent_frame']

    @property
    def _constructor(self):
        return CensusSeries

    @property
    def _constructor_expanddim(self):
        from publicdata.census.dataframe import CensusDataFrame
        return CensusDataFrame

    @property
    def title(self):  # b/c the _metadata elements aren't created until assigned
        try:
            return self._title
        except AttributeError:
            return None

    @title.setter
    def title(self, v):
        self._title = v

    @property
    def census_code(self):
        return self.name

    @property
    def census_index(self):
        raise NotImplementedError

    @property
    def census_title(self):
        return self.title

    @property
    def col_position(self):
        raise NotImplementedError


    def __init__(self, data=None, index=None, dtype=None, name=None, copy=False, fastpath=False):
        super(CensusSeries, self).__init__(data, index, dtype, name, copy, fastpath)


    @property
    def m90(self):
        if self.census_code.endswith('_m90'):
            return self
        else:
            return self.parent_frame[self.census_code+'_m90'].astype('float')

    @property
    def estimate(self):
        """Return the estimate value, for either an estimate column or a margin column. """
        if self.census_code.endswith('_m90'):
            return self.parent_frame[self.census_code.replace('_m90','')].astype('float')
        else:
            return self

    @property
    def value(self):
        """Synonym for estimate()"""
        if self.census_code.endswith('_m90'):
            return self.parent_frame[self.census_code.replace('_m90','')].astype('float')
        else:
            return self

    @property
    def se(self):
        """Return a standard error series, computed from the 90% margins"""
        return self.m90 / 1.645

    @property
    def rse(self):
        """Return the relative standard error for a column"""

        return ( (self.se / self.value) * 100).replace([np.inf, -np.inf], np.nan)

    @property
    def m95(self):
        """Return a standard error series, computed from the 90% margins"""
        return self.se * 1.96

    @property
    def m99(self):
        """Return a standard error series, computed from the 90% margins"""
        return self.se * 2.575

    def sum_m90(self, *cols):
        """"""

        # See the ACS General Handbook, Appendix A, "Calculating Margins of Error for Derived Estimates".
        # (https://www.census.gov/content/dam/Census/library/publications/2008/acs/ACSGeneralHandbook.pdf)
        # for a guide to these calculations.

        return np.sqrt(sum(self.m90 ** 2))


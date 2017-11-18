import numpy as np
from pandas.core.groupby import SeriesGroupBy, DataFrameGroupBy

from .dataframe import CensusDataFrame
from .series import CensusSeries


def groupby(obj, by, **kwds):
    if isinstance(obj, CensusSeries):
        klass = CensusSeriesGroupBy
    elif isinstance(obj, CensusDataFrame):
        klass = CensusDataFrameGroupBy
    else:  # pragma: no cover
        raise TypeError('invalid type: %s' % type(obj))

    return klass(obj, by, **kwds)


class CensusSeriesGroupBy(SeriesGroupBy):

    def sum_rs(self, x):
        """root of the sum of the squares"""

        # See the ACS General Handbook, Appendix A, "Calculating Margins of Error for Derived Estimates".
        # (https://www.census.gov/content/dam/Census/library/publications/2008/acs/ACSGeneralHandbook.pdf)
        # for a guide to these calculations.

        return np.sqrt(sum(self.m90 ** 2))


class CensusDataFrameGroupBy(DataFrameGroupBy):


    def sum_m(self):
        """root of the sum of the squares"""

        # See the ACS General Handbook, Appendix A, "Calculating Margins of Error for Derived Estimates".
        # (https://www.census.gov/content/dam/Census/library/publications/2008/acs/ACSGeneralHandbook.pdf)
        # for a guide to these calculations.

        return np.sqrt(sum(self.m90 ** 2))

    def aggregate(self, arg, *args, **kwargs):

        return super().aggregate(arg, *args, **kwargs)

    agg = aggregate


    def _m_agg(self, f1, f2):

        cf = {}

        if not isinstance(self.keys, (list, tuple)):
            keys = [self.keys]
        else:
            keys = self.keys

        for c in list(self.obj.columns):

            if c in keys:
                continue

            if self.obj[c].dtype == object:
                continue # Skip strings?

            if c.endswith('_m90'):
                cf[c] = [f2]
            else:
                cf[c] = [f1]


        return self.agg(cf)


    def sum(self):
        from publicdata.censusreporter.func import sum_rs

        return self._m_agg('sum',sum_rs)

    def mean(self):
        from publicdata.censusreporter.func import mean_m

        return self._m_agg('mean', mean_m)

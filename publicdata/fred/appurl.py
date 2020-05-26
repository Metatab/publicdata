# Copyright (c) 2020 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

from rowgenerators import Url
from fredapi import Fred
from os import environ
from rowgenerators.exceptions import MissingCredentials
import pandas as pd
from rowgenerators.appurl.file.csv import CsvFileUrl
from pathlib import Path
from rowgenerators.util import slugify

class FredUrl(Url):
    """

    FRED Url. Federal Reserve Data from St Louis FED

    Url forms:

        fred:series/start-date/end-date
        fred:series/start-date
        fred:series

    The Parser will also accept a '//:

        fred://series/start-date/end-date


    This URL requires an API key, which can be obtained from the FRED website
    . The key must be set in the environmental variable FRED_API_KEY

    """
    match_priority = 20

    def __init__(self, url=None, downloader=None, **kwargs):

        self._proto = 'fred'

        super().__init__(url, downloader, **kwargs)

        parts = [ e for e in [self.netloc]+self.path.split('/') if e]

        self.series = parts.pop(0)

        # Get rid of space and empty elements
        if ',' in self.series:
            self.series = [ e.strip() for e in self.series.split(',') if e]
        else:
            self.series = [self.series]

        try:
            self.start_date = parts.pop(0)
        except IndexError:
            self.start_date = None

        try:
            self.end_date = parts.pop(0)
        except IndexError:
            self.end_date = None


        try:
            self.token = environ['FRED_API_KEY']
        except KeyError:
            raise MissingCredentials("Missing credentials. Define env var FRED_API_KEY")

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme == 'fred'

    def cache_path(self, series):
        from datetime import datetime

        sd = self.start_date or 'START'
        ed = self.end_date or datetime.now().date().isoformat()

        if isinstance(series, list):
            s = ','.join(series)
        else:
            s = series

        return f"fred/{s}/{sd}-{ed}"


    def _fetch_series(self, series):
        """Fecth, and cache, individual series"""


        fred = Fred()
        params = {}

        # Cache just the individual series. Includes the full paths
        # because the series can have different date ranges


        cp = Path(self.downloader.cache.getsyspath(f"{self.cache_path(series)}.csv"))
        cp.parent.mkdir(parents=True, exist_ok=True)

        if not cp.exists():

            if self.start_date:
                params['observation_start'] = self.start_date

            if self.start_date:
                params['observation_end'] = self.end_date

            s = fred.get_series(series, **params)

            df = s.to_frame(name=series)
            df.index.set_names('date', inplace=True)
            df.to_csv(cp)

        return cp

    def get_series(self):
        """Get all of the series for the cached series. """
        from functools import reduce

        return [ pd.read_csv(self._fetch_series(s)).set_index('date') for s in self.series]

    def get_resource(self):
        from functools import reduce

        # Combines the series with an outer join on the dates

        def merge(a, b):
            return a.join(b, how='outer')

        df = reduce(merge, self.get_series())

        cp = Path(self.downloader.cache.getsyspath(f"{self.cache_path(self.series)}.csv"))
        cp.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(cp)

        return CsvFileUrl(cp, downloader=self.downloader)

    def get_target(self):
        return self.get_resource().get_target()

    def dataframe(self, *args, **kwargs):
        """Return a Pandas dataframe with the data for this table"""
        return self.get_target().generator.dataframe(*args, **kwargs)


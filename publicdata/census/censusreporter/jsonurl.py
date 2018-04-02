
# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from rowgenerators.appurl.file import FileUrl


class CensusReporterJsonUrl(FileUrl):
    """Url for the JSON file downloaded by CensusReporterUrl"""

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

        # HACK This hsould be handled properly in parse_app_url
        self._fragment = kwargs.get('_fragment')
        self.scheme_extension = 'CRJSON'

    def get_resource(self):
        return self

    def get_target(self):
        return self
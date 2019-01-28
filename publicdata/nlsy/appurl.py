# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Application URLS and generators for NLSY urls
"""


from rowgenerators import Url
from rowgenerators.exceptions import AppUrlError
from rowgenerators.appurl.file import Hdf5Url

class NlsyUrl(Url):
    """A URL for the National Longitudinal Survey of Youth

    General form:

        nlsy+file:/path/to/nlsy97_all_1997-2013.h5#question_name

    The referenced file must be an HDF5 file created by the conversion programs.
    See: https://github.com/Metatab/publicdata/blob/master/publicdata/docs/Nlsy.rst for details

    The generator object for the URL is also an NLSY object.


    """

    match_priority = Hdf5Url.match_priority - 1

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(url, downloader, **kwargs)

    def get_resource(self):
        return self.inner.get_resource()

    @classmethod
    def _match(cls, url, **kwargs):
        return url.proto == 'nlsy'

    @property
    def nlsy(self):
        """Return an NLSY object"""
        from .nlsy import NLSY79, NLSY97


        path = str(self.get_resource().get_target().fspath)

        if '97' in path:
            return NLSY97(path)
        elif '79' in path:
            return NLSY79(path)
        else:
            raise AppUrlError("Can't determine NLSY object type from paths. "
                              "Must have '97' or '79' in path: "+str(path))


from rowgenerators import Url
from rowgenerators.exceptions import AppUrlError
from publicdata.census.util import sub_geoids, sub_summarylevel
from warnings import warn

class StataUrl(Url):
    """
    """
    match_priority = 20

    def __init__(self, url=None, downloader=None, **kwargs):
        super().__init__(str(u), downloader=downloader, **kwargs)

        self.scheme_extension = 'stata'

        





from rowgenerators import Url
from rowgenerators.exceptions import AppUrlError
from publicdata.census.util import sub_geoids, sub_summarylevel

class CensusUrl(Url):
    """A URL for censusreporter tables.

    General form:

        census:<table_id>/<summary_level>/<geoid>

    <geoid> is the geoid of the containing area. For Census Reporter URLs, this can be almost
    any containing area, but other URL types may respect only limits on the state or state and county.

    For instance:

        census:B17001/140/05000US06073

    Geoids For the US and states, the geoid may be 'US' or the two character state abbreviation.

    """
    match_priority = 20

    @property
    def _parts(self):
        if not self.netloc:
            # If the URL didn't have ://, there is no netloc
            parts =  self.path.strip('/').split('/')
        else:
            parts = tuple( [self.netloc] + self.path.strip('/').split('/'))

        if len(parts) != 3:
            raise AppUrlError("Census reporters must have three path components. Got: '{}' ".format(parts))

        return parts




    @property
    def table_id(self):
        return self._parts[0]

    @property
    def summary_level(self):
       return self._parts[1]

    @property
    def geoid(self):
        return sub_geoids(self._parts[2])

    def join(self, s):
        raise NotImplementedError()

    def join_dir(self, s):
        raise NotImplementedError()

    def join_target(self, tf):
        raise NotImplementedError()

    def get_resource(self):
        return self

    def get_target(self):
        return self




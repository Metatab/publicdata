from rowgenerators import Url
from rowgenerators.exceptions import AppUrlError
from publicdata.census.util import sub_geoids, sub_summarylevel
from warnings import warn
from .exceptions import CensusParsingException

class CensusUrl(Url):
    """A URL for censusreporter tables.

    General form:

        census:<table_id>/<summary_level>/<geoid>

    <geoid> is the geoid of the containing area. For Census Reporter URLs, this can be almost
    any containing area, but other URL types may respect only limits on the state or state and county.

    For instance:

        census:/05000US06073/140/B17001

        census://<year>/<release/<geoid>/<summarylevel>/<table>
        census://<geoid>/<summarylevel>/<table>


    Geoids For the US and states, the geoid may be 'US' or the two character state abbreviation.

    """
    match_priority = 20

    default_year = 0 # Default year, if note specified
    default_release = 5 # Default release, if not specified

    def __init__(self, url=None, downloader=None, **kwargs):

        if any(['table' in kwargs, 'geoid' in kwargs,' summarylevel' in kwargs]):

            if 'year' in kwargs:
                parts = [kwargs['year'], kwargs.get('release', self.default_release)]

            else:
                parts = []

            parts += [kwargs.get('geoid'), kwargs.get('summarylevel'), kwargs.get('table')]

            if len(parts) == 3:
                url = "{}://{}/{}/{}".format(self.proto, *parts )
            else:
                url = "{}:/{}/{}/{}/{}/{}".format(self.proto, *parts)


        super().__init__(url, downloader, **kwargs)

        if not self.netloc:
            # If the URL didn't have ://, there is no netloc
            parts =  self.path.strip('/').split('/')

        else:
            parts = list( [self.netloc] + self.path.strip('/').split('/'))

        parts_len = len(parts)

        if len(parts) == 3:
            parts = [self.default_year, self.default_release ] + parts


        if len(parts)  != 5:
            raise AppUrlError("Census reporters must have 3 or 5 path components. Got: '{}' ".format(parts))

        if self._test_parts(parts):

            parts = self._guess(parts)

            if parts_len  == 3:
                new_url =  "{}://{}/{}/{}".format(self.proto, *(parts[2:]))
            else:
                new_url =  "{}:/{}/{}/{}/{}/{}".format(self.proto, *(parts))

            warn("Badly formatted Census URL. The url '{}' should be '{}' ".format(url, new_url))

        self._year, self._release, self._geoid, self._summary_level, self._tableid = parts


    def _test_parts(self, parts, raise_exception = False):
        """Check if the URL is formatted properly"""
        year, release, geoid, summary_level, tableid = parts

        message = []

        if year is None:
            message.append("No year")
        else:
            try:
                int(year)
            except:
                message.append("Bad year {}".format(year))


        if not release:
            message.append("No release")
        else:
            try:
                assert (int(release) in [1, 3, 5])
            except:
                message.append("Bad release {}".format(release))

        if not geoid:
            message.append("No geoid")
        else:
            try:
                sub_geoids(geoid)
            except:
                message.append("Bad geoid {}".format(geoid))

        if not summary_level:
            message.append("No summary_level")
        else:
            try:
                sub_summarylevel(summary_level)
            except:
                message.append("Bad summarylevel {}".format(summary_level))

        if not tableid:
            message.append("No tableid")
        else:
            try:
                assert(tableid.upper()[0] in ['B','C'])
            except:
                message.append("Bad tableid {}".format(tableid))

        return message


    def _guess(self, parts):
        """Guess at what the URL ought to be"""

        messages = []

        year = release = geoid = summary_level = tableid = None

        for part in parts:


            try:
                int(str(part)[1])
                if part.upper()[0] in ['B','C'] :
                    tableid = part
                    continue
            except (IndexError, ValueError, AttributeError):
                pass

            try:
                sub_geoids(part)
                geoid = part
                continue
            except (ValueError, TypeError):
                pass

            try:
                sub_summarylevel(part)
                summary_level = part
                continue
            except (ValueError, KeyError):
                pass

            try:
                if int(part) in [1,3,5]:
                    release = int(part)
                continue
            except ValueError:
                pass

            try:
                if 2004 < int(part) < 2050:
                    year = int(part)
                continue
            except ValueError:
                pass

            messages.append("Failed to parse '{}' ".format(part))



        year = year or self.default_year
        release = release or self.default_release

        messages += self._test_parts([year, release, geoid, summary_level, tableid])

        if messages:
            raise CensusParsingException("Failed to parse census url '{}' : {}".format('/'.join(str(e) for e in parts),
                                                                                      '; '.join(messages)))

        return year, release, geoid, summary_level, tableid


    @property
    def geoid(self):
        '''Return the containment Geoid'''
        return sub_geoids(self._geoid)

    @property
    def summary_level(self):
        '''Return the sumary level code'''
        return sub_summarylevel(self._summary_level)


    @property
    def tableid(self):
        '''Return the table id'''
        return self._tableid

    @property
    def year(self):
        return self._year

    @property
    def release(self):
        return self._release


    @property
    def geo_url(self):
        """Return the URL for geographic data for this URL"""
        raise NotImplemented()

    @property
    def dataframe(self):
        """Return a Pandas dataframe with the data for this table"""
        return self.generator.dataframe()

    @property
    def geo_generator(self):
        return self.geo_url.get_resource().get_target().generator

    @property
    def geoframe(self):

        return self.geo_generator.geoframe()

    @property
    def cache_key(self):
        """Return the path for this url's data in the cache"""

        return "{}/{}/{}/{}/{}/{}.json".format(self.api_host, *self.path_parts)

    @property
    def path_parts(self):
        return [str(e) for e in [self.year, self.release, self.geoid, self.summary_level,self.tableid]]

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






Public Data Application Urls
============================

This library defines a set of `Application Urls
<https://github.com/CivicKnowledge/appurl>`_ and `Row Generators
<https://github.com/CivicKnowledge/rowgenerators>`_ that allow access to public
datasets. For instance, using the Census Reporter URLs, you can define access
to a American Community Survey data table on the Census Reporter website. Then,
using the associated Row Generator, you can download the data as a sequences of
rows.

For instance, this code will return rows from ACS table B17001 for tracts in San Diego County

.. code-block:: python

    from publicdata import  parse_app_url

    url = parse_app_url("census://CA/140/B17001")

    # Or: url = CensusReporterUrl(table='B17001',summarylevel='140',geoid='CA')

    for row in url.generator:
        print(row)


The library uses the appurl and rowgenerator python entrypoints, so all
libraries that you install that use the entrypoints can be accessed via the
``parse_app_url`` and ``get_generator`` functions.

Census Urls
============


There are two URL types for Census access, distinguished by their scheme names,
``census`` and ``censusreporter``. The ``census`` URLs download files directly
from the Census department's FTP servers, and the ``censusreporter`` urls get
data from the CensusReporter.org apis. Both also have access to geography
files, but the ``census`` urls have a richer interface for metadata.

The general schemes for the URLS are::

    <scheme>:/[/year/release]/<geoid>/<summarylevel>/<table>

Where: 

- <scheme> is either ``census`` or ``censusreporter``
- <year> is the year of the release, which work from 2010 on for ``census`` urls and are ignored for ``censusreporter``
- <release> is 1, 3, or 5, and is applied or ignored as with <year>
- <geoid> defined the geographic region that contains the returned data, and is either an ACS style geoid, or a state abbreviation, or 'US'
- <summarylevel> is either a summary level numeric code, or a summary level name
- <table> is a census table id

The Geoid is an ACS style geoid, such as '04000US06', or a US state abbreviation ( 'AZ' or "CA' ) or 'US'. The geoid defines the area that contains the data to be returned. See the `Geographic Codes Lookup <https://census.missouri.edu/geocodes/>`_ web application for more details about geoids and how to find them. 

The summary level can also be expressed in text names, as described in the `geoid package documentation <https://github.com/Metatab/geoid>`_
. The most common of these names, and their numeric codes, are::


'us': 10,
'region': 20,
'division': 30,
'state': 40,
'county': 50,
'cosub': 60,
'place': 160,
'ua': 400,
'tract': 140,
'blockgroup': 150,
'block': 101,
'sdelm': 950,
'sdsec': 960,
'sduni': 970,
'zcta': 860


Usually the geoid is the abbreviation for a state or a county, and then the summary level describes the type of sub region within that state or county. For instance, all of the counties in California is '04000US06/140' or 'CA/county', and all of the places in San Diego county is '05000US06073/160' or '05000US06073/place'.

You can look up the table ideas at `Census Reporter <http://censusreporter.org>`_ or `American Fact Finder <https://factfinder.census.gov/>`_ . 

Creating Census Reporter Urls
-----------------------------

The ``censusreporter:``  url scheme retrieves data from `Census Reporter <http://censusreporter.org>`_ . The structure of the URL is::

    censusreporter://<geoid>/<summarylevel>/<table>

Or, use the URL directly:

.. code-block:: python

    from publicdata import CensusReporterUrl
    from rowgenerators import Downloader
    CensusReporterUrl(table='B17001',summarylevel='140',geoid='CA', downloader=Downloader())


So, to get the population  of all of the counties in California:

.. code-block:: python

    CensusReporterUrl(table='B17001',summarylevel='county',geoid='CA')

or:

.. code-block:: python

    from rowgenerators import parse_app_url
    parse_app_url('census://CA/county/B17001')

The ``geoid`` may either be a census Geoid ( like '04000US06' ) , or a US state
abbreviation, or 'US' for indicating all US states.


Creating Census File Urls
----------------------

The Census file URLS retrieve data directly from the Census FTP server. You can use the same 3-part url scheme as with Census Reporter, in which case you will get the 2016 5-year ACS. Or, you can specify the year and release::

    census://<year>/<release>/<geoid>/<summarylevel>/<table>
    
Such as::

    census://2015/5/CA/140/B17001
    
or:

.. code-block:: python

    from publicdata import CensusFileUrl
    rom rowgenerators import Downloader CensusFileUrl(year=2016,release=5,table='B17001',summarylevel='140',geoid='CA', downloader=Downloader())

Common Operations
-----------------

Construct the URL:

.. code-block:: python

    url = parse_app_url('census://2015/5/CA/140/B17001')
    
Iterate rows, header first, then data:

.. code-block:: python

    for row in url.generator:
        print(row)
        
or, to return dict-ish object:

.. code-block:: python

    for row in url.generator.iterrows:
        print(row.geometry, row['geometry])
    
Get a pandas dataframe ( Actually a CensusDataframe):

.. code-block:: python

    url.dataframe
    
Get a Geopandas dataframe:

.. code-block:: python

    url.geoframe

Census Dataframes
-----------------

For a general overview of the features of the Census URLs, see the `ACS Notebook <https://github.com/Metatab/publicdata/blob/master/notebooks/ACS.ipynb>`_.

The ``.dataframe`` property returns a ``CensusDataFrame`` which has some
special features for working with Census data, including margin-aware
summation, ratios, proportions and margin manipulations. See the `Special
Features of Census Dataframes <https://github.com/Metatab/publicdata/blob/master/notebooks/Special%
20Features%20of%20Census%20Dataframe.ipynb>`_ notebook for details.



Goals
=====

The `ADSFree online book <http://asdfree.com/l>`_ has an excellent list of
datasets ( and R code for downloading them ) that this library should
incorporate. The author also has downloading code for these datasets in the
`lowdown R package <https://github.com/ajdamico/lodown>`_

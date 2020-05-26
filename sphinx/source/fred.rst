FRED: Federal Reserve Economic Data
===================================


The FRED package includes both an application url for FRED series and a
program for manipulating Metapack programs.


FRED Urls
---------

The FRED URl can specify a one or mulltiple series identifier:

- fred:series/start-date/end-date
- fred:series/start-date
- fred:series

The Parser will also accept a '//:

- fred://series/start-date/end-date

The `series`


This URL requires an API key, which can be obtained from the FRED website. The key must be set in the environmental variable FRED_API_KEY


FRED Support for Metapack
--------------------------


Set a `Fred` section in the metatab file, with similar content::

    Section: Fred|Title
    Start: 2019-01-01
    End: 2020-01-01
    Series: TDSP
    Series: SP500
    Series: GDPC1

The `Start` and `End terms define the start and end dates. Each series is defined with a
`Series` term.

Then, run the `mp fred update` program, which will:

- Add titles from the FRED API to each of the `Series` terms in the `Fred` section
- Create new `Reference` termsin with `fred:` urls, including names and descriptions from the FRED API.
- Create a `DataFile` term, names `fred_frame` that combines all of the `Series` entries into a single URL
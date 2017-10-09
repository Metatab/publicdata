Public Data Application Urls
============================

This library defines a set of `Application Urls <https://github.com/CivicKnowledge/appurl>`_
and `Row Generators <https://github.com/CivicKnowledge/rowgenerators>`_ that allow access
to public datasets. For instance, using the Census Reporter URLs, you can define access
to a American Community Survey data table on the Census Reporter website. Then, using
the associated Row Generator, you can download the data as a sequences of rows.

For instance, this code will return rows from ACS table B17001 for tracts in San Diego County

.. code-block:: python

    from publicdata import  parse_app_url

    url = parse_app_url("censusreporter:B17001/140/05000US06073")

    # Or: url = CensusReporterUrl(table='B17001',summarylevel='140',geoid='05000US06073')

    for row in url.generator:
        print(row)


The library uses the appurl and rowgenerator python entrypoints, so all libraries that
you install that use the entrypoints can be accessed via the ``parse_app_url``
and ``get_generator`` functions.

Goals
=====

The  `ADSFree online book <http://asdfree.com/l>`_ has an excellent list of datasets
( and R code for downloading them ) that this library should incorporate. The author
also has downloading code for these datasets in the `lowdown R
package <https://github.com/ajdamico/lodown>`_
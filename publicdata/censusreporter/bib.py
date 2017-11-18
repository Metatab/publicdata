def make_citation_dict(t):
    """
    Return a dict with BibText key/values
    :param t:
    :return:
    """

    from datetime import datetime
    from appurl import Url

    try:
        if Url(t.url).proto == 'censusreporter':

            try:
                url = str(t.resolved_url.url)
            except AttributeError:
                url = t.url

            return {
                'type': 'dataset',
                'name': t.name,
                'origin': 'United States Census Bureau',
                'publisher': 'CensusReporter.org',
                'title': "2010 - 2015 American Community Survey, Table {}: {}".format(t.name.split('_', 1).pop(0), t.description),
                'year': 2015,
                'accessDate': '{}'.format(datetime.now().strftime('%Y-%m-%d')),
                'url': str(url)
            }
    except (AttributeError, KeyError) as e:

        pass


    return False
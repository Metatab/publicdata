
def convert_citation_xml(citation_xml_str):

    from xmljson import yahoo
    import json

    import xml.etree.ElementTree as ET

    citation_xml = ET.fromstring(citation_xml_str)

    js = yahoo.data(citation_xml)['PubmedArticle']

    cit = js['MedlineCitation']

    pmdata = js['PubmedData']

    print(json.dumps(pmdata, indent=4))

    dc = cit['DateCompleted']
    date = "{}-{}-{}".format(dc['Year'], dc['Month'], dc['Day'])
    year = int(dc['Year'])
    title = cit['Article']['ArticleTitle']
    abstract = cit['Article']['Abstract']

    pmc_id = None
    for ai in pmdata.get('ArticleIdList', {}).get('ArticleId',[]):
        if ai.get('IdType') == 'pmc':
            pmc_id = ai.get('content')

    pmid = cit.get('PMID',{}).get('content')

    def yield_mh():
        for e in cit['MeshHeadingList']['MeshHeading']:

            d = {
                'dn': e['DescriptorName']['UI'], # Descriptor number
                'dmt': True if e['DescriptorName']['MajorTopicYN'] == 'Y' else False, # Descriptor major topic
                'd': (e['DescriptorName']['content'] or '').lower()
            }

            if 'QualifierName' in e:
                if isinstance(e['QualifierName'], dict):
                    q = [e['QualifierName']]
                else:
                    q = e['QualifierName']

            else:
                q = [{
                "UI": "Q000000",
                "MajorTopicYN": "N",
                "content": None
                }]

            for e in q:
                dq = dict(**d)
                dq.update({
                    'qn': e['UI'],  # Descriptor number
                    'qmt': True if e['MajorTopicYN'] == 'Y' else False,  # Descriptor major topic
                    'q': (e['content'] or '').lower()
                })

                dq['mt'] = dq['dmt'] or dq['qmt']
                dq['dqid'] = int(dq ['dn'][1:] + dq ['qn'][1:])

                yield dq

    def yield_references():

        if not 'CommentsCorrectionsList' in cit:
            return

        ccl = cit['CommentsCorrectionsList']
        if not 'CommentsCorrections' in ccl:
            return

        for r in ccl['CommentsCorrections']:
            if r['RefType'] == 'Cites' and 'PMID' in r:
                yield r['PMID']['content']

    def yield_authors():

        al = cit.get('Article',{}).get('AuthorList', {}).get("Author",[])

        for r in al:
            try:
                yield r['Initials']+' '+r['LastName']
            except TypeError: # No idea, seems to get a string sometimes, for the ValidYN key.
                pass

    return {
        'pmid': pmid,
        'pmc': pmc_id,
        'date': date,
        'year': year,
        'title': title,
        'abstract': abstract,
        'headings':  list(yield_mh()),
        'refs': list(yield_references()),
        'authors': list(yield_authors()),

    }


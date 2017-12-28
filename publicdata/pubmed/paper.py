# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE




def convert_doc(data):

    import json
    from lxml import etree as ET
    from xmljson import yahoo

    element = ET.fromstring(data)

    # the keys for these elements are invalid for BSON, used in MongoDB
    if False:
        for excl in ('//inline-formula','//ext-link','//uri',
                     '//{http://www.w3.org/1998/Math/MathML}math',
                     '//{http://www.w3.org/XML/1998/namespace}lang',
                     '//{http://www.w3.org/1999/xlink}href'):
            for el in element.findall(excl):
                el.getparent().remove(el)

    pmid = element.findtext('.//article-id[@pub-id-type="pmid"]')
    doi = element.findtext('.//article-id[@pub-id-type="doi"]')
    title = element.findtext('.//title-group/article-title')
    abstract = element.findtext('.//abstract')

    sections = []
    for sec in element.findall('.//sec'):

        title = None
        for i in sec.findall('title'):
            title =  i.text

        text = ' '.join(sec.itertext()).encode().decode('ascii','ignore')

        sections.append((title, text))

    refs = [ json.loads(json.dumps(yahoo.data(e), indent=4)) for e in element.findall('.//ref-list')]

    keywords = [ i.text for i in element.findall('.//kwd') ]

    doc = {
        'doi': doi,
        'pmid': pmid,
        'title': title,
        'abstract': abstract,
        'sections': sections,
        'refs': refs,
        'keywords': keywords
    }

    return doc


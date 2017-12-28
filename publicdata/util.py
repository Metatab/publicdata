# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


def extract_tables(d, base_id = ''):
    """For a datastructure d, with it's root being a dict, return a collection of
    row oriented data representing the datastruct flattened and reduced to tables.

    The routine converts dicts into a root table entry, while nested arrays get their
    own tables. The tables are linked by the _id and _parentid fields

    """


    import flatdict
    import re
    import json

    if base_id and not base_id.endswith('_'):
        base_id = base_id+'_'

    array_index = re.compile(r'\:(\d+)')

    def extract_array_index(l, parent_prefix=[], parent_index=[]):
        m =  array_index.search(l)
        if m:
            prefix =  l[:m.start()].replace(':','_').lower()
            suffix = l[m.end():].strip(':')
            index = int(m[0].strip(':').replace(':','_'))

            psi = extract_array_index(suffix, parent_prefix+[prefix], parent_index+[index])

            if psi is False:
                return (parent_prefix+[prefix], parent_index+[index], suffix.replace(':','_').lower())
            else:
                return psi

        else:
            return False

    tables = {}

    for k, value in flatdict.FlatDict(d).items():

        psi =  extract_array_index(k)

        if psi:
            table_name = ('_'.join(psi[0]))
            index = '_'.join(str(e) for e in psi[1]) or "X"
            column_name = psi[2] or 'value'
            parent_table = '_'.join(psi[0][:-1])
            parentid = (parent_table +'_'+ '_'.join(str(e) for e in psi[1][:-1]) or "X")
        else:
            table_name = ''
            index = ''
            column_name = k.replace(':','_').lower()
            parentid = None

        if not table_name in tables:
            tables[table_name] = {}


        if not index in tables[table_name]:
            tables[table_name][index] = {
                '_parentid': (base_id+parentid).strip('_') if parentid else None,
                '_id': base_id+table_name+'_'+index
            }

        tables[table_name][index][column_name] = value

    records = {}

    for k, v in tables.items():
        if not k:
            k = 'root'

        records[k] = []

        for i, r in v.items():
            records[k].append(r)

    return records
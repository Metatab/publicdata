# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from os import remove
from os.path import exists
import argparse
from metapack.cli.core import prt, err, warn
from metapack.cli.core import  get_config as _get_config
from metapack.cli.core import MetapackCliMemo as _MetapackCliMemo
from metapack import Downloader
from fredapi import Fred
from collections import namedtuple

downloader = Downloader.get_instance()

class ArgumentError(Exception): pass

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

def fred(subparsers):
    """
    Manipulate Metatab documents with FredSeries entries, for the St Louis FED's
    FRED economic data server.
    """


    parser = subparsers.add_parser('fred',
                                   help='Manipulate references to FRED',
                                   description=fred.__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   )

    parser.set_defaults(run_command=run_fred)

    #parser.add_argument('-j', '--json', default=False, action='store_true',
    #                    help='Display configuration and diagnostic information ad JSON')

    subparsers = parser.add_subparsers()

    ##  Update Entries

    load = subparsers.add_parser('update', help='Update FredSeries entries in a Metatab Document')
    load.set_defaults(sub_command=run_update_cmd)

    load.add_argument('-r', '--resource', default=False, action='store_true',
                      help='Add resource reference to build dataset from FredSeries references')
    # load.add_argument('urls', nargs='*', help="Database or Datapackage URLS")

    ## Create a remote instance

    #info = subparsers.add_parser('remote', help='Create a remote for this package')
    #info.set_defaults(sub_command=run_remote_cmd)

    #info.add_argument('url', help="Database or Datapackage URL")

    parser.add_argument('metatabfile', nargs='?', help="Path to a notebook file or a Metapack package")


def run_fred(args):
    m = MetapackCliMemo(args, downloader)

    args.sub_command(m)

def get_config():
    config = _get_config()

    if config is None:
        err("No metatab configuration found. Can't get Github credentials. Maybe create '~/.metapack.yaml'")

    return config

def get_token():

    return get_config().get('github', {}).get('token')

from metatab.util import slugify

def run_update_cmd(m):
    fred = Fred()

    changed = False

    # Ensure there is a Title argument for the section
    if 'Fred' in m.doc:
        s = m.doc['Fred']

        if 'Title' not in m.doc['Fred'].args:
            m.doc['Fred'].add_arg('Title')
            changed = True

        if 'Units' not in m.doc['Fred'].args:
            m.doc['Fred'].add_arg('Units')
            changed = True

        if 'SeasonalAdj' not in m.doc['Fred'].args:
            m.doc['Fred'].add_arg('SeasonalAdj')
            changed = True

        if 'Notes' not in m.doc['Fred'].args:
            m.doc['Fred'].add_arg('Notes')
            changed = True

    try:
        start = m.doc['Fred'].get_value('Root.Start', default=None)
        end = m.doc['Fred'].get_value('Root.End', default=None)
    except KeyError:
        start = None
        end = None

    # What references do we already have?
    refs = list(sorted([r.name for r in m.doc.references() if r.value.startswith('fred:')]))

    # Transform Fred Series entries

    for t in m.doc['Fred'].find('Root.Series'):
        name = t.value

        if name not in refs:

            url = 'fred:' + '/'.join([e for e in [name, start, end] if e])
            d = fred.search(t.value).loc[t.value]
            desc = f"{d.title}, {d.units}. { d.notes} Seasonality: {d.seasonal_adjustment}"

            m.doc['References'].new_term('Root.Reference', url,
                                         name=name,
                                         description=desc)
            t['Title'] = d.title
            t['Units'] = d.units
            t['SeasonalAdj'] = d.seasonal_adjustment
            t['Notes'] = d.notes

            changed=True

    # Add the Datafile entry to generate a datafile from the FredSeries entries,
    # if it had not been added yet.

    refs = list(sorted([r.name for r in m.doc.references() if r.value.startswith('fred:')]))

    url = 'fred:' + '/'.join([e for e in [','.join(refs), start, end] if e])

    for t in m.doc['Resources'].find('Root.Datafile'):
        if url in t.value:
            break
    else:
        t = m.doc['Resources'].new_term('Datafile',url, name='fred_frame',
                                        description=f"FRED data series: {','.join(refs)}")
        changed = True


    # Add the title, etc to the schema.
    def get_fred_term(name):
        for t in m.doc['Fred'].find('Root.Series'):
            if t.value.lower() == name.lower():
                return t
        else:
            return None
            #NullTerm = namedtuple('NullTerm','title units seasonaladj notes')
            #return NullTerm('', '', '', '')


    for t in m.doc['Schema'].find('Table.Column'):
        if 'description' not in t.props:
            ft = get_fred_term(t.name)
            if ft:
                t['Description'] = f"{ft.title}. {ft.units}, {ft.seasonaladj}".strip()
                changed = True

    # Done!
    if changed:
        m.doc.write()

def run_remote_cmd(m):
    pass

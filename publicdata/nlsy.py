# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from itertools import islice
from math import ceil

import csv
import h5py
import numpy as np
import pandas as pd
from copy import copy
from pathlib import Path
from rowgenerators import Source
from rowgenerators.appurl.web import WebUrl


class NlsyUrl(WebUrl):
    pass


class NlsySource(Source):
    pass


class NLSY(object):

    respondent_cols = None # Columns for variables that are about the respondent, across years.

    def __init__(self, data_ref, weights_ref=None):

        assert data_ref

        self._data_ref = data_ref
        self._weigths_ref = weights_ref

        self._question_groups = None
        self._var_labels = None

    def _variable_labels(self, ref):
        """
        Given a Metapack reference Term that references a downloaded NLSY data set,
        return a Pandas dataframe with metadata about the variables included in the data package.

        First, download data dataset from the NLS Investigator, and store it locally. When downloading,
        use the "Advanced Download" tab, and be sure that "Short Description File" is checked.  In this example,
        the downloaded zip file is stored in the ``data`` directory, which is in the same directory
        as the ``metatab.csv`` file.

        The, add a Reference term to a Metapack metadata file, as shown below in Metatab Line Format:

            Section: References
            Reference: data/shiftwork.zip#.*.sdf
            Reference.Name: var_list


        Them to call this function, in this case, from an IPython notebook in the datapackage:

        >>> import metatab as mt
        >>> pack = mt.jupyter.open_package()
        >>> variable_labels(pack.reference('var_list'))

        :param ref a Metapack Refernce Term:
        :return: a pandas dataframe
        """
        import pandas as pd

        t = ref.resolved_url.get_resource().get_target()

        vdf = pd.read_fwf(t.path, header=1, skiprows=[0, 1, 4])

        vdf['Number'] = vdf['Number'].str.replace('.', '')

        def extract_parts(v):
            parts = v.split('.')
            parts += [float('nan')] * (4 - len(parts))
            parts[0] = parts[0].replace('!', '_').replace('-','_')  # KEY!SEX -> KEY_SEX
            return parts

        vdf['question_root'] = vdf['Question Name'].apply(lambda v: extract_parts(v)[0])
        vdf['dim_1'] = vdf['Question Name'].apply(lambda v: extract_parts(v)[1])
        vdf['dim_2'] = vdf['Question Name'].apply(lambda v: extract_parts(v)[2])
        vdf['dim_3'] = vdf['Question Name'].apply(lambda v: extract_parts(v)[3])

        vdf.set_index('Number', inplace=True)

        vdf.rename(columns={
            'Year': 'year',
            'Variable Description': 'description',
            'Question Name': 'question_name'
        }, inplace=True)

        vdf.index.name = 'var_name'

        return vdf

    @property
    def var_labels(self):
        """Return a dataframe of the metadata for all of the variables."""
        if self._var_labels is None:
            r = copy(self._data_ref)
            r.url += '#.*\.sdf'
            self._var_labels = self._variable_labels(r)

            # XRND, cross round, in NLYS97, question asked in various years
            # 78SCRN, NLSY79 screening question
            try:
                self._var_labels['year'] = self._var_labels['year'].str.replace("XRND", "0").str.replace('78SCRN',"0")
            except AttributeError: # Probably b/c not a string col
                pass

            self._var_labels['year'] = self._var_labels['year'].astype(int)

        return self._var_labels

    @property
    def questions(self):
        """Like var_labels(), but return only one row per question"""
        return self.var_labels[['question_root', 'description']] \
            .drop_duplicates(subset=['question_root']).set_index('question_root').sort_index()

    @property
    def data(self):
        r = copy(self._data_ref)
        r.url += '#.*\.csv'
        df = r.dataframe().astype(int).set_index('R0000100')
        df.index.name = 'case_id'  # NLSY97 actually uses pubid; case_id is from 79
        return df.astype(int)

    @property
    def weights(self):
        """Return the weights data, if it was specified"""
        if self._weigths_ref:

            r = copy(self._weigths_ref)
            r.url += '#.*\.dat'
            w = r.read_csv(sep=' ', names=['case_id', 'weight']).astype(int).set_index('case_id')

            return w / 100  # Weigths have 2 implicit decimals

        else:
            return None

    @property
    def question_groups(self):
        """Return variable metadata for specific questions"""
        if not self._question_groups:
            self._question_groups = self.var_labels.reset_index().set_index('year').groupby('question_root')

        return self._question_groups

    @property
    def question_names(self):
        return list(self.question_groups.groups.keys())

    def question_frame(self, qn, column_name=None, dim_1_index = False, dim_2_index = False, dim_3_index = False):
        """Return the dataframe from the question groups for a specific question

        :param qn:
        :param column_name:
        :param employer_index:
        :return:

        """

        # All of the variable names for the question
        q_vars = list(self.question_groups.get_group(qn).var_name)

        _ = self.data[q_vars].stack().to_frame()  # Move the var_names to the index, so we can merge with metadata
        _.index.names = ['case_id', 'var_name']

        dim_1_name = 'dim_1'
        dim_2_name = 'dim_2'
        dim_3_name = 'dim_3'

        dim_1_rename = dim_1_name if not isinstance(dim_1_index, str) else dim_1_index
        dim_2_rename = dim_2_name if not isinstance(dim_2_index, str) else dim_2_index
        dim_3_rename = dim_3_name if not isinstance(dim_3_index, str) else dim_3_index

        vl_cols = ['year']
        index_cols = ['case_id', 'year']

        if column_name is None:
            column_name = qn

        renames = {0: column_name}

        if dim_1_index:
            vl_cols.append(dim_1_name)
            index_cols.append(dim_1_name)
            renames[dim_1_name] = dim_1_rename

        if dim_2_index:
            vl_cols.append(dim_2_name)
            index_cols.append(dim_2_name)
            renames[dim_2_name] = dim_2_rename

        if dim_3_index:
            vl_cols.append(dim_3_name)
            index_cols.append(dim_3_name)
            renames[dim_3_name] = dim_3_rename

        return _.join(self.var_labels[vl_cols])\
            .reset_index().rename(columns=renames)\
            .drop('var_name', axis=1)\
            .set_index(['case_id','year'])


    def employment_question_frame(self, qn):
        """Return the dataframe from the question groups for a specific employment question, which
        includes the employer number in the index"""

        return self.question_frame(qn, dim_1_index='employer_no')


class NLSY97(NLSY):
    # Variables that only appear in one year.
    respondent_cols = ['CV_SAMPLE_TYPE', 'KEY!BDATE_M', 'KEY!BDATE_Y', 'KEY!RACE_ETHNICITY', 'KEY!SEX']


class NLSY79(NLSY):
    # Variables that only appear in one year, maybe?
    respondent_cols = ['SAMPLE_ID','SAMPLE_RACE','SAMPLE_SEX','SHIFTSP_86A','VERSION_R26']


def extract_from_codebook(f, cb=None):
    """
    Parse the codebook for the NYLS79 full dataset, downloadable from
    https://www.nlsinfo.org/accessing-data-cohorts


    :param f:
    :return:
    """

    import re
    import hashlib

    vars = []
    var = None
    var_line = 0
    var_no = 0
    in_val_labels = False

    if not cb:
        cb = lambda v: None

    for line_no, l in enumerate(f.readlines()):

        cb(line_no)

        if 'Survey Year' in l and 'COMMENT' not in l:
            var_line = 0
            var_no += 1
            p = l.split()
            var = {
                'var_no': var_no,
                'col_no': var_no -1,
                'labels': {},
                'labels_id': None,
                'variable_name': p[0],
                'variable_name_nd': p[0].replace('.', ''),
                'question_name': p[1].replace('[', '').replace(']', ''),
                'survey_year': p[4]
            }

        if len(l.strip()) == 0:
            pass

        if var_line == 4:
            var['question'] = l.strip()

        # Mark the indented value labels
        if re.match(r'\-{5,20}', l.strip()) and in_val_labels:  # '-----', the summation line for value counts
            # Marks end of value label
            in_val_labels = False
        elif re.match(r'\s{4,8}\d', l) and not var['labels']:
            in_val_labels = True

        if '---------------------------------' in l:
            # Marks end of question

            var['labels_id'] = hashlib.sha224(
                ('\n'.join(["{}:{}".format(*e)for e in sorted(var['labels'].items())])).encode('utf8')
            ).hexdigest()

            if var:
                vars.append(var)

            v = None

        if in_val_labels:  # Not quite working

            try:
                l = l.strip()
                if ':' in l:
                    m = re.match(r'(\d+)\s+([^:]+):(.*)', l)
                    count, val, label = m.groups() if m else (None, None, None)
                elif ' TO ' in l:
                    m = re.match(r'(\d+)\s+(.*)', l)
                    count,  val = m.groups() if m else (None, None)
                    label = val
                else:
                    m = re.match(r'(\d+)\s+(\d+)\s+(.*)',l)
                    count, val, label = m.groups() if m else (None, None, None)

                if m:

                    if 'TO' in val: # The value is a range
                        parts = val.strip().split()
                        val = '-'.join((parts[0], parts[2]))
                    else:
                        val.strip()

                    var['labels'][val] = label.strip()

            except:
                print('Line: ', l)
                raise

        var_line += 1



    if var:  # Maybe last line doesn't have h-rule marker
        vars.append(var)

    return vars


def parse_vars(resource, doc, *args, **kwargs):
    """
    This is a function for a Metapack Python appurl. It can be used as the URL
    in a ``Datafile`` term to generate the codebook data.

        Datafile: python:publicdata.nlsy#parse_vars

    It requires that the metdata ``Reference`` terms for ``tagset`` and ``codebook``:

        Reference:      https://nlsinfo.org/cohort-data/nlsy79_all_1979-2012.zip#.*.cdb
        Reference.Name: codebook
        Reference:  	https://nlsinfo.org/cohort-data/nlsy79_all_1979-2012.zip#.*.NLSY79
        Reference.Name: tagset

    :param resource:
    :param doc:
    :param args:
    :param kwargs:
    :return:
    """
    from operator import itemgetter
    from metapack.exc import PackageError

    # Load the tagset so we can check that we
    # are getting the correct variables.
    ts_ref = doc.reference('tagset').parsed_url.get_resource().get_target()

    with open(ts_ref.path) as f:
        tags = f.readlines()

    ref = doc.reference('codebook')

    t = ref.parsed_url.get_resource().get_target()

    with open(t.path) as f:
        v = extract_from_codebook(f)

    headers = 'var_no variable_name variable_name_nd survey_year question_name question'.split()

    ig = itemgetter(*headers)

    yield headers

    for v_n, e in enumerate(v):
        row = ig(e)
        # Ensure that the variables have been parsed exactly the same order
        # as the tagset.
        if row[2].strip() != tags[v_n].strip():
            raise PackageError(
                "Variable ref '{}' != tagset ref '{}' "
                    .format(row[2], tags[v_n]))
        yield row


def split():
    from itertools import zip_longest
    import argparse
    from math import ceil
    import numpy as np
    import h5py
    # from tqdm import tqdm

    def tqdm(i, *args, **kwargs):
        return i

    nrows = 8983
    chunk_size = 250
    nchunks = ceil(nrows / chunk_size)

    parser = argparse.ArgumentParser(description='Dump a subset of NLSY columns')
    parser.add_argument('-s', '--start', type=int, help='Start column')
    parser.add_argument('-e', '--end', type=int, help='End column')
    parser.add_argument('base', help='Base file name')

    args = parser.parse_args()

    def header_row():
        # Yield the header
        with open(f'{args.base}.NLSY97') as f:
            return [c.strip() for c in f.readlines()]

    def yield_rows():

        # yield header_row()

        with open(f'{args.base}.dat') as f:
            for i, line in enumerate(f.readlines()):
                yield line.rstrip().split(' ')

                if i > nrows:
                    break

    ncols = len(header_row())

    print(f'{ncols} columns {nchunks} chunks {chunk_size} chunk_size')

    with h5py.File(f'{args.base}.h5', "w") as h5f:
        dset = h5f.create_dataset(f'{args.base}', (chunk_size * nchunks, ncols), dtype=np.int32, chunks=True,
                                  compression="gzip")

        row_n = 0
        # zip_longest chunking from https://stackoverflow.com/a/312644
        for chunkn, chunk in enumerate(
                tqdm(zip_longest(*[iter(yield_rows())] * chunk_size), desc='chunks', total=nchunks)):

            a = np.zeros((chunk_size, ncols), dtype=np.int32)

            for chunk_row_n, row in enumerate(tqdm(chunk, desc=f'rows in chunk', leave=False)):
                try:
                    a[chunk_row_n, :] = [int(e) for e in row]
                except TypeError:
                    break

                row_n += 1

            dset[chunkn * chunk_size:(chunkn + 1) * chunk_size, :] = a[:chunk_size, ]

        dset.resize((nrows, ncols))

def convert_cbd(cdb_file, hdf_file):
    """Convert a .cdb ( data dictionary) file to CSV and add the data to the
    HDF5 file for the survey data"""

    from tqdm import tqdm

    def callback(m, l):
        import sys
        print(">>> {} {:,} lines      ".format(m, l), end='\r')
        sys.stdout.flush()

    csv_meta_file = Path(cdb_file).with_suffix('.meta.csv')
    csv_labels_file = Path(cdb_file).with_suffix('.labels.csv')

    headers_file = Path(cdb_file).with_suffix('.NLSY97')

    last_label_num = 0
    label_nums = {}
    with open(cdb_file) as f, open(csv_meta_file, 'w') as fo, open(csv_labels_file, 'w') as fl:

        v = extract_from_codebook(f, cb=lambda l: callback('processed', l))

        labels = {}

        for i, e in enumerate(tqdm(v, desc='Variables')):

            if 'labels' in e:

                lid = e['labels_id']

                if not lid in label_nums:
                    label_nums[lid] = last_label_num
                    last_label_num += 1

                label_num = label_nums[lid]
                e['labels_id'] = label_num
                labels[label_num] = e['labels']

                del e['labels']

            if i == 0:
                wv = csv.DictWriter(fo, fieldnames=e.keys())
                wv.writeheader()

            wv.writerow(e)

        wl = csv.writer(fl)
        wl.writerow('label_id value lower upper label'.split())

        for i, (lid, labels) in enumerate(tqdm(labels.items(), desc='Values   ')):
            for k, v in labels.items():

                if '-' in k:
                    try:
                        lower, upper = k.split('-')
                    except ValueError:
                        lower, upper = (None, None)
                else:
                    lower = upper = ''

                wl.writerow([lid, k, lower, upper, v])
    ##
    ## Now add the CSV files into the HDF5 file

    with h5py.File(hdf_file, 'r+') as f:

        base = Path(cdb_file).stem

        try:
            f[str(base)]  # Throw exception if it does not exist
        except KeyError:
            raise Exception("Failed to find dataset {}. File has: {}".format(base, list(f.keys())))

        # Value and Variable labels

        for dsn, fn in (('value_labels', csv_labels_file), ('variable_labels', csv_meta_file)):

            dsn = base + '_' + dsn

            values = pd.read_csv(fn)

            if dsn in f:
                del f[dsn]

            f.create_dataset(dsn, values.shape, dtype=h5py.special_dtype(vlen=str), chunks=True, compression="gzip",
                             data=values)

        headers_df = pd.read_csv(headers_file, header=None)

        if base + '_headers' in f:
            del f[base + '_headers']

        f.create_dataset(base + '_headers', (len(headers_df),), dtype=h5py.special_dtype(vlen=str), chunks=True,
                                compression="gzip",
                                data=headers_df)

def convert_nlsy(dat_file, hdf5_file):
    """Convert an nlsy file data file to HDF5"""

    from tqdm import tqdm

    base = Path(dat_file).stem

    nrows = 8983
    chunk_size = 250
    nchunks = ceil(nrows / chunk_size)

    def header_row():
        # Yield the header
        with open(f'{base}.NLSY97') as f:
            return [c.strip() for c in f.readlines()]

    def yield_rows():

        with open(f'{base}.dat') as f:
            for i, line in enumerate(islice(f.readlines(), nrows)):
                yield line.rstrip().split(' ')

    ncols = len(header_row())

    print(f'{ncols} columns {nchunks} chunks {chunk_size} chunk_size')
    chunkn = 0
    with h5py.File(hdf5_file, "w") as h5f:

        dset = h5f.create_dataset(f'base', (chunk_size * nchunks, ncols), dtype=np.int32, chunks=True,
                                  compression="gzip")

        a = np.zeros((chunk_size, ncols), dtype=np.int32)

        for row_n, row in enumerate(tqdm(yield_rows(), total=nrows, ncols=80)):

            a[row_n % chunk_size, :] = [int(e) for e in row]

            if (row_n + 1) % chunk_size == 0:
                dset[chunkn * chunk_size:(chunkn + 1) * chunk_size, :] = a[:, :]
                a = np.zeros((chunk_size, ncols), dtype=np.int32)
                chunkn += 1
        else:
            dset[chunkn * chunk_size:(chunkn + 1) * chunk_size, :] = a[:, :]

        dset.resize((nrows, ncols))

# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Functions for converting the code book, the .cdb file
"""

from pathlib import Path
import csv
from tqdm import tqdm
import pickle


def pair_slugify(e):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata

    value = "{} {}".format(*e)
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8').strip().lower()
    value = re.sub(r'[^\w\s]', '', value)
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'[-\s]+', '-', value)

    return value

def split_dims(qn):
    """Extract the base question name, dimensions and comonent from the question name"""

    base_qn, rem = qn.split('.', 1) if '.' in qn else (qn, '')
    rem = rem.replace('_', '~')  # Seems to be a consistency error

    x, component = rem.split('~') if '~' in rem else (rem, None)

    dims = x.split('.')

    dims += [None] * (3 - len(dims))  # pad to length 3

    return [base_qn + ('~' + component if component else '')] + dims + [component]


def _extract_from_codebook(f, cb=None, limit = None):
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
    var_labels_done = False
    var_label_lines = []

    if not cb:
        cb = lambda v: None

    for line_no, l in enumerate(f.readlines()):

        cb(line_no)

        if 'Survey Year' in l and 'COMMENT' not in l:
            var_line = 0
            var_no += 1
            p = l.split()

            qn =  p[1].replace('[', '').replace(']', '')

            base_qn, *dims, component = split_dims(qn)

            question_group,*_ = re.sub('[\!\-\~\.\_\d]','-',base_qn).split('-')

            var = {
                'var_no': var_no,
                'col_no': var_no -1,
                'label_lines': [],
                'labels_id': None,
                'is_categorical': None,
                'var_level': None,
                'variable_name': p[0],
                'variable_name_nd': p[0].replace('.', ''),
                'question_name': qn,
                'base_qn': base_qn,
                'question_group': question_group,
                'component': component,
                'response_choice': None,
                'dim1': dims[0],
                'dim2': dims[1],
                'dim3': dims[2],
                'survey_year': p[4]

            }

            var_labels_done = False



        if len(l.strip()) == 0:
            pass

        if var_line == 4:
            var['question'] = l.strip()


        m = re.search('RESPONSE CHOICE: \"([^\"]+)\"', l)

        if m:
            var['response_choice'] = m.group(1)



        m = re.search('(PRIMARY|SECONDARY|TERTIARY) VARIABLE', l)
        if m:
            var['var_level'] = m.group(1)


        # Mark the indented value labels
        if re.match(r'\-{5,20}', l.strip()) and in_val_labels:  # '-----', the summation line for value counts
            # Marks end of value label
            in_val_labels = False
            var_labels_done = True
            var['label_lines'] = var_label_lines
            var_label_lines = []
            continue

        elif re.match(r'^\s{4,8}\d', l) and not var_label_lines and not var_labels_done:
            in_val_labels = True

        if in_val_labels:
            if l.startswith('    '):
                var_label_lines.append(l.rstrip())

        if '---------------------------------' in l:
            # Marks end of question

            if var:
                vars.append(var)

            v = None

            if limit is not None:
                if line_no > limit:
                    break


        var_line += 1

    if var:  # Maybe last line doesn't have h-rule marker
        vars.append(var)

    return vars

def extract_from_codebook(cdb_file, limit=None, force=False):
    """Extract the code book to a data structure, cached on disk"""


    pkl_file = Path(cdb_file).with_suffix('.cdb.pkl')

    cdb_length = sum(1 for _ in open(cdb_file))

    if not pkl_file.exists() or force:

        with open(cdb_file) as f:
            extract_progress = tqdm(total=cdb_length, desc='Extract  ', ncols=80)
            v = _extract_from_codebook(f, cb=lambda l: extract_progress.update(), limit=limit)
            extract_progress.close()

        with pkl_file.open('wb') as f:
            pickle.dump(v, f)

        return v

    else:

        with pkl_file.open('rb') as f:
            return pickle.load(f)



def create_label_sets(procd_val_labels):
    from .labels import get_remap_dict, process_value_labels
    import hashlib

    rd = get_remap_dict(procd_val_labels)

    labels = {}
    qn_to_hash = {}

    for qn, bqn, is_range, is_categorical, d in tqdm(procd_val_labels, desc='create label sets'):

        if is_categorical:

            for k, v in list(d.items()):
                d[k] = rd.get(qn+':'+k,{}).get(k,v)

                slugs = list(sorted([pair_slugify(e) for e in sorted(d.items())]))

                labels_hash = hashlib.sha224(('\n'.join(slugs).encode('utf8'))).hexdigest()

                labels[labels_hash] = (d, is_range, is_categorical)

                qn_to_hash[qn] = labels_hash

    hash_to_int = { hash:i for i,hash in enumerate(labels.keys())}

    labels = { hash_to_int[hash]:d for hash,d in labels.items()}
    qn_to_lid = { qn: hash_to_int[hash] for qn,hash in qn_to_hash.items()}

    return labels, qn_to_lid

def create_reduced_label_sets(procd_val_labels):
    from .labels import get_remap_dict, process_value_labels
    import hashlib

    rd = get_remap_dict(procd_val_labels)

    labels = {}
    qn_to_hash = {}

    for qn, bqn, is_range, is_categorical, d in tqdm(procd_val_labels, desc='create label sets'):

        if is_categorical:

            for k, v in list(d.items()):
                d[k] = rd.get(qn+':'+k,{}).get(k,v)

                slugs = list(sorted([pair_slugify(e) for e in sorted(d.items())]))

                labels_hash = hashlib.sha224(('\n'.join(slugs).encode('utf8'))).hexdigest()

                labels[labels_hash] = (d, is_range, is_categorical)

                qn_to_hash[qn] = labels_hash

    hash_to_int = { hash:i for i,hash in enumerate(labels.keys())}

    labels = { hash_to_int[hash]:d for hash,d in labels.items()}
    qn_to_lid = { qn: hash_to_int[hash] for qn,hash in qn_to_hash.items()}

    return labels, qn_to_lid


def convert_cdb(cdb_file):
    """Convert a .cdb ( data dictionary) file to CSV and add the data to the
    HDF5 file for the survey data"""

    from tqdm import tqdm
    from .labels import process_value_labels

    csv_meta_file = Path(cdb_file).with_suffix('.meta.csv')
    csv_labels_file = Path(cdb_file).with_suffix('.labels.csv') # All labels
    csv_reducedlabels_file = Path(cdb_file).with_suffix('.rlabels.csv')  # Reduced labels

    codeb = extract_from_codebook(cdb_file)

    procd_value_labels = list(process_value_labels(codeb))

    wrote_files = []

    ##
    ##  Write full Labels file
    with open(csv_labels_file, 'w') as fl:
        wl = csv.writer(fl)
        wl.writerow('question_name base_name value label'.split())

        for i,(qn, base_qn, is_range, is_categorical, d)  in enumerate(tqdm(procd_value_labels, desc='Full Labels')):
            if is_categorical:
                for k,v in d.items():
                    wl.writerow([qn, base_qn, k, v])

        wrote_files.append(csv_labels_file)

    labels, qn_to_lid = create_label_sets(procd_value_labels)

    ##
    ## Write meta csv, and extract labels for later.
    with open(csv_meta_file, 'w') as fo:

        for i, e in enumerate(tqdm(codeb, desc='Variables')):

            e['labels_id'] = qn_to_lid.get(e['question_name'])

            if e['labels_id']:
                (_, _, e['is_categorical']) = labels[ e['labels_id']]
            else:
                e['is_categorical'] = 0

            # No idea why some of these are missing sometimes
            for k in ['labels_hash', 'labels', 'label_lines']:
                try:
                    del e[k]
                except KeyError:
                    pass

            if i == 0:
                wv = csv.DictWriter(fo, fieldnames=e.keys())
                wv.writeheader()

            wv.writerow(e)

        wrote_files.append(csv_meta_file)

    ##
    ##  Write Labels file
    with open(csv_reducedlabels_file, 'w') as fl:
        wl = csv.writer(fl)
        wl.writerow('label_id value label'.split())

        for i, (lid, labels) in enumerate(tqdm(sorted(labels.items()), desc='Reduced Labels   ')):

            for k, v in labels[0].items():
                wl.writerow([lid, k, v])

            if not labels:
                # This happens once, for instance with BIOCHILD_BDATE.01~Y
                wl.writerow([lid, None, None])

        wrote_files.append(csv_reducedlabels_file)


    return wrote_files

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Convert an NLSY codebook to CSV files')

    parser.add_argument('-e', '--extract', action='store_true', help='Only extract the cdb file, ignoring the cached version')

    parser.add_argument('-c', '--convert', action='store_true', help='Create the meta and label files.')

    parser.add_argument('-L','--limit', type=int, help='set limit for number of rows processed with -e')

    parser.add_argument('-l', '--labels', action='store_true',
                        help='Process label lines')

    parser.add_argument('cdb_file', help='.cdb file')

    args = parser.parse_args()

    if args.extract:
        extract_from_codebook(args.cdb_file, force=True, limit=args.limit)

    if args.convert:
        convert_cdb(args.cdb_file)

if __name__ == "__main__":
    # execute only if run as a script
    main()


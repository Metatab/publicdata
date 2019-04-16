# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Functions for processing value labels
"""
import csv

from pathlib import Path
from tqdm import tqdm

import fuzzy

dmeta = fuzzy.DMetaphone()

from nltk.tokenize import RegexpTokenizer

tokenizer = RegexpTokenizer(r'\w+')


def dmeta_sub(s1, s2):
    try:
        p1 = sorted(dmeta(str(e))[0] for e in tokenizer.tokenize(str(s1)))
        p2 = sorted(dmeta(str(e))[0] for e in tokenizer.tokenize(str(s2)))
    except TypeError:
        # print("!!! {}, {}".format(s1, s2))
        return 100
        # raise

    if all(w1 in p2 for w1 in p1) or all(w2 in p1 for w2 in p2):
        return 0
    else:
        return 100


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata

    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8').strip().lower()
    value = re.sub(r'[^\w\s]', '', value)
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'[-\s]+', '', value)

    return value


def multi_label_questions(meta_df):
    g = meta_df.groupby('base_qn')

    for name in g.groups:
        labels = list(g.get_group(name).labels_id.unique())
        if len(labels) > 1:
            yield name


def cluster_words(words, thresh=8):
    """Return clusters of words, where word are added to clusters where
    the word has an average levenshtein of less than a threshold

    Each word is actally a tuple, with the word being the first item, and any other
    data in subsequent items

    """

    import stringdist

    clusters = []

    for w1 in words:

        placed = False
        for cluster in clusters:
            # Average dist to all words in the cluster
            ad = sum(stringdist.levenshtein(slugify(w1[0]), slugify(w2[0])) for w2 in cluster) / float(len(cluster))
            if ad < thresh:
                cluster.add(w1)
                placed = True
                break

            elif any(dmeta_sub(w1[0], w2[0]) < thresh for w2 in cluster):
                cluster.add(w1)
                placed = True
                break

        if not placed:
            clusters.append(set([w1]))

    return clusters


def get_clusters(qn, meta_df, label_df):
    label_ids = meta_df[meta_df.base_qn == qn].labels_id.astype(int)

    g = label_df[label_df.label_id.isin(label_ids)].groupby('value')

    for value in g.groups:
        group = g.get_group(value)
        words = set(zip(group.label, group.label_id))

        clusters = cluster_words(words)

        if len(clusters) > 1:
            yield (value, clusters)


def merged_value_map(qn, meta_df, label_df):
    def _merged_value_map(qn, meta_df, label_df):
        label_ids = meta_df[meta_df.base_qn == qn].labels_id.astype(int)

        g = label_df[label_df.label_id.isin(label_ids)].groupby('value')

        for value in g.groups:
            group = g.get_group(value)
            words = set(zip(group.label, group.label_id))

            clusters = cluster_words(words)

            def shortest_value(cluster):
                try:
                    shortest = min((e[0] for e in cluster if e[0].strip()), key=len).strip()
                except ValueError:
                    shortest = list(cluster)[0][0].strip()

                return shortest

            def convert_to_columns(lids):
                return list(
                    meta_df[meta_df.labels_id.isin(label_ids)].variable_name_nd.unique())

            if len(clusters) == 1:
                # If there is only one cluster, The value maps  directly to one of the values

                cluster = next(iter(clusters))
                yield (value, shortest_value(cluster))
            else:
                labels = [shortest_value(cluster) for cluster in clusters]
                columns = tuple(convert_to_columns(e[1] for e in cluster) for cluster in clusters)

                yield (value, list(zip(labels, columns)))

    d = dict(_merged_value_map(qn, meta_df, label_df))
    remaps = [k for k, v in d.items() if isinstance(v, list)]

    return d, remaps


def remap_values(meta_df, label_df):
    multi_labels = list(multi_label_questions(meta_df))

    for qn in multi_labels:
        qn_value_clusters = get_clusters(qn, meta_df, label_df)

        for value, clusters in qn_value_clusters:
            for cluster in clusters:
                final_value = next(iter(sorted(p[0] for p in cluster)))
                seen = set()
                for value, label_id in cluster:
                    if value != final_value and not value in seen:
                        yield [qn, slugify(value), final_value.title()]
                        seen.add(value)



def process_value_labels(v):
    """Process the value label lines from the codebook"""

    for var in tqdm(v, desc="proc value labels"):
        lines = join_label_lines(var['label_lines'])
        lines = markup_label_lines(lines)
        entries = split_lines(lines)

        d, is_range, is_categorical = analyze_entries(var['question_name'], list(entries))

        yield [var['question_name'], var['base_qn'], is_range, is_categorical, d]


def generate_remap_rows(procd_val_labels):
    """Yield rows that map value labels to names that are more common across questions"""
    from collections import defaultdict
    from .labels import cluster_words

    qn_labels = defaultdict(list)

    # Group label sets by base question name
    for qn, bqn, _, _, d in procd_val_labels:
        qn_labels[bqn].append((d, qn))

    for bqn, label_sets in tqdm(qn_labels.items(), desc='find clusters'):  # For each question name.

        value_labels = defaultdict(set)

        for ls, qn in label_sets:  # Group labels by value
            for k, v in ls.items():
                value_labels[k].add((v, qn))

        # For each value, cluster all of the labels.
        for k, v in value_labels.items():
            clusters = cluster_words(v)
            for cn, cluster in enumerate(clusters):
                # For each cluster, find the shortest label,
                # then emit re-mappings for all of the other ones
                try:
                    shortest = min((e[0] for e in cluster if e[0].strip()), key=len).strip()
                except ValueError:
                    shortest = list(cluster)[0][0].strip()

                for label, qn in cluster:
                    if label != shortest and label and shortest:
                        yield (qn, k, cn, label, shortest)


def get_remap_dict(procd_val_labels):
    from collections import defaultdict
    rd = defaultdict(dict)

    for qn, k, cn, label, shortest in generate_remap_rows(procd_val_labels):
        rd[qn + ':' + str(k)][label] = shortest

    return rd


def write_remap_file(cdb_file):
    remap_file = Path(cdb_file).with_suffix('.remap.csv')

    with open(remap_file, 'w') as fo:
        w = csv.writer(fo)
        w.writerow('base_qn value cluster_no old_label new_label'.split())
        w.writerows(generate_remap_rows(cdb_file))


def join_label_lines(lines):
    """Join lines that don't start with a count to the previous line"""
    import re

    def _joined_lines(lines):

        continue_line = None
        for line in reversed(lines):

            line = re.sub('^\s\s\s\s', '', line)

            if not re.match('^\s*\d+', line):
                continue_line = line
                continue

            if 'or Advanced Biology' in line:
                # Line should be matched by clause above, but it isn't because it starts with a number
                print('!!!', line)
                continue_line = line
                continue

            if continue_line:
                line = line + ' ' + (continue_line.strip())
                continue_line = None

            yield line.strip()

    return reversed(list(_joined_lines(lines)))


def markup_label_lines(lines):
    """Add a pipe character between parts of the line"""
    import re

    def clean(lines):
        for line in lines:
            line = re.sub('Other\s*-\s*Recoded to', '', line, flags=re.IGNORECASE)
            line = re.sub('Other\s*-\s*Recoed to', '', line, flags=re.IGNORECASE)
            line = re.sub('Added in -', '', line, flags=re.IGNORECASE)
            line = re.sub('0 FI:', '0: FI', line)
            line = re.sub(r'\(\s*Go To [^\)]+\s*\)', '', line).strip().replace('\t', '|')
            line = re.sub('\d+\.', '', line)

            yield line

    def mark_splits(lines):

        # Using the replace with | technique because
        # its easy to debug
        for line in lines:

            # Remove the count number
            line = re.sub('^(\d+)\s+', '', line)

            if re.search('\d+\s+([^:]{15,}):', line):
                line = re.sub('(\d+)\s+(.*)',r'\1: \2', line)
                mark = True

            line = line.replace(':', '|', 1)

            # Lines with match position of colons, like:
            #


            if not '|' in line:
                if re.match('^\d+ TO \d+$', line.strip()):
                    line = line + '|'  # Its a range
                else:
                    # It just just missing the ':'
                    line = re.sub('(\d+)\s*', r'\1|', line, count=1)


            yield line

    return mark_splits(clean(lines))


def split_lines(lines):
    """Break a line into parts and yield tuples"""
    import re

    for line in lines:
        try:
            k, v = line.split('|')
            k = k.strip()
            v = v.strip()
        except ValueError:
            # Some entries have a key and no value
            k = (line.split('|')[0]).strip()
            v = None

        k = k.replace(' TO ', '-')

        if v:
            v = v.replace('{}.'.format(k), '').strip()

            # There are still a few labels that have numbers at the start
            # Buy only remove 3 or fewer, because a year at the start is valid, such as
            # int YCOC-003C
            v = re.sub('^(\d+)\s+', '', v).strip()
            v = v.capitalize()

        yield (k, v)


def analyze_entries(qn, entries):
    """  Do some analysis

    Mostly breaking up labels that are ranges ( "10 - 100" ) and correcting errors in identifying categoricals

    :param qn:
    :param entries:
    :return:

    """

    def is_nothing(e):

        if e is None or str(e).strip() == '':
            return True
        else:
            return False

    is_range = any('-' in k for k, v in entries)

    not_categorical = all(is_nothing(v) for k, v in entries) or \
                      is_range or \
                      'WEIGHT' in qn or \
                      '_ID_' in qn or \
                      all(str(k) == str(v) for k, v in entries) or \
                      'january' in [v.lower() for k, v in entries if v]

    is_categorical = not not_categorical

    if len(entries) <= 2:
        # Ignore binary values, https://github.com/Metatab/publicdata/issues/9
        is_categorical == False
        entries = []

    if is_categorical:
        # Fix missing entries if it is categorical
        entries = [(k, v if v else k) for k, v in entries]

    return dict(entries), int(is_range), int(is_categorical)

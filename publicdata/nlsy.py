# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

from appurl import WebUrl
from rowgenerators import Source
from copy import copy


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


def extract_from_codebook(f):
    """
    Parse the codebook for the NYLS79 full dataset, downloadable from
    https://www.nlsinfo.org/accessing-data-cohorts


    :param f:
    :return:
    """

    import re

    vars = []
    var = None
    var_line = 0
    var_no = 0
    in_val_labels = False

    for line_no, l in enumerate(f.readlines()):
        if 'Survey Year' in l and 'COMMENT' not in l:
            var_line = 0
            var_no += 1
            p = l.split()
            var = {
                'var_no': var_no,
                # 'labels': [],
                'variable_name': p[0],
                'variable_name_nd': p[0].replace('.', ''),
                'question_name': p[1].replace('[', '').replace(']', ''),
                'survey_year': p[4]
            }

        if var_line == 4:
            var['question'] = l.strip()

        if var_line == 5:
            in_val_labels = True

        if re.match(r'\-{5,20}', l.strip()) and in_val_labels:  # '-----', the summation line for value counts
            # Marks end of value labels
            in_val_labels = False

        if '---------------------------------' in l:
            # Marks end of question
            if var:
                vars.append(var)

            v = None

        if in_val_labels and False:  # Not quite working
            if l.strip() and 'COMMENT' not in l:
                try:
                    count, val_label = re.split(r'\s{2,}', l.strip())
                except:
                    print('Line: ', l)
                    raise
                if ':' in val_label:
                    val, label = val_label.split(':')
                else:
                    val, label = val_label, val_label

                var['labels'].append((val.strip(), label.strip(), int(count.strip())))

        var_line += 1

        # if line_no > 50000 or var_no > 100:
        #    var = None
        #    break

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


import unittest


class TestNlsy97(unittest.TestCase):
    def test_basic(self):
        import metapack as mp
        import pandas as pd

        pd.set_option('display.width', 120)
        pd.set_option('display.max_columns', 12)

        p = mp.open_package(
            '/Volumes/Storage/proj/virt/data-projects/workshift.us/packages/nlsinfo.org-nlsy-shiftwork/metadata.csv')

        nlsy = NLSY97(p.reference('shiftwork_97'))

        print(nlsy.var_labels)

        print(nlsy.question_frame('YEMP_81300').head())



from rowgenerators.test import RowGeneratorTest
from rowgenerators import parse_app_url

class NlsyTest(RowGeneratorTest):

    def test_create(self):

        from publicdata.nlsy import NLSY97

        u = parse_app_url('nlsy+file:../nlsy97_all_1997-2013.h5')

        nlsy = u.nlsy

        print(nlsy)



    def test_labels(self):
        from os.path import join
        from publicdata.nlsy.cdb import extract_from_codebook
        from publicdata.nlsy.labels import process_value_labels

        d = '/Users/eric/proj/virt-proj/data-project/sdrdl-data-projects/nlsinfo.org/nlsy97_all_1997-2013'

        cdb_file = join(d, 'nlsy97_all_1997-2013.cdb')

        codeb = extract_from_codebook(cdb_file)

        l = list(process_value_labels(codeb))


import unittest
if __name__ == '__main__':
    unittest.main()


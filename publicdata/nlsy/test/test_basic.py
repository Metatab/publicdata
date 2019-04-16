

from rowgenerators.test import RowGeneratorTest
from rowgenerators import parse_app_url

class NlsyTest(RowGeneratorTest):

    def test_create(self):

        from publicdata.nlsy import NLSY97

        u = parse_app_url('nlsy+file:../nlsy97_all_1997-2013.h5')

        nlsy = u.nlsy

        print(nlsy)



    def test_labels(self):
        from os.path import join, dirname
        from publicdata.nlsy.cdb import extract_from_codebook
        from publicdata.nlsy.labels import process_value_labels

        cdb_file = join(dirname(__file__), 'test.cdb')

        codeb = extract_from_codebook(cdb_file, force=True)

        l = list(process_value_labels(codeb))

        import yaml

        print(yaml.dump(l, default_flow_style=False))

        print(l[0])


import unittest
if __name__ == '__main__':
    unittest.main()


import unittest
from publicdata.census.util import sub_geoids

class TestUtil(unittest.TestCase):

    def test_sub_geoid(self):

        self.assertEqual(sub_geoids('ca'), '04000US06')
        self.assertEqual(sub_geoids('US'), '01000US')
        self.assertEqual(sub_geoids('x'), 'x')


if __name__ == '__main__':
    unittest.main()

import unittest


class TestCase(unittest.TestCase):

    def setUp(self):

        import warnings # Must turn off warnings in the test function
        warnings.simplefilter("ignore")

        super().setUp()

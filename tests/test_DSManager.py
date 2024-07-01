from unittest import TestCase
from datasets.DSManager import DSM
import pathlib


class TestDSM(TestCase):
    def setUp(self) -> None:
        self.dsm = DSM()
        self.assertIsNotNone(self.dsm)

        # Check cache file
        path = pathlib.Path('/tmp/dsm_cache.pkl')
        is_file = path.is_file()
        self.assertTrue(is_file)

    def test_populate_cache(self):
        self.assertGreater(self.dsm.populate_time, 0, msg='Time should elapse while creating/loading dataset')
        self.assertGreaterEqual(len(self.dsm.cache), 2, msg='There should be at lease 2 datasets in the cache')

    def test_get_current_active_dataset(self):
        with(self.assertRaises(KeyError)):
            self.dsm.get_current()

        self.dsm.active_dataset = '1m_utf'
        ds = self.dsm.get_current()
        self.assertIsNotNone(ds, msg='Should get a cache after setting the active dataset')

    def test_get_cache(self):
        utf_cache = self.dsm.get_cache('1m_utf')
        named_cache = self.dsm.get_cache('1m_named')
        self.assertEqual(1000000, len(utf_cache))
        self.assertEqual(1000000, len(named_cache))


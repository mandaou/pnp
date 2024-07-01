import unittest
from unittest import TestCase
from Algo_ECHT import ECHTBE
from datasets.DSManager import DSM
from ndn import encoding as enc
unittest.TestLoader.sortTestMethodsUsing = None


class TestECHTBE(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.dsm = DSM()
        cls.dsm.active_dataset = '1m_named'
        cls.algo = ECHTBE()

        # Get the corresponding dataset and load it
        cls.ds = cls.dsm.get_current()
        print('Loading 1 million entries, this will take around a minute to complete.')
        cls.algo.load(cls.ds)

    def test_be(self):
        be = self.algo.get_be()
        self.assertEqual('ECHT', be.name)
        self.assertEqual('named', be.value.name)
        self.assertEqual(2, be.value.value)

    def test_loaded_dataset(self):
        self.assertEqual(1000000, self.algo.processed_nodes)
        self.assertGreater(self.algo.total_components, 0)

    def test_get(self):
        query_key = self.dsm.get_cache(self.dsm.active_dataset).choice(1)
        expected = self.dsm.get_cache(self.dsm.active_dataset).find(query_key)
        actual = self.algo.get(query_key)
        self.assertListEqual(expected, actual)

    def test_bcm_identical(self):
        # Positive BCM - Identical
        query_key = self.dsm.get_cache(self.dsm.active_dataset).choice(1)
        expected = self.dsm.get_cache(self.dsm.active_dataset).find(query_key)
        actual_k, actual_v = self.algo.bcm(query_key)
        self.assertListEqual(expected, actual_v)
        self.assertListEqual(query_key, actual_k)

    def test_bcm_suf_component(self):
        # Positive BCM - Extra Component as a suffix
        query_key = self.dsm.get_cache(self.dsm.active_dataset).choice(1)
        expected = self.dsm.get_cache(self.dsm.active_dataset).find(query_key)
        new_key = enc.Name.from_str(enc.Name.to_str(query_key) + '/xyxyxyx')
        actual_k, actual_v = self.algo.bcm(new_key)
        self.assertListEqual(expected, actual_v)
        self.assertListEqual(query_key, actual_k)

    def test_bcm_pre_component(self):
        # Positive BCM - Extra Component as a prefix
        query_key = self.dsm.get_cache(self.dsm.active_dataset).choice(1)
        expected = self.dsm.get_cache(self.dsm.active_dataset).find(query_key)
        new_key = enc.Name.from_str('/xyxyxyx' + enc.Name.to_str(query_key))
        actual_k, actual_v = self.algo.bcm(new_key)
        self.assertIsNone(actual_v)

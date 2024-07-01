from unittest import TestCase

import Selector


class TestNamedBased(TestCase):
    def test_type_compliance(self):
        for a in Selector.Algorithms:
            self.assertIn(a.value.name, {'utf', 'named'})
            self.assertIn(a.value.value, {1, 2})

    def test_type_assignment(self):
        x = Selector.Algorithms.ECHT
        self.assertIsInstance(Selector.Algorithms.ECHT, type(x))
        self.assertEqual(x.value.name, 'named')
        self.assertEqual(x.value.value, 2)


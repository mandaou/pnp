import os
import pathlib
from unittest import TestCase

import Selector
import time
from profiler import Profiler


class TestProfiler(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiler = Profiler(Selector.Algorithms.UTFTest, 1, 'unittest')

    def test_start_and_stop(self):
        self.profiler.start()
        time.sleep(2)
        self.profiler.stop()
        time.sleep(1)
        activity_filename = pathlib.Path(self.profiler.activity_filename)
        plot_filename = pathlib.Path(self.profiler.plot_filename)
        self.assertTrue(activity_filename.exists())
        self.assertTrue(plot_filename.exists())
        os.remove(activity_filename)
        os.remove(plot_filename)

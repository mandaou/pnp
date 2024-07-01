import logging
import math
import pickle
import time
from abc import ABC, abstractmethod

import performance.PerformanceManager as perf
import Selector
from datasets.DSManager import Dataset

logging.basicConfig(format='{asctime} {levelname} [{filename}:{lineno}] {message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG,
                    style='{')


class BEABC(ABC):
    """
    Abstract Class for the application backend
    """

    # region ABC methods
    @abstractmethod
    def add(self, entry_key, entry_value):
        """
        Adds key/value to the algorithm backend. This is an abstract method, the implementation should be handled in the
        algorithm's code.

        Parameters
        ----------
        entry_key
        entry_value
        """
        pass

    @abstractmethod
    def manual_add(self, entry_key, entry_value):
        """
        Adds key/value to the algorithm backend. This is an abstract method, the implementation should be handled in the
        algorithm's code.

        Parameters
        ----------
        entry_key : list[bytearray]
            in NDN-format
        entry_value : list[list[bytearray]]
            in NDN-format
        """
        pass

    def load(self, entries: dict) -> None:
        """
        Loads entries into the corresponding backend/algorithm data structure. Load performance is measured in this
        routine.
        :param entries: a dictionary containing pickled keys/values. The pickled data are originally in UTF if the
        algorithm is text-based or NDN-encoded if the algorithm is named-based. This method should recursively call
        add(unpickled k, unpickled v)
        """
        time_of_first_entry = time.time()
        for k, v in entries.items():
            self.add(pickle.loads(k), pickle.loads(v))
        time_of_last_entry = time.time()
        self.load_performance.add(len(entries), time_of_first_entry, time_of_last_entry)

    def batch_load(self, dataset: Dataset, batch_size):
        """
        Loads the data progressively.
        :param dataset: The data to load
        :param batch_size: The number of lines to load in each iteration.
        :return:
        """
        number_of_batches = math.ceil(len(dataset) / batch_size)
        index = 0
        temp_dict = {}
        for (k, v) in dataset.items():
            index += 1
            temp_dict[k] = v
            if index % batch_size == 0:
                self.load(temp_dict)
                temp_dict = {}
        if len(temp_dict) != 0:
            self.load(temp_dict)
            temp_dict = {}

    @abstractmethod
    def get(self, entry_key):
        """
        Find the values for a corresponding key.
        :param entry_key: a list of bytearray, i.e. "NDN-encoded name" to look for
        :return: key-values in list format, or empty list if key does not exist, or None if key exists with no value
        """
        pass

    @abstractmethod
    def lpm(self, entry_key):
        """
        Search the internal dictionary for the longest prefix match for an entry key. The search direction is left to
        right.
        :param entry_key: word to lookup in NDN-Name encoded format
        :return: k, v
        """
        pass

    @abstractmethod
    def set(self, entry_key, entry_value):
        pass

    @abstractmethod
    def remove(self, entry_key, entry_values='all'):
        """
        Removes a value from the corresponding values of a given key
        :param entry_key:
        :param entry_values:
        :return: TODO: a list of remaining values ? or a list of deleted values ? if key error, return none or empty ?
        """
        pass

    @abstractmethod
    def is_entry(self, entry_key):
        pass

    @abstractmethod
    def dump(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def size(self):
        pass

    # endregion ABC methods

    # region class methods
    def get_be(self):
        return self.be

    def print_load_performance(self):
        self.load_performance.stats()
    # endregion class methods

    # region main
    def __init__(self, algorithm: Selector.Algorithms):
        self.be = algorithm
        self.be_name = algorithm.name
        self.default_dataset_format = algorithm.value.name
        self.description = ''
        self.load_performance = perf.LoadLogs(algorithm)
        self.perf_get_positive = perf.ResolvingLogs(algorithm, 'GET Positive', 'get_positive')
        self.perf_get_negative = perf.ResolvingLogs(algorithm, 'GET Negative', 'get_negative')
        self.perf_lpm_positive = perf.ResolvingLogs(algorithm, 'LPM Positive', 'lpm_positive')
        self.perf_lpm_negative = perf.ResolvingLogs(algorithm, 'GET Negative', 'lpm_negative')
    # endregion main

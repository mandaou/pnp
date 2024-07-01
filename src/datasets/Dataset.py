import csv
import logging
import pickle
import random
import tarfile
import time
from ndn import encoding as enc

from utils import insert_component_prefix, insert_component_suffix, insert_component_suffix_component

# region logging
logging.basicConfig(format='{asctime} {levelname} [{filename}:{lineno}] {message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

logging.getLogger('asyncio').setLevel(logging.WARNING)
# endregion logging


class Dataset:
    """
    A class used to represent a dataset. A dataset is a two column dictionary where the key is the publisher's name and
    the value is the corresponding autonomous numbers, i.e. k:'/om/edu/squ', v:'/AS1,/AS2,/AS9'.

    Attributes
    ----------
    name : str
        A fixed string from one of the following options: 'few', '1k', '10k', '100k', '1m'.

    ndn_encoded : bool
        How to store the data, if False, the data is stored as is in text/utf format. If True, the data is encoded using
        NDN Name Encode From String.

    path : str
        The path to a dataset file on disk.

    Methods
    -------
    get()
        Returns the dataset in dictionary format
    """

    def __init__(self, name: str, ndn_encoded: bool, dataset_path_on_disk: str):
        self.content = dict()
        self.name = name + '_named' if ndn_encoded else name + '_text'
        self.ndn_encoded = ndn_encoded
        self.path = dataset_path_on_disk
        self.gz = True if str(self.path).endswith('gz') else False
        self.open_mode = 'r:gz' if self.gz else 'r'
        self.read_from_disk()

    def __len__(self):
        return len(self.content)

    def items(self):
        for k, v in self.content.items():
            yield k, v

    def get(self):
        """ Returns a generator for unpickled/decoded key-value pairs"""
        for k, v in self.content.items():
            k = pickle.loads(k)
            v = pickle.loads(v)
            if self.ndn_encoded:
                k_decoded = enc.Name.to_str(k)
                v_decoded = []
                for i in v:
                    v_decoded.append(enc.Name.to_str(i))
                yield k_decoded, v_decoded
            else:
                yield k, v

    def to_dict(self):
        """Returns the dataset in dictionary format"""
        return self.content

    def read_from_disk(self):
        """Force reading the dataset file from disk. This method is able to read either a csv or a csv compressed with
        tar.gz """
        # Reading from a compressed file
        if self.gz:
            dicts = []
            with tarfile.open(name=self.path, mode=self.open_mode) as tar:
                members = tar.getmembers()
                for m in members:
                    if m.name.endswith('.csv'):
                        temp_dict = {}
                        f = tar.extractfile(m)
                        content = f.read()
                        lines = csv.reader(str(content, 'utf-8').splitlines())
                        for line in lines:
                            k = str(line[0]).lower()
                            v = line[1:]
                            logging.debug('[READ] {} -> {}'.format(k, v))
                            if self.ndn_encoded:
                                # Encode
                                k_encoded = enc.Name.from_str(k)
                                v_encoded = list()
                                for i in v:
                                    v_encoded.append(enc.Name.from_str(i))
                                logging.debug('[ENCODE] {} -> {}'.format(k_encoded, v_encoded))

                                # Pickle
                                k_pickled = pickle.dumps(k_encoded)
                                v_pickled = pickle.dumps(v_encoded)
                                logging.debug('[PICKLE] {} -> {}'.format(k_pickled, v_pickled))
                                temp_dict[k_pickled] = v_pickled
                            else:
                                k_pickled = pickle.dumps(k)
                                v_pickled = pickle.dumps(v)
                                logging.debug('[PICKLE] {} -> {}'.format(k_pickled, v_pickled))
                                temp_dict[k_pickled] = v_pickled
                        dicts.append(temp_dict)
            self.content = dicts[0]

        # Reading a normal csv file
        else:
            entries_dict = {}
            with open(file=self.path, mode=self.open_mode) as fh:
                # reading the CSV file
                lines = csv.reader(fh)
                # displaying the contents of the CSV file
                for line in lines:
                    k = str(line[0]).lower()
                    v = line[1:]
                    logging.debug('[READ] {} -> {}'.format(k, v))
                    if self.ndn_encoded:
                        # Encode
                        k_encoded = enc.Name.from_str(k)
                        v_encoded = list()
                        for i in v:
                            v_encoded.append(enc.Name.from_str(i))
                        logging.debug('[ENCODE] {} -> {}'.format(k_encoded, v_encoded))

                        # Pickle
                        k_pickled = pickle.dumps(k_encoded)
                        v_pickled = pickle.dumps(v_encoded)
                        logging.debug('[PICKLE] {} -> {}'.format(k_pickled, v_pickled))
                        entries_dict[k_pickled] = v_pickled
                    else:
                        # Pickle
                        k_pickled = pickle.dumps(k)
                        v_pickled = pickle.dumps(v)
                        logging.debug('[PICKLE] {} -> {}'.format(k_pickled, v_pickled))
                        entries_dict[k_pickled] = v_pickled

            self.content = entries_dict

    def unpickle(self):
        """Returns unpi"""
        for k, v in self.content.items():
            yield pickle.loads(k), pickle.loads(v)

    def decode(self):
        for k, v in self.unpickle():
            if self.ndn_encoded:
                k_decoded = enc.Name.to_str(k)
                v_decoded = list()
                for i in v:
                    v_decoded.append(enc.Name.to_str(i))
                yield k_decoded, v_decoded
            else:
                yield k, v

    def build_ds(self):
        dicto = dict()
        for k, v in self.decode():
            dicto[k] = v
        return dicto

    def get_keys(self, count=None, unpickle=True, decode=False):
        if not self.ndn_encoded and decode:
            decode = False
        keys = list(self.content.keys())
        if count is None:
            for k in keys:
                if decode:
                    yield enc.Name.to_str(pickle.loads(k))
                else:
                    if unpickle:
                        yield pickle.loads(k)
                    else:
                        yield k
        else:
            for i in range(count):
                k = random.choice(keys)
                keys.remove(k)
                if decode:
                    yield enc.Name.to_str(pickle.loads(k))
                else:
                    if unpickle:
                        yield pickle.loads(k)
                    else:
                        yield k

    def choice(self, count=1, scope='from_dataset', encoded=False):
        """
        Returns an X-amount of random elements from the dataset.
        Elements will be unpickled before sending them back to the caller. Hence, returned elements will be either in
        utf or NDN-named based on the dataset this function is called from
        """
        results = []
        if scope == 'from_dataset':
            for i in range(count):
                key = random.choice(list(self.content.keys()))
                key_unpickled = pickle.loads(key)
                results.append(key_unpickled)
                # yield key_unpickled
        elif scope == 'outside_dataset':
            unpickled_keys = self.choice(count, 'from_dataset')
            results = list()
            for key in unpickled_keys:
                # Decode key if it is NDN-encoded
                if self.ndn_encoded:
                    key = enc.Name.to_str(key)

                # Create key modifications from a key in utf format
                modifications = [insert_component_prefix(key),
                                 insert_component_suffix(key),
                                 insert_component_suffix_component(key)]
                for new_name in modifications:
                    for i in new_name:
                        results.append(enc.Name.from_str(i) if self.ndn_encoded else i)
                        # yield enc.Name.from_str(i) if self.ndn_encoded else i

        if encoded:
            encoded_results = []
            for i in results:
                encoded_results.append(enc.Name.from_str(i))
            return encoded_results[0] if count == 1 else encoded_results
        return results[0] if count == 1 else results

    def find(self, entry_key):
        pickled_key = pickle.dumps(entry_key)
        return pickle.loads(self.content[pickled_key])

    def subset(self, size):
        start_time = time.time()
        items = list(self.content.items())
        subset = dict()
        while len(subset) < size:
            key, value = random.choice(items)
            subset[key] = value
        end_time = time.time()
        duration = end_time - start_time
        logging.info('Generated a size {} subset of the dataset {} in {} s'.format(size, self.name, duration))
        return subset

    def generate_add_subnet(self, size, domain_prefix_to_add) -> (list, list):
        """
        Generate a subset based on the required size then add the given prefix to each publisher

        Parameters
        ----------
        size : int
            The size of the subset to generate
        domain_prefix_to_add : str
            The prefix to add to each publish


        Returns
        -------
        tuple(list, list)
            (Keys,Values)
        """
        # Get subset
        if size >= len(self.content):
            ss = self.content
        else:
            ss = self.subset(size)

        # Unpickle the subset and add the prefix, also, shuffle the values before storing them
        start_time = time.time()

        if self.ndn_encoded:
            # if dataset is named based
            ks = []
            vs = []
            for k, v in ss.items():
                nk = pickle.loads(k)
                nv = pickle.loads(v)
                nk.insert(0, enc.Name.from_str(domain_prefix_to_add)[0])
                random.shuffle(nv)
                ks.append(nk)
                vs.append(nv)
            end_time = time.time()
            duration = end_time - start_time
            logging.info('The {} items subset was unpickled/prefixed/shuffled/scissored in {} s'.format(size, duration))
            return ks, vs
        else:
            # if dataset is utf based
            uss = dict()
            for k, v in ss.items():
                nv = pickle.loads(v)
                random.shuffle(nv)
                uss[domain_prefix_to_add + pickle.loads(k)] = nv
            end_time = time.time()
            duration = end_time - start_time
            logging.info('The {} items subset was unpickled/prefixed/shuffled in {} s'.format(size, duration))

            # Split the previous subset into two lists: keys and values and then return them
            ks = []
            vs = []
            start_time = time.time()
            for k, v in uss.items():
                ks.append(enc.Name.from_str(k))
                temp = []
                for i in v:
                    temp.append(enc.Name.from_str(i))
                vs.append(temp)
            end_time = time.time()
            duration = end_time - start_time
            logging.info('The {} items subset was scissored in {} s'.format(size, duration))
            return ks, vs

